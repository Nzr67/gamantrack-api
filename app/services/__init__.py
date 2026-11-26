import math
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Route, Stop, RouteStop, NtcFareMatrix, Timetable, AdminUser, AuditLog,
    PublicRoute, PublicRouteStop, PublicFareStage, PublicTimetable
)
from app.schemas import (
    RouteResponse, StopResponse, NearbyStopResponse, RouteStopResponse,
    FareMatrixResponse, TimetableResponse, AdminUserResponse, AuditLogResponse,
)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class StopService:
    """Legacy service for existing tests - kept for backward compatibility."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_stops(self, search: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Stop]:
        q = select(Stop)
        if search:
            q = q.where(Stop.stop_name.ilike(f"%{search}%"))
        q = q.limit(limit).offset(offset)
        return list((await self.db.execute(q)).scalars().all())

    async def get_stop(self, stop_id: int) -> Optional[Stop]:
        return await self.db.get(Stop, stop_id)

    async def nearby(self, lat: float, lng: float, radius_km: float, limit: int = 20) -> List[Stop]:
        stops = list((await self.db.execute(select(Stop))).scalars().all())
        result = []
        for s in stops:
            d = haversine(lat, lng, s.latitude, s.longitude)
            if d <= radius_km:
                result.append((s, d))
        result.sort(key=lambda x: x[1])
        return [s for s, _ in result[:limit]]

    async def nearby_with_distance(self, lat: float, lng: float, radius_km: float, limit: int = 20):
        stops = list((await self.db.execute(select(Stop))).scalars().all())
        result = []
        for s in stops:
            d = haversine(lat, lng, s.latitude, s.longitude)
            if d <= radius_km:
                result.append((s, d))
        result.sort(key=lambda x: x[1])
        return result[:limit]


class RouteService:
    """Legacy service for existing tests - kept for backward compatibility."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_route(self, route_id: int) -> Optional[Route]:
        return await self.db.get(Route, route_id)

    async def list_routes(self, search: Optional[str] = None) -> List[Route]:
        q = select(Route)
        if search:
            q = q.where(Route.route_number.ilike(f"%{search}%"))
        return list((await self.db.execute(q)).scalars().all())

    async def search_routes(self, origin_stop_id: Optional[int] = None, destination_stop_id: Optional[int] = None, route_number: Optional[str] = None) -> List[Route]:
        q = select(Route)
        if route_number:
            q = q.where(Route.route_number == route_number)
        if origin_stop_id is not None:
            q = q.where(Route.id.in_(select(RouteStop.route_id).where(RouteStop.stop_id == origin_stop_id)))
        if destination_stop_id is not None:
            q = q.where(Route.id.in_(select(RouteStop.route_id).where(RouteStop.stop_id == destination_stop_id)))
        return list((await self.db.execute(q)).scalars().all())

    async def route_stops_ordered(self, route_id: int) -> List[RouteStop]:
        q = select(RouteStop).where(RouteStop.route_id == route_id).order_by(RouteStop.stop_sequence)
        return list((await self.db.execute(q)).scalars().all())

    async def get_route_stop(self, route_id: int, stop_id: int) -> Optional[RouteStop]:
        q = select(RouteStop).where(RouteStop.route_id == route_id, RouteStop.stop_id == stop_id)
        return (await self.db.execute(q)).scalar_one_or_none()


class FareService:
    """Legacy service for existing tests - kept for backward compatibility."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate(self, origin_stop_id: int, destination_stop_id: int, service_type: str = "normal"):
        # find route containing both stops
        origin_rs = (await self.db.execute(select(RouteStop).where(RouteStop.stop_id == origin_stop_id))).scalar_one_or_none()
        dest_rs = (await self.db.execute(select(RouteStop).where(RouteStop.stop_id == destination_stop_id))).scalar_one_or_none()
        if origin_rs is None or dest_rs is None:
            raise ValueError("Stop not on a known route")
        if origin_rs.route_id != dest_rs.route_id:
            raise ValueError("Stops not on same route")
        stage_diff = abs((origin_rs.fare_stage or origin_rs.stop_sequence) - (dest_rs.fare_stage or dest_rs.stop_sequence))
        if stage_diff == 0:
            stage_diff = 1
        fm = (await self.db.execute(select(NtcFareMatrix).where(NtcFareMatrix.stage_difference == stage_diff))).scalar_one_or_none()
        if fm is None:
            raise ValueError("Fare not found for stage difference")
        fare_col = {"normal": fm.normal_fare, "semi_luxury": fm.semi_luxury_fare, "ac": fm.ac_fare}[service_type]
        origin_stop = await self.db.get(Stop, origin_stop_id)
        dest_stop = await self.db.get(Stop, destination_stop_id)
        return {
            "origin_stop": origin_stop,
            "destination_stop": dest_stop,
            "stage_difference": stage_diff,
            "fare": fare_col,
        }


class ScheduleService:
    """Legacy service for existing tests - kept for backward compatibility."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_timetables(self, route_id: Optional[int] = None, day_type: Optional[str] = None, direction: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Timetable]:
        q = select(Timetable)
        if route_id is not None:
            q = q.where(Timetable.route_id == route_id)
        if day_type is not None:
            q = q.where(Timetable.day_type == day_type)
        if direction is not None:
            q = q.where(Timetable.direction == direction)
        q = q.limit(limit).offset(offset)
        return list((await self.db.execute(q)).scalars().all())


# =============================================================================
# New services for Supabase-aligned schema (public schema)
# =============================================================================

class PublicRouteService:
    """Service for public.routes table operations."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_route_by_number(self, route_number: str) -> Optional[PublicRoute]:
        """Get active route by route_number."""
        q = select(PublicRoute).where(
            PublicRoute.route_number == route_number,
            PublicRoute.is_active == True
        )
        return (await self.db.execute(q)).scalar_one_or_none()

    async def get_route_stops(self, route_id: int) -> List[PublicRouteStop]:
        """Get route stops ordered by stop_order."""
        q = select(PublicRouteStop).where(
            PublicRouteStop.route_id == route_id
        ).order_by(PublicRouteStop.stop_order)
        return list((await self.db.execute(q)).scalars().all())

    async def get_route_timetables(self, route_id: int) -> List[PublicTimetable]:
        """Get timetables ordered by departure_time."""
        q = select(PublicTimetable).where(
            PublicTimetable.route_id == route_id
        ).order_by(PublicTimetable.departure_time)
        return list((await self.db.execute(q)).scalars().all())


class PublicFareService:
    """Service for public.fare_stages table operations."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_fare_by_stage_diff(self, stage_diff: int) -> Optional[PublicFareStage]:
        """Get fare for a specific stage difference."""
        q = select(PublicFareStage).where(PublicFareStage.stage_diff == stage_diff)
        return (await self.db.execute(q)).scalar_one_or_none()


class AdminUserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[AdminUser]:
        return await self.db.get(AdminUser, user_id)

    async def get_by_username(self, username: str) -> Optional[AdminUser]:
        return (await self.db.execute(select(AdminUser).where(AdminUser.username == username))).scalar_one_or_none()


class AuditLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_logs(self, limit: int = 50, offset: int = 0) -> List[AuditLog]:
        q = select(AuditLog).limit(limit).offset(offset)
        return list((await self.db.execute(q)).scalars().all())