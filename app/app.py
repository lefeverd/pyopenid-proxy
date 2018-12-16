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

    CORS(
        app,
        supports_credentials=True,
        origins=["http://127.0.0.1:8081", "https://127.0.0.1:8081"],
    )
    oauth.init_app(app)
    routes.init_app(app)
    errors.init_app(app)

    return app


def main():
    configure_logging()
    _logger.info("Running application")
    app = create_app()
    app.run(host=settings.HOST, port=settings.PORT, use_reloader=False)


if __name__ == "__main__":
    main()
