from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import TimetableResponse, PaginatedResponse
from app.services import ScheduleService

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


@router.get("/", response_model=PaginatedResponse[TimetableResponse])
async def list_schedules(
    route_id: Optional[int] = Query(None),
    day_type: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = ScheduleService(db)
    items = await service.list_timetables(route_id, day_type, direction, limit, offset)
    return {"items": [TimetableResponse.model_validate(t) for t in items], "total": len(items), "limit": limit, "offset": offset, "has_more": len(items) == limit}