from app.core.extensions import db


class DailyForecast(db.Model):
    __tablename__ = "daily_forecasts"

    latitude = db.Column(db.Float, primary_key=True)
    longitude = db.Column(db.Float, primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    weather_code = db.Column(db.Integer)
    maximum_temperature = db.Column(db.Float)
    minimum_temperature = db.Column(db.Float)
    precipitation_sum = db.Column(db.Float)
    precipitation_probability_max = db.Column(db.Float)
    maximum_wind_speed = db.Column(db.Float)

    def to_dict(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "date": self.date.isoformat(),
            "weather_code": self.weather_code,
            "maximum_temperature": self.maximum_temperature,
            "minimum_temperature": self.minimum_temperature,
            "precipitation_sum": self.precipitation_sum,
            "precipitation_probability_max": self.precipitation_probability_max,
            "maximum_wind_speed": self.maximum_wind_speed,
        }
