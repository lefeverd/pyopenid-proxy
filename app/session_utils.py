from flask import abort, session
import logging

from app.session import session as server_session
from app import settings

_logger = logging.getLogger(__name__)


def get_session_data_or_abort():
    session_id = session[settings.SESSION_ID]
    _logger.debug("Found session_id %s in session, getting session data", session_id)
    session_data = server_session.get(session_id)
    if not session_data:
        _logger.warn("Cannot get session data, returning 401")
        abort(401)

    _logger.debug("Returning session data %s", session_data)
    return session_data
