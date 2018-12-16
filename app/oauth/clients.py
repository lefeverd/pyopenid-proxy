import math
import time

from flask import redirect
from authlib.flask.client import RemoteApp
from authlib.client.client import OAuthClient

from app.oauth.mock_data import ACCESS_TOKEN, ID_TOKEN, RS256_PUBLIC
from app import settings

from .token_decoders import SimpleTokenDecoder, JWKSTokenDecoder


class MockClient(OAuthClient):
    token_decoder = SimpleTokenDecoder(RS256_PUBLIC)

    def __init__(self, *args, token_decoder=None, **kwargs):
        kwargs.pop("client_id", None)
        if token_decoder:
            self.token_decoder = token_decoder
        super().__init__(*args, **kwargs)

    def authorize_redirect(self, redirect_uri=None, **kwargs):
        return redirect(settings.OAUTH_CALLBACK_URL)

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


class Auth0Client(RemoteApp):
    token_decoder = JWKSTokenDecoder(settings.OAUTH_JWKS_URL)
