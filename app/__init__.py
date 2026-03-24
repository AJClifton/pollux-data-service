from flask import Flask

from app.core.config import DevelopmentConfig
from app.core.extensions import db, init_redis


def create_app(config_class=None):
    app = Flask(__name__)
    config_class = config_class or DevelopmentConfig
    app.config.from_object(config_class)

    db.init_app(app)
    init_redis(app)

    from app.api.routes import register_blueprints
    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app
