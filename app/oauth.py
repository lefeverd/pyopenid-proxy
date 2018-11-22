from authlib.flask.client import OAuth
from app import settings

oauth = OAuth()
auth0 = oauth.register(
    "auth0",
    client_id=settings.OAUTH_CLIENT_ID,
    client_secret=settings.OAUTH_CLIENT_SECRET,
    api_base_url=settings.OAUTH_BASE_URL,
    access_token_url=settings.OAUTH_BASE_URL + "/oauth/token",
    authorize_url=settings.OAUTH_BASE_URL + "/authorize",
    client_kwargs={"scope": "openid profile"},
)
