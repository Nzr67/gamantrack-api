from datetime import time, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey,
    Integer, SmallInteger, String, Text, Time, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import NUMERIC
from app.database import Base


class Route(Base):
    """Legacy model for existing tests - kept for backward compatibility."""
    __tablename__ = "routes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    start_name: Mapped[str] = mapped_column(String(100), nullable=False)
    end_name: Mapped[str] = mapped_column(String(100), nullable=False)

    route_stops: Mapped[List["RouteStop"]] = relationship("RouteStop", back_populates="route", cascade="all, delete-orphan")
    timetables: Mapped[List["Timetable"]] = relationship("Timetable", back_populates="route", cascade="all, delete-orphan")


class Stop(Base):
    """Legacy model for existing tests - kept for backward compatibility."""
    __tablename__ = "stops"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stop_name: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)

    route_stops: Mapped[List["RouteStop"]] = relationship("RouteStop", back_populates="stop", cascade="all, delete-orphan")


class RouteStop(Base):
    """Legacy model for existing tests - kept for backward compatibility."""
    __tablename__ = "route_stops"
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), primary_key=True)
    stop_id: Mapped[int] = mapped_column(ForeignKey("stops.id", ondelete="CASCADE"), primary_key=True)
    stop_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    fare_stage: Mapped[Optional[int]] = mapped_column(Integer)

    route: Mapped["Route"] = relationship("Route", back_populates="route_stops")
    stop: Mapped["Stop"] = relationship("Stop", back_populates="route_stops")


class NtcFareMatrix(Base):
    """Legacy model for existing tests - kept for backward compatibility."""
    __tablename__ = "ntc_fare_matrix"
    stage_difference: Mapped[int] = mapped_column(Integer, primary_key=True)
    normal_fare: Mapped[Decimal] = mapped_column(NUMERIC(8, 2), nullable=False)
    semi_luxury_fare: Mapped[Decimal] = mapped_column(NUMERIC(8, 2), nullable=False)
    ac_fare: Mapped[Decimal] = mapped_column(NUMERIC(8, 2), nullable=False)


class Timetable(Base):
    """Legacy model for existing tests - kept for backward compatibility."""
    __tablename__ = "timetables"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    day_type: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)

    __table_args__ = (
        CheckConstraint("day_type IN ('Weekday', 'Saturday', 'Sunday / Holiday')", name="ck_timetables_day_type"),
        CheckConstraint("direction IN ('Outbound', 'Inbound')", name="ck_timetables_direction"),
    )

    route: Mapped["Route"] = relationship("Route", back_populates="timetables")


# =============================================================================
# New Supabase-aligned models (public schema)
# =============================================================================

class PublicRoute(Base):
    """Route model aligned with public.routes table in Supabase."""
    __tablename__ = "routes"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    start_name: Mapped[str] = mapped_column(String(100), nullable=False)
    end_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    route_stops: Mapped[List["PublicRouteStop"]] = relationship("PublicRouteStop", back_populates="route", cascade="all, delete-orphan")
    timetables: Mapped[List["PublicTimetable"]] = relationship("PublicTimetable", back_populates="route", cascade="all, delete-orphan")


class PublicRouteStop(Base):
    """Route stop model aligned with public.route_stops table in Supabase."""
    __tablename__ = "route_stops"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("public.routes.id", ondelete="CASCADE"), nullable=False)
    stage_number: Mapped[int] = mapped_column(Integer, nullable=False)
    stop_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stop_order: Mapped[int] = mapped_column(Integer, nullable=False)

    route: Mapped["PublicRoute"] = relationship("PublicRoute", back_populates="route_stops")


class PublicFareStage(Base):
    """Fare stage model aligned with public.fare_stages table in Supabase."""
    __tablename__ = "fare_stages"
    __table_args__ = {"schema": "public"}

    stage_diff: Mapped[int] = mapped_column(Integer, primary_key=True)
    normal_fare: Mapped[Decimal] = mapped_column(NUMERIC(8, 2), nullable=False)


class PublicTimetable(Base):
    """Timetable model aligned with public.timetables table in Supabase."""
    __tablename__ = "timetables"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("public.routes.id", ondelete="CASCADE"), nullable=False)
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    arrival_estimate: Mapped[Optional[time]] = mapped_column(Time)
    day_type: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    route: Mapped["PublicRoute"] = relationship("PublicRoute", back_populates="timetables")


class AdminUser(Base):
    __tablename__ = "admin_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="ADMIN")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admin_users.id"))
    admin_username: Mapped[Optional[str]] = mapped_column(String(50))
    action_summary: Mapped[Optional[str]] = mapped_column(Text)
    percentage_change: Mapped[Optional[Decimal]] = mapped_column(NUMERIC(8, 2))