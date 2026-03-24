import requests
from flask import current_app

HOURLY_PARAMS = [
    "temperature_2m",
    "dewpoint_2m",
    "rain",
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "visibility",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
]

DAILY_PARAMS = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
]


def fetch_forecast(lat, lon):
    """Fetch hourly and daily forecast from Open-Meteo. Raises on HTTP errors."""
    url = current_app.config["OPEN_METEO_FORECAST_URL"]
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_PARAMS),
        "daily": ",".join(DAILY_PARAMS),
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_geocode(name):
    """Fetch geocoding results from Open-Meteo. Raises on HTTP errors."""
    url = current_app.config["OPEN_METEO_GEOCODING_URL"]
    params = {"name": name, "count": 5, "language": "en"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()
