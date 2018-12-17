import logging

from authlib.flask.client import OAuth

from app import settings
from .clients import Auth0Client, MockClient

_logger = logging.getLogger(__name__)
oauth_registry = OAuth()


def init_app(app):
    global oauth_registry
    # Reinitialize the Oauth registry.
    # In tests for instance, the app module is imported once, thus the registry
    # kept its _clients and _registry values.
    oauth_registry = OAuth()
    oauth_registry.init_app(app)
    if settings.MOCK_OAUTH:
        _logger.info("MOCK_OAUTH set, using Mock oauth client.")
        oauth_registry.register(settings.OAUTH_CLIENT_NAME, client_cls=MockClient)
    else:
        if not settings.OAUTH_JWKS_URL:
            raise Exception("Please set OAUTH_JWKS_URL.")
        oauth_registry.register(
            settings.OAUTH_CLIENT_NAME,
            client_id=settings.OAUTH_CLIENT_ID,
            client_secret=settings.OAUTH_CLIENT_SECRET,
            api_base_url=settings.OAUTH_BASE_URL,
            access_token_url=settings.OAUTH_BASE_URL + "/oauth/token",
            authorize_url=settings.OAUTH_BASE_URL + "/authorize",
            client_kwargs={"scope": "openid profile"},
            client_cls=Auth0Client,
        )


def get_client():
    # create_client will try to get from its cache first,
    # otherwise create a new client based on the registered values.
    return oauth_registry.create_client(settings.OAUTH_CLIENT_NAME)
