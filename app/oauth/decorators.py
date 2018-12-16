import logging
from functools import wraps

from flask import redirect

from app.oauth import get_client
from app import settings
from .utils import get_session_data_or_none

_logger = logging.getLogger(__name__)


def requires_auth(f):
    """
    Decorator that verifies the request can go through.
    Check the session_id (client-side) and get the access_token from it (server-side).
    Verify that the access token is valid.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        session_data = get_session_data_or_none()
        if not session_data:
            return redirect(settings.REDIRECT_LOGIN_URL)
        access_token = session_data.get("access_token")
        # TODO: handle token expiration/refresh ?
        decoded = get_client().token_decoder.decode_token(
            access_token, audience=settings.OAUTH_AUDIENCE
        )
        # decoded = decode_token(access_token, settings.OAUTH_AUDIENCE)
        _logger.debug(f"Access granted to {decoded.get('sub')}")
        return f(*args, **kwargs)

    return decorated
