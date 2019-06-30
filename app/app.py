import logging

from flask import Flask
from flask_cors import CORS

from app import oauth
from app import routes
from app import settings
from app import errors

_logger = logging.getLogger(__package__)


def configure_logging():
    logging.basicConfig()
    _logger.setLevel(logging.INFO)
    if settings.DEBUG:
        _logger.setLevel(logging.DEBUG)
        _logger.debug("Debug logging activated")


def create_app():
    app = Flask(__name__)
    app.secret_key = settings.SECRET_KEY
    if settings.DEBUG:
        app.debug = True

    if settings.CORS_ORIGIN:
        cors_origins = settings.CORS_ORIGIN.split(",")
        CORS(app, supports_credentials=True, origins=cors_origins)

    oauth.init_app(app)
    routes.init_app(app)
    errors.init_app(app)

    return app


def main():
    configure_logging()
    _logger.info("Running application")
    app = create_app()
    _logger.info("Listening on " + str(settings.HOST) + ":" + str(settings.PORT))
    app.run(host=settings.HOST, port=settings.PORT, use_reloader=False)


if __name__ == "__main__":
    main()
