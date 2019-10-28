import logging

from flask import Flask
from flask.logging import default_handler
from flask_cors import CORS

from app import oauth
from app import routes
from app import settings
from app import errors

_logger = logging.getLogger(__package__)


def configure_logging(logger_override=None):
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if logger_override:
        root.addHandler(logger_override)
        root.setLevel(logger_override.level)
    else:
        root.addHandler(default_handler)

    if settings.DEBUG:
        root.setLevel(logging.DEBUG)
        root.debug("Debug logging activated")


def create_app(logger_override=None):
    app = Flask(__name__)

    # app.logger.handlers.extend(logger_override.handlers)
    # app.logger.setLevel(logger_override.level)

    configure_logging(logger_override)

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
    _logger.info("Running application")
    app = create_app()
    _logger.info("Listening on " + str(settings.HOST) + ":" + str(settings.PORT))
    app.run(host=settings.HOST, port=settings.PORT, use_reloader=False)


if __name__ == "__main__":
    main()
