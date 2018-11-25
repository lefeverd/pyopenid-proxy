from flask import Flask
import base64
import json
import mock
from app import api
from app.proxy_routes import ProxyRoute
from tests.tokens_data import ACCESS_TOKEN, ID_TOKEN, RS256_PUBLIC, ID_TOKEN_DATA


def _mock_response(status=200, content="CONTENT", json_data=None):
    mock_resp = mock.Mock()
    mock_resp.status_code = status
    mock_resp.content = content
    if json_data:
        mock_resp.json = mock.Mock(return_value=json_data)
    return mock_resp


class TestApiProxy:
    def test_proxy(self, monkeypatch):
        # Create the test app
        app = Flask(__name__)

        # Add a route to be proxied
        app.add_url_rule("/test/<path:path>", "test", api.proxy)

        # Create the proxy route configuration and mock it
        route = ProxyRoute("test", "/test", "http://127.0.0.1:9999")
        proxy_routes = {route.name: route}
        monkeypatch.setattr("app.api.proxy_routes", proxy_routes)

        # Mock requests to call the following method
        def request(*a, **kw):
            assert kw.get("url") == "http://127.0.0.1:9999/bla"
            return _mock_response(json_data={"status": "ok"})

        monkeypatch.setattr("requests.sessions.Session.request", request)

        client = app.test_client()
        with app.test_request_context():
            # Now call a route that should be proxied, and verify
            # our mocked method is called with the correct arguments
            # Everything going to /test should call 127.0.0.1:9999
            res = client.get("/test/bla")
            assert res.status_code == 200

    def test_proxy_authenticated_headers(self, monkeypatch):
        """
        Test calling the app on an endpoint that should be proxied.
        Emulate authentication by mocking the server-side session to return the needed tokens,
        and verify that these tokens are correctly added to the proxied request.
        """
        # Create the test app
        app = Flask(__name__)

        # Add a route to be proxied
        app.add_url_rule("/test/<path:path>", "test", api.proxy)

        # Create the proxy route configuration and mock it
        route = ProxyRoute("test", "/test", "http://127.0.0.1:9999")
        proxy_routes = {route.name: route}
        monkeypatch.setattr("app.api.proxy_routes", proxy_routes)

        # Mock requests to call the following method
        def request(*a, **kw):
            assert kw.get("url") == "http://127.0.0.1:9999/bla"
            headers = kw.get("headers")
            assert headers.get("Authorization") == f"Bearer {ACCESS_TOKEN}"
            encoded_id_token_data = base64.b64encode(json.dumps(ID_TOKEN_DATA).encode())
            assert headers.get("X-Userinfo") == encoded_id_token_data
            return _mock_response(json_data={"status": "ok"})

        monkeypatch.setattr("requests.sessions.Session.request", request)

        def get_session_data(*a, **kw):
            return {"access_token": ACCESS_TOKEN, "id_token": ID_TOKEN}

        monkeypatch.setattr("app.api.get_session_data_or_none", get_session_data)
        monkeypatch.setattr(
            "app.auth_utils.get_key_from_jwks", lambda *args, **kwargs: RS256_PUBLIC
        )

        client = app.test_client()
        with app.test_request_context():
            # Now call a route that should be proxied, and verify
            # our mocked method is called with the correct arguments
            # Everything going to /test should call 127.0.0.1:9999
            res = client.get("/test/bla")
            assert res.status_code == 200

    def test_proxy_authenticated_headers_removed(self, monkeypatch):
        """
        Test calling the app on an endpoint that should be proxied.
        Without server-side session found, no authorization or X-Userinfo
        headers should be transmitted in the proxied request.
        Be sure that if the original request contains them, they are removed.
        """
        # Create the test app
        app = Flask(__name__)

        # Add a route to be proxied
        app.add_url_rule("/test/<path:path>", "test", api.proxy)

        # Create the proxy route configuration and mock it
        route = ProxyRoute("test", "/test", "http://127.0.0.1:9999")
        proxy_routes = {route.name: route}
        monkeypatch.setattr("app.api.proxy_routes", proxy_routes)

        # Mock requests to call the following method
        def request(*a, **kw):
            assert kw.get("url") == "http://127.0.0.1:9999/bla"
            headers = kw.get("headers")
            assert "Authorization" not in headers
            assert "X-Userinfo" not in headers
            return _mock_response(json_data={"status": "ok"})

        monkeypatch.setattr("requests.sessions.Session.request", request)

        monkeypatch.setattr(
            "app.auth_utils.get_key_from_jwks", lambda *args, **kwargs: RS256_PUBLIC
        )

        client = app.test_client()
        with app.test_request_context():
            # Now call a route that should be proxied, and verify
            # our mocked method is called with the correct arguments
            # Everything going to /test should call 127.0.0.1:9999
            encoded_id_token_data = base64.b64encode(json.dumps(ID_TOKEN_DATA).encode())
            headers = {
                "Authorization": "Bearer fakebearer",
                "X-Userinfo": encoded_id_token_data,
            }
            res = client.get("/test/bla", headers=headers)
            assert res.status_code == 200
