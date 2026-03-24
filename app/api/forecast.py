from flask import Blueprint, jsonify, request

from app.services import forecast_service, geocoding_service

forecast_bp = Blueprint("forecast", __name__)


@forecast_bp.route("/forecast")
def get_forecast():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    location = request.args.get("location", type=str)

    if lat is not None and lon is not None:
        pass
    elif location:
        results = geocoding_service.get_coordinates(location)
        if not results:
            return jsonify({"error": f"No results found for '{location}'"}), 404
        lat = results[0]["latitude"]
        lon = results[0]["longitude"]
    else:
        return jsonify({"error": "Provide lat/lon or location parameter"}), 400

    try:
        data = forecast_service.get_forecast(lat, lon)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch forecast: {e}"}), 502

    return jsonify(data)
