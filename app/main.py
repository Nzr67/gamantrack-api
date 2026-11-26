from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.routers import stops, routes, fares, schedules, admin, auth

app = FastAPI(title="GamanTrack API", version="1.0.0")

origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stops.router)
app.include_router(routes.router)
app.include_router(fares.router)
app.include_router(schedules.router)
app.include_router(admin.router)
app.include_router(auth.router)


@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT COUNT(*) FROM routes"))
    routes_count = result.scalar_one()
    return {
        "status": "ok",
        "database": "connected",
        "routes_seeded": routes_count,
    }