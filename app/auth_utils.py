from functools import wraps
import logging
from jose import jwt
from flask import session, redirect
import requests
from app.session import session as server_session
from app import settings
from app.errors import (
    AppError,
    ERROR_TOKEN_EXPIRED,
    ERROR_TOKEN_CLAIMS,
    ERROR_TOKEN_SIGNATURE,
    ERROR_JWKS_KEY_NOT_FOUND,
)

_logger = logging.getLogger(__name__)


def get_session_data_or_none():
    try:
        session_data = server_session.get(session[settings.SESSION_ID])
        return session_data
    except Exception:
        return None


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
        decoded = decode_token(access_token, settings.OAUTH_AUDIENCE)
        _logger.debug(f"Access granted to {decoded.get('sub')}")
        return f(*args, **kwargs)

    return decorated


def get_key_from_jwks(token):
    """
    Iterate on the keys from the JWKS to find the one matching the token header's kid
    (key id).
    """
    jwks = jwks_fetcher.get()
    unverified_header = jwt.get_unverified_header(token)
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
            return rsa_key
    raise AppError(ERROR_JWKS_KEY_NOT_FOUND)


def decode_token(token, audience):
    """
    Decode the specified token using keys from the JWKS endpoint.
    The audience has to match the token's audience.
    """
    payload = None
    rsa_key = get_key_from_jwks(token)
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[settings.OAUTH_SIGNING_ALGORITHM],
            audience=audience,
            issuer=settings.OAUTH_BASE_URL + "/",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AppError(ERROR_TOKEN_EXPIRED)
    except jwt.JWTClaimsError:
        raise AppError(ERROR_TOKEN_CLAIMS)
    except jwt.JWTError:
        raise AppError(ERROR_TOKEN_SIGNATURE)


class JWKSFetcher:
    """
    Class that fetches the JWKS from the defined URL and keeps it in cache.
    For now, if keys are rotated, the program needs to be restarted.
    """

    jwks = None

    def __init__(self, url):
        self.url = url

    def get(self):
        if not self.jwks:
            resp = requests.get(self.url)
            self.jwks = resp.json()
        return self.jwks


jwks_fetcher = JWKSFetcher(settings.OAUTH_JWKS_URL)
