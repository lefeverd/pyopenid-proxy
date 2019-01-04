from flask import abort, session
import logging

from app.session import session as server_session
from app import settings

_logger = logging.getLogger(__name__)


def get_session_data_or_abort():
    session_id = session[settings.SESSION_ID]
    _logger.debug("Found session_id in session")
    session_data = server_session.get(session_id)
    if not session_data:
        abort(401)

    return session_data
