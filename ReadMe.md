# GamanTrack API

FastAPI backend powering **GamanTrack**, a Sri Lankan public bus route, timetable, and NTC stage-based ticket fare calculator web application.

## Tech Stack
- **Framework:** Python, FastAPI, Uvicorn
- **Database:** PostgreSQL (hosted on Supabase)
- **Client SDK:** `supabase-py`

## Database Schema
The API connects to four core tables in Supabase (`public` schema):
- **`routes`**: Bus route metadata (`id`, `route_number`, `start_name`, `end_name`, `service_type`, `is_active`).
- **`route_stops`**: Ordered stops along each route with official NTC stage numbers (`route_id`, `stage_number`, `stop_name`, `stop_order`).
- **`fare_stages`**: Master stage-difference lookup table (`stage_diff`, `normal_fare`).
- **`timetables`**: Scheduled departures and estimated arrivals per route (`route_id`, `departure_time`, `arrival_estimate`, `day_type`, `notes`).

## Key Endpoints

### Routes & Stops
- `GET /api/routes/{route_number}/stops` — Returns active route details and ordered stops with stage numbers.
- `GET /api/routes/{route_number}/timetable` — Returns scheduled departures for the specified route.

### Ticket Fare Calculation
- `GET /api/fare/calculate` — Calculates ticket fare based on `|to_stage - from_stage|`.
  - **Query Parameters:** `route_number` (str), `from_stage` (int), `to_stage` (int)
  - **Example:** `GET /api/fare/calculate?route_number=67&from_stage=0&to_stage=52`
  - **Sample Response:**
    ```json
    {
      "route_number": "67",
      "start_name": "Rakwana",
      "end_name": "Colombo",
      "from_stage": 0,
      "to_stage": 52,
      "stage_difference": 52,
      "fare": 615.0,
      "currency": "LKR"
    }
    ```

## Local Setup (Ubuntu)

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate