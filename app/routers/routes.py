from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    RouteResponse, RouteStopResponse, PaginatedResponse,
    RouteStopsResponse, RouteTimetableResponse,
    PublicRouteDetailResponse, PublicRouteStopResponse, PublicTimetableResponse
)
from app.services import RouteService, PublicRouteService

router = APIRouter(prefix="/api/routes", tags=["routes"])


# =============================================================================
# New Supabase-aligned endpoints (must come before legacy to avoid route conflicts)
# =============================================================================

@router.get("/{route_number}/stops", response_model=RouteStopsResponse)
async def get_route_stops_by_number(
    route_number: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get route details and ordered stops for a route by route_number.
    Queries public.routes and public.route_stops tables.
    """
    service = PublicRouteService(db)
    
    # Get route by route_number (must be active)
    route = await service.get_route_by_number(route_number)
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Get ordered stops
    stops = await service.get_route_stops(route.id)
    
    return RouteStopsResponse(
        route=PublicRouteDetailResponse.model_validate(route),
        stops=[PublicRouteStopResponse.model_validate(s) for s in stops]
    )


@router.get("/{route_number}/timetable", response_model=RouteTimetableResponse)
async def get_route_timetable_by_number(
    route_number: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get route details and timetable for a route by route_number.
    Queries public.routes and public.timetables tables.
    """
    service = PublicRouteService(db)
    
    # Get route by route_number (must be active)
    route = await service.get_route_by_number(route_number)
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Get timetables ordered by departure_time
    timetables = await service.get_route_timetables(route.id)
    
    return RouteTimetableResponse(
        route=PublicRouteDetailResponse.model_validate(route),
        departures=[PublicTimetableResponse.model_validate(t) for t in timetables]
    )


# =============================================================================
# Legacy endpoints (for backward compatibility with existing tests)
# =============================================================================

@router.get("/search", response_model=List[RouteResponse])
async def search_routes(
    origin_stop_id: Optional[int] = Query(None),
    destination_stop_id: Optional[int] = Query(None),
    route_number: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = RouteService(db)
    routes = await service.search_routes(origin_stop_id, destination_stop_id, route_number)
    return [RouteResponse.model_validate(r) for r in routes]


@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(route_id: int, db: AsyncSession = Depends(get_db)):
    service = RouteService(db)
    route = await service.get_route(route_id)
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    return RouteResponse.model_validate(route)


@router.get("/{route_id}/stops", response_model=List[RouteStopResponse])
async def get_route_stops(route_id: int, db: AsyncSession = Depends(get_db)):
    service = RouteService(db)
    stops = await service.route_stops_ordered(route_id)
    out = []
    for rs in stops:
        out.append(RouteStopResponse(route_id=rs.route_id, stop_id=rs.stop_id, stop_sequence=rs.stop_sequence, fare_stage=rs.fare_stage))
    return out


@router.get("/", response_model=List[RouteResponse])
async def list_routes(search: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    service = RouteService(db)
    routes = await service.list_routes(search)
    return [RouteResponse.model_validate(r) for r in routes]