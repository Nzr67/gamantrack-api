from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import AdminUserResponse, AuditLogResponse, FareMatrixResponse, TimetableResponse, PaginatedResponse
from app.services import AdminUserService, AuditLogService
from app.auth import get_current_admin


router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


@router.get("/me", response_model=AdminUserResponse)
async def admin_me(current_admin: AdminUserResponse = Depends(get_current_admin)):
    """Return current admin user."""
    return current_admin


@router.get("/fare-matrix", response_model=List[FareMatrixResponse])
async def list_fare_matrix(
    current_admin: AdminUserResponse = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return NTC fare matrix rows ordered by stage_difference."""
    from app.models import NtcFareMatrix

    q = select(NtcFareMatrix).order_by(NtcFareMatrix.stage_difference)
    rows = (await db.execute(q)).scalars().all()
    return [FareMatrixResponse.model_validate(r) for r in rows]


@router.post("/fare-matrix")
async def update_fare_matrix(
    stage_difference: int = Query(..., ge=1),
    normal_fare: float = Query(..., ge=0),
    semi_luxury_fare: float = Query(..., ge=0),
    ac_fare: float = Query(..., ge=0),
    current_admin: AdminUserResponse = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a fare matrix stage and record the change in audit_logs."""
    from app.models import NtcFareMatrix, AuditLog

    fm = (
        (
            await db.execute(
                select(NtcFareMatrix).where(NtcFareMatrix.stage_difference == stage_difference)
            )
        )
    ).scalar_one_or_none()
    if fm is None:
        raise HTTPException(status_code=404, detail="Fare stage not found")
    fm.normal_fare = normal_fare
    fm.semi_luxury_fare = semi_luxury_fare
    fm.ac_fare = ac_fare
    db.add(fm)
    log = AuditLog(
        admin_id=current_admin.id,
        admin_username=current_admin.username,
        action_summary=f"Updated fare matrix stage_difference={stage_difference}",
        percentage_change=0.0,
    )
    db.add(log)
    await db.commit()
    return {"status": "updated", "stage_difference": stage_difference, "normal_fare": normal_fare, "semi_luxury_fare": semi_luxury_fare, "ac_fare": ac_fare}


@router.get("/timetables", response_model=List[TimetableResponse])
async def list_timetables(
    current_admin: AdminUserResponse = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return all timetable entries."""
    from app.models import Timetable

    q = select(Timetable)
    rows = (await db.execute(q)).scalars().all()
    return [TimetableResponse.model_validate(r) for r in rows]


@router.post("/timetables")
async def add_timetable(
    route_id: int = Query(..., ge=1),
    departure_time: str = Query(...),
    day_type: str = Query(...),
    direction: str = Query(...),
    current_admin: AdminUserResponse = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a new timetable entry and audit the change."""
    from datetime import time

    from app.models import AuditLog, Timetable

    if day_type not in ("Weekday", "Saturday", "Sunday / Holiday") or direction not in ("Outbound", "Inbound"):
        raise HTTPException(status_code=422, detail="Invalid day_type or direction")
    tt = Timetable(
        route_id=route_id,
        departure_time=time.fromisoformat(departure_time),
        day_type=day_type,
        direction=direction,
    )
    db.add(tt)
    log = AuditLog(
        admin_id=current_admin.id,
        admin_username=current_admin.username,
        action_summary=f"Added timetable route_id={route_id} time={departure_time}",
        percentage_change=0.0,
    )
    db.add(log)
    await db.commit()
    return {"status": "added", "route_id": route_id, "departure_time": departure_time, "day_type": day_type, "direction": direction}


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: AdminUserResponse = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return recent audit log entries."""
    service = AuditLogService(db)
    items = await service.list_logs(limit, offset)
    return {
        "items": [AuditLogResponse.model_validate(r) for r in items],
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "has_more": len(items) == limit,
    }