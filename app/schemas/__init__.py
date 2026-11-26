from typing import Generic, TypeVar, Optional, List, Literal
from decimal import Decimal
from datetime import time
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RouteResponse(BaseModel):
    id: int
    route_number: str
    start_name: str
    end_name: str

    model_config = ConfigDict(from_attributes=True)


class StopResponse(BaseModel):
    id: int
    stop_name: str
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)


class NearbyStopResponse(StopResponse):
    distance_km: float


class RouteStopResponse(BaseModel):
    route_id: int
    stop_id: int
    stop_sequence: int
    fare_stage: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class FareMatrixResponse(BaseModel):
    stage_difference: int
    normal_fare: Decimal
    semi_luxury_fare: Decimal
    ac_fare: Decimal

    model_config = ConfigDict(from_attributes=True)


class TimetableResponse(BaseModel):
    id: int
    route_id: int
    departure_time: time
    day_type: str
    direction: str

    model_config = ConfigDict(from_attributes=True)


class AdminUserResponse(BaseModel):
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: int
    admin_id: Optional[int] = None
    admin_username: Optional[str] = None
    action_summary: Optional[str] = None
    percentage_change: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool


class FareCalculationRequest(BaseModel):
    origin_stop_id: int
    destination_stop_id: int
    service_type: Literal["normal", "semi_luxury", "ac"] = "normal"


class FareCalculationResponse(BaseModel):
    origin_stop: StopResponse
    destination_stop: StopResponse
    stage_difference: int
    fare: Decimal


class NearbyStopsRequest(BaseModel):
    lat: float
    lng: float
    radius_km: float = 1.0


class RouteSearchRequest(BaseModel):
    origin_stop_id: Optional[int] = None
    destination_stop_id: Optional[int] = None
    route_number: Optional[str] = None


class ScheduleSearchRequest(BaseModel):
    route_id: Optional[int] = None
    day_type: Optional[str] = None
    direction: Optional[str] = None


# =============================================================================
# New schemas for Supabase-aligned endpoints
# =============================================================================

class PublicRouteStopResponse(BaseModel):
    """Response model for public.route_stops."""
    stage_number: int
    stop_name: str
    stop_order: int

    model_config = ConfigDict(from_attributes=True)


class PublicRouteDetailResponse(BaseModel):
    """Response model for route details from public.routes."""
    id: int
    route_number: str
    start_name: str
    end_name: str
    service_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PublicTimetableResponse(BaseModel):
    """Response model for public.timetables."""
    id: int
    departure_time: time
    arrival_estimate: Optional[time] = None
    day_type: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RouteStopsResponse(BaseModel):
    """Response for GET /routes/{route_number}/stops."""
    route: PublicRouteDetailResponse
    stops: List[PublicRouteStopResponse]


class RouteTimetableResponse(BaseModel):
    """Response for GET /routes/{route_number}/timetable."""
    route: PublicRouteDetailResponse
    departures: List[PublicTimetableResponse]


class FareCalculateRequest(BaseModel):
    """Request model for fare calculation by stages."""
    route_number: str
    from_stage: int = Field(ge=0)
    to_stage: int = Field(ge=0)


class FareCalculateResponse(BaseModel):
    """Response model for fare calculation by stages."""
    route_number: str
    start_name: str
    end_name: str
    from_stage: int
    to_stage: int
    stage_difference: int
    fare: float
    currency: str = "LKR"