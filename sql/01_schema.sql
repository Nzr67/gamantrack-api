-- GamanTrack Database Schema (aligned to seed script)

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    route_number VARCHAR(20) NOT NULL UNIQUE,
    start_name VARCHAR(100) NOT NULL,
    end_name VARCHAR(100) NOT NULL
);

CREATE TABLE stops (
    id SERIAL PRIMARY KEY,
    stop_name VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL
);

CREATE TABLE route_stops (
    route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    stop_id INTEGER NOT NULL REFERENCES stops(id) ON DELETE CASCADE,
    stop_sequence INTEGER NOT NULL,
    fare_stage INTEGER,
    PRIMARY KEY (route_id, stop_id)
);

CREATE TABLE ntc_fare_matrix (
    stage_difference INTEGER NOT NULL,
    normal_fare DECIMAL(8,2) NOT NULL,
    semi_luxury_fare DECIMAL(8,2) NOT NULL,
    ac_fare DECIMAL(8,2) NOT NULL,
    PRIMARY KEY (stage_difference)
);

CREATE TABLE timetables (
    id BIGSERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    departure_time TIME NOT NULL,
    day_type VARCHAR(20) NOT NULL CHECK (day_type IN ('Weekday', 'Saturday', 'Sunday / Holiday')),
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('Outbound', 'Inbound'))
);

CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'ADMIN'
);

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES admin_users(id),
    admin_username VARCHAR(50),
    action_summary TEXT,
    percentage_change DECIMAL(8,2)
);