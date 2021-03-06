import os

# Required
try:
    OAUTH_CLIENT_ID = os.environ["OAUTH_CLIENT_ID"]
    OAUTH_CLIENT_SECRET = os.environ["OAUTH_CLIENT_SECRET"]
    OAUTH_CALLBACK_URL = os.environ["OAUTH_CALLBACK_URL"]
    OAUTH_DOMAIN = os.environ["OAUTH_DOMAIN"]
    SECRET_KEY = os.environ["SECRET_KEY"]
    REDIRECT_LOGIN_URL = os.environ["REDIRECT_LOGIN_URL"]
    REDIRECT_LOGOUT_URL = os.environ["REDIRECT_LOGOUT_URL"]
except KeyError as exc:
    raise Exception(f"Mandatory parameter {exc} not set.")

# Optional
OAUTH_JWKS_URL = os.environ.get("OAUTH_JWKS_URL", None)
OAUTH_SIGNING_ALGORITHM = os.environ.get("OAUTH_SIGNING_ALGORITHM", "RS256")
REDIRECT_LOGGED_IN_URL = os.environ.get("REDIRECT_LOGGED_IN_URL", None)
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
PORT = int(os.environ.get("PORT", 8080))
HOST = os.environ.get("HOST", "127.0.0.1")
DEBUG = os.environ.get("DEBUG", False)
MOCK_OAUTH = os.environ.get("MOCK_OAUTH", False)
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", None)
AUTH0_MANAGEMENT_CLIENT_ID = os.environ.get("AUTH0_MANAGEMENT_CLIENT_ID", None)
AUTH0_MANAGEMENT_CLIENT_SECRET = os.environ.get("AUTH0_MANAGEMENT_CLIENT_SECRET", None)

# Computed
OAUTH_BASE_URL = "https://" + OAUTH_DOMAIN
OAUTH_AUDIENCE = os.environ.get("OAUTH_AUDIENCE", OAUTH_BASE_URL + "/userinfo")

# Constants
SESSION_ID = "session_id"
OAUTH_CLIENT_NAME = "oauth_client"
