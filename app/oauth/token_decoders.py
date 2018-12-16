from jose import jwt
import requests

from app import settings
from app.errors import (
    AppError,
    ERROR_TOKEN_EXPIRED,
    ERROR_TOKEN_CLAIMS,
    ERROR_TOKEN_SIGNATURE,
    ERROR_JWKS_KEY_NOT_FOUND,
)


class TokenDecoder:
    def decode_token(self, token, key=None, audience=None):
        """
        Decode the specified token.
        The audience has to match the token's audience.
        """
        payload = None
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=[settings.OAUTH_SIGNING_ALGORITHM],
                audience=audience,
                issuer=settings.OAUTH_BASE_URL + "/",
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AppError(ERROR_TOKEN_EXPIRED)
        except jwt.JWTClaimsError:
            raise AppError(ERROR_TOKEN_CLAIMS)
        except jwt.JWTError:
            raise AppError(ERROR_TOKEN_SIGNATURE)


class SimpleTokenDecoder(TokenDecoder):
    def __init__(self, key):
        self.key = key

    def decode_token(self, token, **kwargs):
        """
        Decode the specified token.
        The audience has to match the token's audience.
        """
        return super().decode_token(token, self.key, **kwargs)


class JWKSTokenDecoder(TokenDecoder):
    jwks = None

    def __init__(self, jwks_url):
        self.jwks_url = jwks_url

    def get_jwks(self):
        if not self.jwks:
            resp = requests.get(self.jwks_url)
            self.jwks = resp.json()
        return self.jwks

    def get_key_from_jwks(self, token):
        """
        Iterate on the keys from the JWKS to find the one matching the token header's kid
        (key id).
        """
        jwks = self.get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                return rsa_key
        raise AppError(ERROR_JWKS_KEY_NOT_FOUND)

    def decode_token(self, token, **kwargs):
        key = self.get_key_from_jwks(token)
        return super().decode_token(token, key, **kwargs)
