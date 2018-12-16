import logging
from jose import jwt

from flask import session

from app.session import session as server_session
from app import settings

_logger = logging.getLogger(__name__)


def get_session_data_or_none():
    """
    Return the server-side session data or None,
    based on the client-side session id.
    Server-side session is a dict containing an access_token, an id_token, and other
    information.
    """
    try:
        session_data = server_session.get(session[settings.SESSION_ID])
        return session_data
    except Exception:
        return None


def create_token(payload, key, headers=None):
    """
    Create a token based on the given key.
    It can be decoded using decode_token method from oauth utils.
    Mainly needed for testing/mocking purpose.
    """
    token = jwt.encode(payload, key, settings.OAUTH_SIGNING_ALGORITHM, headers=headers)
    return token
