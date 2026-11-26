from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import AdminUser


SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get admin user from database
    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return user


async def ensure_single_admin(db: AsyncSession) -> AdminUser:
    """Ensure exactly one admin user exists. Creates default if none exist."""
    result = await db.execute(select(AdminUser).where(AdminUser.role == "ADMIN"))
    admins = result.scalars().all()
    
    if len(admins) == 0:
        # Create default admin user
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        default_admin = AdminUser(
            username="admin",
            password_hash=pwd_context.hash("admin123"),
            role="ADMIN",
        )
        db.add(default_admin)
        await db.commit()
        await db.refresh(default_admin)
        return default_admin
    
    if len(admins) > 1:
        # This should not happen in production, but we enforce single admin
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multiple admin users detected. Only one admin is allowed.",
        )
    
    return admins[0]


async def verify_single_admin_constraint(db: AsyncSession, username: str, role: str) -> None:
    """Verify that creating/updating a user doesn't violate single-admin constraint."""
    if role == "ADMIN":
        result = await db.execute(select(AdminUser).where(AdminUser.role == "ADMIN"))
        existing_admin = result.scalar_one_or_none()
        if existing_admin and existing_admin.username != username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only one admin user is allowed. An admin already exists.",
            )