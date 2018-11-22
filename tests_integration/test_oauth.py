import math
import time
from flask import session, jsonify

from jose import jwt

from app.session import session as server_session
from app.auth_utils import requires_auth
from app import settings

from tests.tokens_data import (
    ACCESS_TOKEN_DATA,
    ID_TOKEN_DATA,
    RS256_PRIVATE,
    RS256_PUBLIC,
)


def create_token(payload, key, headers=None):
    """
    Create a token based on the private RS256 test key.
    It can be decoded using decode_token method from auth_utils.
    """
    token = jwt.encode(payload, key, settings.OAUTH_SIGNING_ALGORITHM, headers=headers)
    return token


class TestOAuth:
    def test_index(self, client):
        response = client.get("/")
        assert response.status_code == 200
        json_response = response.json
        assert json_response["status"] == "running"

    def test_cookie_and_session(self, app, client, monkeypatch):
        @app.route("/test-session-cookie", methods=["OPTIONS", "POST"])
        def test_session_cookie():
            # Fake method to verify that we can get the session_id
            # from the request (cookie should have been set and sent along)

            # Get the server-side session based on the client-side session_id
            server_session_data = server_session.get(session.get(settings.SESSION_ID))

            # Tokens should match
            assert server_session_data.get("access_token") == access_token
            assert server_session_data.get("id_token") == id_token
            return jsonify({}), 200

        access_token = create_token(ACCESS_TOKEN_DATA, RS256_PRIVATE)
        id_token = create_token(ID_TOKEN_DATA, RS256_PRIVATE)

        def get_tokens():
            expiration_seconds = 24 * 3600
            return {
                "access_token": access_token,
                "expires_at": math.floor(time.time()) + expiration_seconds,
                "expires_in": expiration_seconds,
                "id_token": id_token,
                "scope": "openid profile",
                "token_type": "Bearer",
            }

        def get_key(token):
            return RS256_PUBLIC

        # Patch the oauth authorize_access_token method that exchanges a code for
        # tokens.
        monkeypatch.setattr("app.oauth.auth0.authorize_access_token", get_tokens)
        monkeypatch.setattr("app.auth_utils.get_key_from_jwks", get_key)

        # Call the callback endpoint, which is responsible of exchanging a code for
        # tokens from the OAuth server.
        # Here we'll use mock data.
        # The response should contain a set-cookie header to set the session_id
        # client-side.
        # The session_id is an opaque (or reference) token.
        response = client.get("/callback")
        assert response.status_code == 302

        # Call another method and see if the session_id is sent in the request.
        # If so, we can get the actual tokens based on the session_id (opaque token)
        client.post("/test-session-cookie", json={})

    def test_get_requires_auth_redirect(self, app, client):
        @app.route("/test-authenticated", methods=["OPTIONS", "GET"])
        @requires_auth
        def test_authenticated():
            return jsonify({}), 200

        response = client.get("/test-authenticated")
        assert response.status_code == 302
        assert response.location == settings.REDIRECT_LOGIN_URL

    def test_get_requires_auth_with_valid_token(self, app, client, monkeypatch):
        @app.route("/test-authenticated", methods=["OPTIONS", "GET"])
        @requires_auth
        def test_authenticated():
            return jsonify({}), 200

        access_token = create_token(ACCESS_TOKEN_DATA, RS256_PRIVATE)
        id_token = create_token(ID_TOKEN_DATA, RS256_PRIVATE)

        def get_tokens():
            expiration_seconds = 24 * 3600
            return {
                "access_token": access_token,
                "expires_at": math.floor(time.time()) + expiration_seconds,
                "expires_in": expiration_seconds,
                "id_token": id_token,
                "scope": "openid profile",
                "token_type": "Bearer",
            }

        def get_key(token):
            return RS256_PUBLIC

        # Patch the oauth authorize_access_token method that exchanges a code for
        # tokens.
        monkeypatch.setattr("app.oauth.auth0.authorize_access_token", get_tokens)
        monkeypatch.setattr("app.auth_utils.get_key_from_jwks", get_key)

        # Login, create session
        response = client.get("/callback")
        assert response.status_code == 302

        response = client.get("/test-authenticated")
        assert response.status_code == 200

    def test_session_expiration(self, app, client, monkeypatch):
        @app.route("/test-authenticated", methods=["OPTIONS", "GET"])
        @requires_auth
        def test_authenticated():
            return jsonify({}), 200

        access_token = create_token(ACCESS_TOKEN_DATA, RS256_PRIVATE)
        id_token = create_token(ID_TOKEN_DATA, RS256_PRIVATE)

        def get_tokens():
            expiration_seconds = 2
            return {
                "access_token": access_token,
                "expires_at": math.floor(time.time()) + expiration_seconds,
                "expires_in": expiration_seconds,
                "id_token": id_token,
                "scope": "openid profile",
                "token_type": "Bearer",
            }

        def get_key(token):
            return RS256_PUBLIC

        # Patch the oauth authorize_access_token method that exchanges a code for
        # tokens.
        monkeypatch.setattr("app.oauth.auth0.authorize_access_token", get_tokens)
        monkeypatch.setattr("app.auth_utils.get_key_from_jwks", get_key)

        # Login, create session
        response = client.get("/callback")
        assert response.status_code == 302

        response = client.get("/test-authenticated")
        assert response.status_code == 200

        time.sleep(3)  # Wait for session to expire

        response = client.get("/test-authenticated")
        assert response.status_code == 302
        assert response.location == settings.REDIRECT_LOGIN_URL
