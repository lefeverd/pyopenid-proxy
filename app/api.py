from flask import jsonify, abort, session, request
import base64
import uuid
import json
import logging
import requests
from app import settings
from app.oauth import get_client
from app.session import session as server_session
from app.session_utils import get_session_data_or_abort
from app.oauth.utils import get_session_data_or_none
from app.proxy_routes import proxy_routes
from app.errors import AppError, ERROR_DELETE_USER

DEFAULT_EXPIRATION_SECONDS = 24 * 3600
_logger = logging.getLogger(__name__)


def index():
    return jsonify({"status": "running"}), 200


def login():
    _logger.debug("Login")
    return get_client().login()


def callback():
    try:
        tokens = get_client().authorize_access_token()
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
        return get_client().callback()
    except Exception as exc:
        _logger.error(exc)
        return jsonify({}), 401


def me():
    _logger.debug("/me, getting session data")
    try:
        session_data = get_session_data_or_abort()
        _logger.debug("got session data %s, trying to decode", session_data)
        # access token can be decoded with audience = actual audience
        # id token can be decoded with audience = client id
        # decoded_access_token = decode_token(access_token, OAUTH_AUDIENCE)

        decoded_id_token = get_client().token_decoder.decode_token(
            session_data.get("id_token"), audience=settings.OAUTH_CLIENT_ID
        )
        _logger.debug("session data decoded")
    except KeyError:
        _logger.warn("Could not find session data, aborting")
        return abort(401)
    _logger.debug("/me, %s", decoded_id_token)
    return jsonify(decoded_id_token), 200


def logout():
    # Clear client-side session
    session.clear()
    try:
        # Clear server-side session
        session_id = session[settings.SESSION_ID]
        session[session_id] = ""
        server_session.destroy_session(session_id)
        _logger.debug(f"Cleared session {session_id}")
    except Exception:
        pass
    return get_client().logout()


def delete():
    session_data = get_session_data_or_abort()
    decoded_id_token = get_client().token_decoder.decode_token(
        session_data.get("id_token"), audience=settings.OAUTH_CLIENT_ID
    )
    _logger.info(f"Deleting user {decoded_id_token['sub']}")
    try:
        get_client().delete_user(decoded_id_token["sub"])
        return jsonify({"success": "true"}), 200
    except Exception as e:
        _logger.error(e)
        raise AppError(description=e.message)


def proxy(path):
    """
    Special route used to proxy requests defined in the routes.yaml configuration file.
    """
    _logger.debug(f"Proxying {path}")
    route = proxy_routes.get(request.endpoint)
    if not route:
        _logger.error(f"No route configuration could be found for path {path}")
        return jsonify({}), 500
    _logger.debug(f"Using proxy route {route.name} to {route.upstream}")

    headers = dict(request.headers.to_wsgi_list())
    sanitize_headers(headers)
    headers.update(get_session_data_headers())

    # Allows CORS, will still be wrapped by flask_cors
    if request.method in ["OPTIONS", "HEAD"]:
        return "", 200

    def get_file_data():
        file_data = b""
        chunk_size = 4096
        while True:
            chunk = request.stream.read(chunk_size)
            if len(chunk) == 0:
                break
            file_data += chunk
        return file_data

    # TODO: handle larger file upload with chuncking/streaming ?
    # use requests data or file ?
    # def exhaust(stream):
    #    while True:
    #        out = stream.read(1024 * 1024)
    #        if not out:
    #            break
    #        yield out

    data = None
    if request.headers.get("Content-Type", None) and request.headers.get(
        "Content-Type"
    ).startswith("multipart/form-data"):
        data = get_file_data()
    else:
        data = request.data

    full_path = request.full_path[request.full_path.find(path) :]
    response = requests.request(
        request.method.lower(),
        f"{route.upstream}/{full_path}",
        headers=headers,
        data=data,
    )

    return (response.content, response.status_code, response.headers.items())


def sanitize_headers(headers):
    """
    Authorization and X-Userinfo headers are added based on the server-side session.
    Be sure to remove them from the original request if present.
    """
    auth_header = headers.pop("Authorization", None)
    if auth_header:
        _logger.warning(
            f"Possible fraud: Authorization header was set to {auth_header}"
        )
    userinfo_header = headers.pop("X-Userinfo", None)
    if userinfo_header:
        _logger.warning(
            f"Possible fraud: X-Userinfo header was set to {userinfo_header}"
        )


def get_session_data_headers():
    headers = {}
    session_data = get_session_data_or_none()
    if session_data:
        access_token = session_data.get("access_token")
        headers["Authorization"] = f"Bearer {access_token}"

        id_token = session_data.get("id_token")
        id_token_data = get_client().token_decoder.decode_token(
            id_token, audience=settings.OAUTH_CLIENT_ID
        )
        headers["X-Userinfo"] = base64.b64encode(json.dumps(id_token_data).encode())
        _logger.debug("Added Authorization header")
    else:
        _logger.debug("No session_data found.")
    return headers
