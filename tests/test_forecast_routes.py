import json
from unittest.mock import patch


SAMPLE_FORECAST = {
    "latitude": 51.51,
    "longitude": -0.13,
    "hourly": [{"temperature": 10.5}],
    "daily": [{"weather_code": 3}],
}

SAMPLE_GEOCODE = [
    {"name": "London", "latitude": 51.51, "longitude": -0.13,
     "country": "United Kingdom", "admin1": "England"}
]


class TestForecastRoute:

    def test_get_forecast_validLatLon_returns200(self, client, mock_redis):
        # Arrange
        with patch(
            "app.api.forecast.forecast_service.get_forecast",
            return_value=SAMPLE_FORECAST,
        ):
            # Act
            response = client.get("/api/forecast?lat=51.51&lon=-0.13")

            # Assert
            assert response.status_code == 200
            data = response.get_json()
            assert data["latitude"] == 51.51

    def test_get_forecast_validLocation_returns200(self, client, mock_redis):
        # Arrange
        with patch(
            "app.api.forecast.geocoding_service.get_coordinates",
            return_value=SAMPLE_GEOCODE,
        ), patch(
            "app.api.forecast.forecast_service.get_forecast",
            return_value=SAMPLE_FORECAST,
        ):
            # Act
            response = client.get("/api/forecast?location=London")

            # Assert
            assert response.status_code == 200
            data = response.get_json()
            assert data["latitude"] == 51.51

    def test_get_forecast_noParams_returns400(self, client, mock_redis):
        # Arrange / Act
        response = client.get("/api/forecast")

        # Assert
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_get_forecast_locationNotFound_returns404(self, client, mock_redis):
        # Arrange
        with patch(
            "app.api.forecast.geocoding_service.get_coordinates",
            return_value=[],
        ):
            # Act
            response = client.get("/api/forecast?location=xyznonexistent")

            # Assert
            assert response.status_code == 404

    def test_get_forecast_upstreamFailure_returns502(self, client, mock_redis):
        # Arrange
        with patch(
            "app.api.forecast.forecast_service.get_forecast",
            side_effect=Exception("API down"),
        ):
            # Act
            response = client.get("/api/forecast?lat=51.51&lon=-0.13")

            # Assert
            assert response.status_code == 502
