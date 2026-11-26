from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.database import get_db
from app.models import AdminUser
from app.schemas import LoginRequest, Token
from app.auth import create_access_token, ensure_single_admin


router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Admin login - verifies credentials and returns JWT token."""
    # Ensure single admin exists
    await ensure_single_admin(db)
    
    # Get admin user
    from sqlalchemy import select
    result = await db.execute(select(AdminUser).where(AdminUser.username == credentials.username))
    user = result.scalar_one_or_none()
    
    if not user or not pwd_context.verify(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        role=user.role,
    )


@router.post("/setup-admin", response_model=Token)
async def setup_admin(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Initial admin setup - only works if no admin exists yet."""
    from sqlalchemy import select
    
    # Check if any admin exists
    result = await db.execute(select(AdminUser).where(AdminUser.role == "ADMIN"))
    existing_admin = result.scalar_one_or_none()
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin already exists. Use /api/auth/login instead.",
        )
    
    # Create admin
    admin = AdminUser(
        username=credentials.username,
        password_hash=pwd_context.hash(credentials.password),
        role="ADMIN",
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    
    access_token = create_access_token(data={"sub": admin.username, "role": admin.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=admin.username,
        role=admin.role,
    )