from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    FareCalculationRequest, FareCalculationResponse, StopResponse,
    FareCalculateRequest, FareCalculateResponse
)
from app.services import FareService, StopService, PublicRouteService, PublicFareService

router = APIRouter(prefix="/api/fare", tags=["fare"])


# =============================================================================
# Legacy endpoints (for backward compatibility with existing tests)
# =============================================================================

@router.get("/", response_model=FareCalculationResponse)
async def calculate_fare(
    origin_stop_id: int = Query(...),
    destination_stop_id: int = Query(...),
    service_type: str = Query("normal"),
    db: AsyncSession = Depends(get_db),
):
    service = FareService(db)
    stop_service = StopService(db)
    try:
        result = await service.calculate(origin_stop_id, destination_stop_id, service_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    origin = await stop_service.get_stop(origin_stop_id)
    dest = await stop_service.get_stop(destination_stop_id)
    return FareCalculationResponse(
        origin_stop=StopResponse.from_orm(origin),
        destination_stop=StopResponse.from_orm(dest),
        stage_difference=result["stage_difference"],
        fare=result["fare"],
    )


@router.post("/", response_model=FareCalculationResponse)
async def calculate_fare_post(req: FareCalculationRequest, db: AsyncSession = Depends(get_db)):
    service = FareService(db)
    stop_service = StopService(db)
    try:
        result = await service.calculate(req.origin_stop_id, req.destination_stop_id, req.service_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    origin = await stop_service.get_stop(req.origin_stop_id)
    dest = await stop_service.get_stop(req.destination_stop_id)
    return FareCalculationResponse(
        origin_stop=StopResponse.from_orm(origin),
        destination_stop=StopResponse.from_orm(dest),
        stage_difference=result["stage_difference"],
        fare=result["fare"],
    )


# =============================================================================
# New Supabase-aligned endpoints
# =============================================================================

@router.get("/calculate", response_model=FareCalculateResponse)
async def calculate_fare_by_stages(
    route_number: str = Query(...),
    from_stage: int = Query(..., ge=0),
    to_stage: int = Query(..., ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate fare based on stage difference for a route.
    Queries public.routes for route details and public.fare_stages for fare.
    """
    route_service = PublicRouteService(db)
    fare_service = PublicFareService(db)
    
    # Verify the active route exists
    route = await route_service.get_route_by_number(route_number)
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Compute stage difference
    stage_diff = abs(to_stage - from_stage)
    
    # If stage_diff is 0, return fare 0.0
    if stage_diff == 0:
        return FareCalculateResponse(
            route_number=route.route_number,
            start_name=route.start_name,
            end_name=route.end_name,
            from_stage=from_stage,
            to_stage=to_stage,
            stage_difference=0,
            fare=0.0,
            currency="LKR"
        )
    
    # Query fare_stages for the stage difference
    fare_stage = await fare_service.get_fare_by_stage_diff(stage_diff)
    if fare_stage is None:
        raise HTTPException(status_code=404, detail=f"No fare found for stage difference {stage_diff}")
    
    return FareCalculateResponse(
        route_number=route.route_number,
        start_name=route.start_name,
        end_name=route.end_name,
        from_stage=from_stage,
        to_stage=to_stage,
        stage_difference=stage_diff,
        fare=float(fare_stage.normal_fare),
        currency="LKR"
    )