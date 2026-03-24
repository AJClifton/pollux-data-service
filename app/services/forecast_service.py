import logging
from datetime import datetime, timezone

from flask import current_app

from app.core.extensions import db
from app.models.daily_forecast import DailyForecast
from app.models.hourly_forecast import HourlyForecast
from app.services import open_meteo_client, redis_service
from app.services.request_coalescer import forecast_coalescer

logger = logging.getLogger(__name__)

HOURLY_FIELD_MAP = {
    "temperature_2m": "temperature",
    "dewpoint_2m": "dewpoint",
    "rain": "rain",
    "cloud_cover": "cloud_cover_total",
    "cloud_cover_low": "cloud_cover_low",
    "cloud_cover_mid": "cloud_cover_mid",
    "cloud_cover_high": "cloud_cover_high",
    "visibility": "visibility",
    "surface_pressure": "surface_pressure",
    "wind_speed_10m": "wind_speed",
    "wind_direction_10m": "wind_direction",
    "wind_gusts_10m": "wind_gusts",
}

DAILY_FIELD_MAP = {
    "weather_code": "weather_code",
    "temperature_2m_max": "maximum_temperature",
    "temperature_2m_min": "minimum_temperature",
    "precipitation_sum": "precipitation_sum",
    "precipitation_probability_max": "precipitation_probability_max",
    "wind_speed_10m_max": "maximum_wind_speed",
}


def get_forecast(lat, lon):
    """Fetch forecast with fallback: Redis -> Database -> Open-Meteo API."""
    lat = round(lat, 2)
    lon = round(lon, 2)
    cache_key = f"forecast:{lat}:{lon}"
    ttl = current_app.config["FORECAST_CACHE_TTL"]

    # 1. Try Redis
    cached = redis_service.cache_get(cache_key)
    if cached:
        return cached

    # 2. Try Database
    db_result = _get_from_db(lat, lon, ttl)
    if db_result:
        redis_service.cache_set(cache_key, db_result, ttl)
        return db_result

    # 3. Fetch from Open-Meteo API (with request coalescing)
    api_data = forecast_coalescer.execute(
        cache_key, open_meteo_client.fetch_forecast, lat, lon
    )

    # Parse and store
    result = _parse_and_store(lat, lon, api_data)
    redis_service.cache_set(cache_key, result, ttl)
    return result


def _get_from_db(lat, lon, ttl):
    """Query DB for forecast rows. Returns None if no fresh data exists."""
    hourly_rows = HourlyForecast.query.filter_by(
        latitude=lat, longitude=lon
    ).order_by(HourlyForecast.datetime.asc()).all()

    daily_rows = DailyForecast.query.filter_by(
        latitude=lat, longitude=lon
    ).order_by(DailyForecast.date.asc()).all()

    if not hourly_rows and not daily_rows:
        return None

    return {
        "latitude": lat,
        "longitude": lon,
        "hourly": [row.to_dict() for row in hourly_rows],
        "daily": [row.to_dict() for row in daily_rows],
    }


def _parse_and_store(lat, lon, api_data):
    """Parse Open-Meteo response into model rows and persist to DB."""
    hourly = api_data.get("hourly", {})
    daily = api_data.get("daily", {})
    hourly_times = hourly.get("time", [])
    daily_times = daily.get("time", [])

    hourly_rows = []
    for i, time_str in enumerate(hourly_times):
        dt = datetime.fromisoformat(time_str)
        row_data = {"latitude": lat, "longitude": lon, "datetime": dt}
        for api_field, model_field in HOURLY_FIELD_MAP.items():
            row_data[model_field] = hourly.get(api_field, [None])[i]

        existing = db.session.get(HourlyForecast, (lat, lon, dt))
        if existing:
            for field, value in row_data.items():
                if field not in ("latitude", "longitude", "datetime"):
                    setattr(existing, field, value)
            hourly_rows.append(existing)
        else:
            row = HourlyForecast(**row_data)
            db.session.add(row)
            hourly_rows.append(row)

    daily_rows = []
    for i, date_str in enumerate(daily_times):
        d = datetime.fromisoformat(date_str).date()
        row_data = {"latitude": lat, "longitude": lon, "date": d}
        for api_field, model_field in DAILY_FIELD_MAP.items():
            row_data[model_field] = daily.get(api_field, [None])[i]

        existing = db.session.get(DailyForecast, (lat, lon, d))
        if existing:
            for field, value in row_data.items():
                if field not in ("latitude", "longitude", "date"):
                    setattr(existing, field, value)
            daily_rows.append(existing)
        else:
            row = DailyForecast(**row_data)
            db.session.add(row)
            daily_rows.append(row)

    db.session.commit()

    return {
        "latitude": lat,
        "longitude": lon,
        "hourly": [row.to_dict() for row in hourly_rows],
        "daily": [row.to_dict() for row in daily_rows],
    }
