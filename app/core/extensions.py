import redis
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
redis_client = None


def init_redis(app):
    global redis_client
    redis_client = redis.from_url(app.config["REDIS_URL"], decode_responses=True)
