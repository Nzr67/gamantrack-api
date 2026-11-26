from fastapi import FastAPI
from app.routers import stops, routes, fares, schedules, admin

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