from flask import jsonify, abort, session, redirect, request
import uuid
import logging
import requests
from six.moves.urllib.parse import urlencode
from app import settings
from app.oauth import auth0
from app.session import session as server_session
from app.auth_utils import decode_token, get_session_data_or_none
from app.proxy_routes import proxy_routes

DEFAULT_EXPIRATION_SECONDS = 24 * 3600
_logger = logging.getLogger(__name__)


def index():
    return jsonify({"status": "running"}), 200


def login():
    return auth0.authorize_redirect(
        redirect_uri=settings.OAUTH_CALLBACK_URL, audience=settings.OAUTH_AUDIENCE
    )


def callback():
    try:
        tokens = auth0.authorize_access_token()
        session_uuid = uuid.uuid4().hex
        # Put uuid in client session
        session[settings.SESSION_ID] = session_uuid
        session.permanent = True
        # Save tokens in server-side session
        server_session.create_session(
            session_uuid,
            tokens,
            expire_seconds=tokens.get("expires_in", DEFAULT_EXPIRATION_SECONDS),
        )
        _logger.debug(f"Creating session {session_uuid}")
        return redirect(settings.REDIRECT_LOGGED_IN_URL)
    except Exception as exc:
        _logger.error(exc)
        return jsonify({}), 401


def me():
    try:
        session_id = session[settings.SESSION_ID]
        _logger.debug("Found session_id in session")
        token = server_session.get(session_id)
        _logger.debug("Found session in sessions list")
        # access token can be decoded with audience = actual audience
        # id token can be decoded with audience = client id
        # decoded_access_token = decode_token(access_token, OAUTH_AUDIENCE)
        decoded_id_token = decode_token(token.get("id_token"), settings.OAUTH_CLIENT_ID)
    except KeyError:
        return abort(401)
    return jsonify(decoded_id_token), 200


def logout():
    # Clear client-side session
    session.clear()
    redirect_url = request.args.get("redirect_url")
    if not redirect_url:
        redirect_url = settings.REDIRECT_LOGOUT_URL
    try:
        # Clear server-side session
        session_id = session[settings.SESSION_ID]
        session[session_id] = ""
        server_session.destroy_session(session_id)
        _logger.debug(f"Cleared session {session_id}")
    except Exception:
        pass
    # TODO: pass return URL as param ?
    params = {"returnTo": redirect_url, "client_id": settings.OAUTH_CLIENT_ID}
    return redirect(auth0.api_base_url + "/v2/logout?" + urlencode(params))


def proxy(path):
    """
    Special route used to proxy requests defined in the routes.yaml configuration file.
    """
    print(f"Proxying {path}")
    route = proxy_routes.get(request.endpoint)
    if not route:
        _logger.error(f"No route configuration could be found for path {path}")
        return jsonify({}), 500
    _logger.debug(f"Using proxy route {route.name} to {route.upstream}")

    headers = dict(request.headers.to_list())
    session_data = get_session_data_or_none()
    if session_data:
        access_token = session_data.get("access_token")
        id_token = session_data.get("id_token")
        id_token_data = decode_token(id_token, settings.OAUTH_CLIENT_ID)
        headers["Authorization"] = f"Bearer {access_token}"
        headers["X-Userinfo"] = id_token_data
        _logger.debug("Added Authorization header")

    response = requests.request(request.method.lower(), f"{route.upstream}/{path}")
    return jsonify(response.json()), response.status_code
