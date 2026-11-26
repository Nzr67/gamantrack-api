from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import StopResponse, NearbyStopResponse, PaginatedResponse
from app.services import StopService

router = APIRouter(prefix="/api/stops", tags=["stops"])


@router.get("/", response_model=PaginatedResponse[StopResponse])
async def list_stops(
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = StopService(db)
    stops = await service.list_stops(search, limit, offset)
    return {"items": [StopResponse.model_validate(s) for s in stops], "total": len(stops), "limit": limit, "offset": offset, "has_more": len(stops) == limit}


@router.get("/nearby", response_model=List[NearbyStopResponse])
async def nearby_stops(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(1.0, ge=0.1, le=50),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = StopService(db)
    results = await service.nearby_with_distance(lat, lng, radius_km, limit)
    out = []
    for s, d in results:
        out.append(NearbyStopResponse(id=s.id, stop_name=s.stop_name, latitude=s.latitude, longitude=s.longitude, distance_km=round(d, 3)))
    return out


@router.get("/{stop_id}", response_model=StopResponse)
async def get_stop(stop_id: int, db: AsyncSession = Depends(get_db)):
    service = StopService(db)
    stop = await service.get_stop(stop_id)
    if stop is None:
        raise HTTPException(status_code=404, detail="Stop not found")
    return StopResponse.from_orm(stop)