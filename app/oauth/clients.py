import abc
import math
import time
import logging
import uuid
import urllib
from six.moves.urllib.parse import urlencode

from flask import redirect, jsonify, request
from authlib.flask.client import RemoteApp
from authlib.client.client import OAuthClient
import requests

from app.oauth.mock_data import ACCESS_TOKEN, ID_TOKEN, RS256_PUBLIC
from app.session import session as server_session
from app.session_utils import get_session_data_or_abort
from app import settings
from .token_decoders import SimpleTokenDecoder, JWKSTokenDecoder

_logger = logging.getLogger(__name__)


class BaseClient(abc.ABC, OAuthClient):
    token_decoder = None

    def login(self):
        _logger.debug(
            "login, redirecting to %s, audience %s",
            settings.OAUTH_CALLBACK_URL,
            settings.OAUTH_AUDIENCE,
        )
        return self.authorize_redirect(
            redirect_uri=settings.OAUTH_CALLBACK_URL, audience=settings.OAUTH_AUDIENCE
        )

    def callback(self):
        if settings.REDIRECT_LOGGED_IN_URL:
            _logger.debug(
                "callback, redirecting to %s", settings.REDIRECT_LOGGED_IN_URL
            )
            return redirect(settings.REDIRECT_LOGGED_IN_URL)
        _logger.debug("callback, no redirect URL set, returning 200")
        return jsonify({}), 200

    @abc.abstractmethod
    def logout(self):
        pass

    @abc.abstractmethod
    def delete_user(self):
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
        _logger.debug(
            "authorize_redirect, redirecting to %s", settings.OAUTH_CALLBACK_URL
        )
        return redirect(settings.OAUTH_CALLBACK_URL)

    def logout(self):
        _logger.debug("logout, redirecting to %s", settings.REDIRECT_LOGOUT_URL)
        return redirect(settings.REDIRECT_LOGOUT_URL)

    def delete_user(self):
        _logger.warn(
            "MockClient delete_user. Returning 200, but cannot delete mock user."
        )
        return jsonify({}), 200

    def authorize_access_token(self, **kwargs):
        expiration_seconds = 60 * 60 * 24
        token = {
            "access_token": ACCESS_TOKEN,
            "expires_at": math.floor(time.time()) + expiration_seconds,
            "expires_in": expiration_seconds,
            "id_token": ID_TOKEN,
            "scope": "openid profile",
            "token_type": "Bearer",
        }
        _logger.debug("authorize_access_token, values %s", token)
        return token


class Auth0Client(BaseClient, RemoteApp):
    token_decoder = JWKSTokenDecoder(settings.OAUTH_JWKS_URL)
    management_session_id = None

    def _get_management_token(self):
        if self.management_session_id:
            # Get the payload from cache. Might be expired and not exist anymore.
            payload = server_session.get(self.management_session_id)
            if payload and "access_token" in payload:
                return payload["access_token"]

        payload = self._get_management_token_from_remote()
        access_token = payload.get("access_token", None)
        if not access_token:
            raise Exception("Could not find access_token in response")

        expires_in = payload.get("expires_in", None)
        session_uuid = uuid.uuid4().hex
        server_session.create_session(session_uuid, payload, expire_seconds=expires_in)
        self.management_session_id = session_uuid
        return access_token

    def _get_management_token_from_remote(self):
        auth_token_url = f"https://{settings.OAUTH_DOMAIN}/oauth/token"
        auth_headers = {"Content-Type": "application/json"}
        auth_payload = {
            "grant_type": "client_credentials",
            "client_id": settings.AUTH0_MANAGEMENT_CLIENT_ID,
            "client_secret": settings.AUTH0_MANAGEMENT_CLIENT_SECRET,
            "audience": f"https://{settings.OAUTH_DOMAIN}/api/v2/",
        }
        res = requests.post(auth_token_url, headers=auth_headers, json=auth_payload)
        if not res or not res.status_code == 200:
            raise Exception("Could not get management authentication token")

        json_response = res.json()
        return json_response

    def logout(self):
        redirect_url = request.args.get("redirect_url")
        if not redirect_url:
            redirect_url = settings.REDIRECT_LOGOUT_URL
        params = {"returnTo": redirect_url, "client_id": settings.OAUTH_CLIENT_ID}
        redirect_uri = self.api_base_url + "/v2/logout?" + urlencode(params)
        _logger("logout, redirecting to %s", redirect_uri)
        return redirect(redirect_url)

    def delete_user(self, subject):
        _logger.debug("delete_user")
        token = self._get_management_token()
        management_url = f"https://{settings.OAUTH_DOMAIN}/api/v2"
        headers = {"Authorization": "Bearer " + token}
        res = requests.delete(
            management_url + "/users/" + urllib.parse.quote(subject), headers=headers
        )
        if not res or res.status_code >= 400:
            raise Exception(f"Could not delete user {subject}: {res.status_code}")
        return True
