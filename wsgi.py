import logging
from app.app import create_app

gunicorn_logger = logging.getLogger("gunicorn.error")
app = create_app(logger_override=gunicorn_logger)
