import json
from datetime import datetime
from unittest.mock import patch

from app.models.hourly_forecast import HourlyForecast
from app.models.daily_forecast import DailyForecast
from app.services import forecast_service


SAMPLE_API_RESPONSE = {
    "hourly": {
        "time": ["2026-03-24T00:00", "2026-03-24T01:00"],
        "temperature_2m": [10.5, 9.8],
        "dewpoint_2m": [5.0, 4.5],
        "rain": [0.0, 0.1],
        "cloud_cover": [50.0, 60.0],
        "cloud_cover_low": [20.0, 30.0],
        "cloud_cover_mid": [15.0, 20.0],
        "cloud_cover_high": [10.0, 10.0],
        "visibility": [10000.0, 8000.0],
        "surface_pressure": [1013.0, 1012.5],
        "wind_speed_10m": [5.0, 6.0],
        "wind_direction_10m": [180.0, 190.0],
        "wind_gusts_10m": [10.0, 12.0],
    },
    "daily": {
        "time": ["2026-03-24"],
        "weather_code": [3],
        "temperature_2m_max": [12.0],
        "temperature_2m_min": [8.0],
        "precipitation_sum": [0.1],
        "precipitation_probability_max": [20.0],
        "wind_speed_10m_max": [15.0],
    },
}


class TestGetForecast:

    def test_get_forecast_cachedInRedis_returnsCachedData(self, app, mock_redis):
        # Arrange
        cached_data = {"latitude": 51.51, "longitude": -0.13, "hourly": [], "daily": []}
        mock_redis.get.return_value = json.dumps(cached_data)

        with app.app_context():
            # Act
            result = forecast_service.get_forecast(51.51, -0.13)

            # Assert
            assert result == cached_data

    def test_get_forecast_redisMissDbHit_returnsDbData(self, app, mock_redis, db_session):
        # Arrange
        row = HourlyForecast(
            latitude=51.51, longitude=-0.13,
            datetime=datetime(2026, 3, 24, 0, 0),
            temperature=10.5, dewpoint=5.0, rain=0.0,
            cloud_cover_total=50.0, cloud_cover_low=20.0,
            cloud_cover_mid=15.0, cloud_cover_high=10.0,
            visibility=10000.0, surface_pressure=1013.0,
            wind_speed=5.0, wind_direction=180.0, wind_gusts=10.0,
        )
        db_session.add(row)
        db_session.commit()

        with app.app_context():
            # Act
            result = forecast_service.get_forecast(51.51, -0.13)

            # Assert
            assert result["latitude"] == 51.51
            assert len(result["hourly"]) == 1
            assert result["hourly"][0]["temperature"] == 10.5

    def test_get_forecast_allMiss_fetchesFromApi(self, app, mock_redis):
        # Arrange
        with app.app_context():
            with patch(
                "app.services.open_meteo_client.fetch_forecast",
                return_value=SAMPLE_API_RESPONSE,
            ):
                # Act
                result = forecast_service.get_forecast(51.51, -0.13)

                # Assert
                assert result["latitude"] == 51.51
                assert len(result["hourly"]) == 2
                assert len(result["daily"]) == 1
                assert result["hourly"][0]["temperature"] == 10.5
                assert result["daily"][0]["weather_code"] == 3

    def test_get_forecast_apiResponse_persistsToDb(self, app, mock_redis, db_session):
        # Arrange
        with app.app_context():
            with patch(
                "app.services.open_meteo_client.fetch_forecast",
                return_value=SAMPLE_API_RESPONSE,
            ):
                # Act
                forecast_service.get_forecast(51.51, -0.13)

                # Assert
                hourly_count = HourlyForecast.query.filter_by(
                    latitude=51.51, longitude=-0.13
                ).count()
                daily_count = DailyForecast.query.filter_by(
                    latitude=51.51, longitude=-0.13
                ).count()
                assert hourly_count == 2
                assert daily_count == 1

    def test_get_forecast_roundsCoordinates_usesSameKey(self, app, mock_redis):
        # Arrange
        cached_data = {"latitude": 51.51, "longitude": -0.13, "hourly": [], "daily": []}
        mock_redis.get.return_value = json.dumps(cached_data)

        with app.app_context():
            # Act
            result = forecast_service.get_forecast(51.5074, -0.1278)

            # Assert
            assert result == cached_data
            mock_redis.get.assert_called_with("forecast:51.51:-0.13")
