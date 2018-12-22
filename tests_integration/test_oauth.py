import math
import time
from flask import session, jsonify
from unittest.mock import Mock, MagicMock

from app.app import create_app
from app.session import session as server_session
from app.oauth.decorators import requires_auth
from app.oauth.clients import MockClient
from app import settings

from app.oauth.mock_data import RS256_PUBLIC, ACCESS_TOKEN, ID_TOKEN, ID_TOKEN_DATA


def get_mock_tokens():
    expiration_seconds = 24 * 3600
    mock_token = {
        "access_token": ACCESS_TOKEN,
        "expires_at": math.floor(time.time()) + expiration_seconds,
        "expires_in": expiration_seconds,
        "id_token": ID_TOKEN,
        "scope": "openid profile",
        "token_type": "Bearer",
    }
    return mock_token


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
            assert server_session_data.get("access_token") == ACCESS_TOKEN
            assert server_session_data.get("id_token") == ID_TOKEN
            return jsonify({}), 200

        base_client = MockClient()
        mock_oauth_client = Mock(wraps=base_client)
        mock_oauth_client.authorize_access_token = MagicMock(
            return_value=get_mock_tokens()
        )

        def get_key(token):
            return RS256_PUBLIC

        # Patch the oauth authorize_access_token method that exchanges a code for
        # tokens.
        monkeypatch.setattr(
            "app.api.get_client", MagicMock(return_value=mock_oauth_client)
        )

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

        def get_key(token):
            return RS256_PUBLIC

        # Patch the oauth authorize_access_token method that exchanges a code for
        # tokens.
        base_client = MockClient()
        mock_oauth_client = Mock(wraps=base_client)
        mock_oauth_client.authorize_access_token = MagicMock(
            return_value=get_mock_tokens()
        )
        monkeypatch.setattr(
            "app.api.get_client", MagicMock(return_value=mock_oauth_client)
        )
        monkeypatch.setattr(
            "app.oauth.decorators.get_client", MagicMock(return_value=mock_oauth_client)
        )

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

        def get_key(token):
            return RS256_PUBLIC

        mock_tokens = get_mock_tokens()
        mock_tokens.update({"expires_at": math.floor(time.time()) + 2, "expires_in": 2})

        # Patch the oauth authorize_access_token method that exchanges a code for
        # tokens.
        base_client = MockClient()
        mock_oauth_client = Mock(wraps=base_client)
        mock_oauth_client.authorize_access_token = MagicMock(return_value=mock_tokens)
        monkeypatch.setattr(
            "app.oauth.decorators.get_client", MagicMock(return_value=mock_oauth_client)
        )
        monkeypatch.setattr(
            "app.api.get_client", MagicMock(return_value=mock_oauth_client)
        )

        # Login, create session
        response = client.get("/callback")
        assert response.status_code == 302

        response = client.get("/test-authenticated")
        assert response.status_code == 200

        time.sleep(3)  # Wait for session to expire

        response = client.get("/test-authenticated")
        assert response.status_code == 302
        assert response.location == settings.REDIRECT_LOGIN_URL

    def test_mock_oauth(self, monkeypatch):
        monkeypatch.setattr("app.settings.MOCK_OAUTH", True)
        app = create_app()
        with app.test_client() as client:
            response = client.get("/login")
            assert response.status_code == 302
            assert response.location == settings.OAUTH_CALLBACK_URL
            response = client.get("/callback")
            assert response.status_code == 302
            assert response.location == settings.REDIRECT_LOGGED_IN_URL
            assert "session=" in response.headers.get("Set-Cookie")
            response = client.get("/me")
            assert response.status_code == 200
            assert response.json["iss"] == ID_TOKEN_DATA["iss"]
            assert response.json["nickname"] == ID_TOKEN_DATA["nickname"]
            assert response.json["name"] == ID_TOKEN_DATA["name"]
            assert response.json["sub"] == ID_TOKEN_DATA["sub"]
            assert response.json["aud"] == ID_TOKEN_DATA["aud"]
