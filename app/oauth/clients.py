import abc
import math
import time
import logging
from six.moves.urllib.parse import urlencode

from flask import redirect, jsonify, request
from authlib.flask.client import RemoteApp
from authlib.client.client import OAuthClient

from app.oauth.mock_data import ACCESS_TOKEN, ID_TOKEN, RS256_PUBLIC
from app import settings
from .token_decoders import SimpleTokenDecoder, JWKSTokenDecoder

_logger = logging.getLogger(__name__)


class BaseClient(abc.ABC, OAuthClient):
    token_decoder = None

    def login(self):
        return self.authorize_redirect(
            redirect_uri=settings.OAUTH_CALLBACK_URL, audience=settings.OAUTH_AUDIENCE
        )

    def callback(self):
        if settings.REDIRECT_LOGGED_IN_URL:
            return redirect(settings.REDIRECT_LOGGED_IN_URL)
        return jsonify({}), 200

    @abc.abstractmethod
    def logout(self):
        pass


class MockClient(BaseClient):
    token_decoder = SimpleTokenDecoder(RS256_PUBLIC)

    def __init__(self, *args, token_decoder=None, **kwargs):
        kwargs.pop("client_id", None)
        if token_decoder:
            self.token_decoder = token_decoder
        _logger.info("You can call /callback to create the session.")
        _logger.info("It will return a cookie containing the session ID.")
        super().__init__(*args, **kwargs)

    def authorize_redirect(self, redirect_uri=None, **kwargs):
        return redirect(settings.OAUTH_CALLBACK_URL)

    def logout(self):
        return redirect(settings.REDIRECT_LOGOUT_URL)

    def authorize_access_token(self, **kwargs):
        expiration_seconds = 60 * 60 * 24
        return {
            "access_token": ACCESS_TOKEN,
            "expires_at": math.floor(time.time()) + expiration_seconds,
            "expires_in": expiration_seconds,
            "id_token": ID_TOKEN,
            "scope": "openid profile",
            "token_type": "Bearer",
        }


class Auth0Client(BaseClient, RemoteApp):
    token_decoder = JWKSTokenDecoder(settings.OAUTH_JWKS_URL)

    def logout(self):
        redirect_url = request.args.get("redirect_url")
        if not redirect_url:
            redirect_url = settings.REDIRECT_LOGOUT_URL
        params = {"returnTo": redirect_url, "client_id": settings.OAUTH_CLIENT_ID}
        return redirect(self.api_base_url + "/v2/logout?" + urlencode(params))
