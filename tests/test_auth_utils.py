import math
import time
import pytest

from jose import jwt, jwk

from app.auth_utils import decode_token
from app.errors import AppError
from app import settings
from tests.tokens_data import RS256_PRIVATE, RS256_PUBLIC


def create_token(payload, key, headers=None):
    """
    Create a token based on the private RS256 test key.
    It can be decoded using decode_token method from auth_utils.
    """
    token = jwt.encode(payload, key, settings.OAUTH_SIGNING_ALGORITHM, headers=headers)
    return token


class TestOAuth:
    def test_decode_token(self, monkeypatch):
        now = math.floor(time.time())
        expiration_epoch = now + 24 * 3600
        token_data = {
            "iss": "https://simplebookmarks.fakeidp.com/",
            "sub": "auth0|123456789",
            "aud": [
                "http://127.0.0.1:3000",
                "https://simplebookmarks.fakeidp.com/userinfo",
            ],
            "iat": now,
            "exp": expiration_epoch,
            "azp": "2TvmetzbRpLI25A1RYvceTMAMerxIjzv",
            "scope": "openid profile",
        }
        token = create_token(token_data, RS256_PRIVATE)

        monkeypatch.setattr(
            "app.auth_utils.get_key_from_jwks", lambda *args, **kwargs: RS256_PUBLIC
        )
        decode_token(token, "http://127.0.0.1:3000")
        assert True

    def test_decode_token_bad_audience(self, monkeypatch):
        now = math.floor(time.time())
        expiration_epoch = now + 24 * 3600
        token_data = {
            "iss": "https://simplebookmarks.fakeidp.com/",
            "sub": "auth0|123456789",
            "aud": [
                "http://127.0.0.1:3000",
                "https://simplebookmarks.fakeidp.com/userinfo",
            ],
            "iat": now,
            "exp": expiration_epoch,
            "azp": "2TvmetzbRpLI25A1RYvceTMAMerxIjzv",
            "scope": "openid profile",
        }
        token = create_token(token_data, RS256_PRIVATE)

        monkeypatch.setattr(
            "app.auth_utils.get_key_from_jwks", lambda *args, **kwargs: RS256_PUBLIC
        )

        with pytest.raises(AppError) as exc:
            decode_token(token, "bad_audience")

        assert exc.value.status == 401
        assert exc.value.code == 2

    def test_decode_token_bad_exp(self, monkeypatch):
        now = math.floor(time.time())
        token_data = {
            "iss": "https://simplebookmarks.fakeidp.com/",
            "sub": "auth0|123456789",
            "aud": [
                "http://127.0.0.1:3000",
                "https://simplebookmarks.fakeidp.com/userinfo",
            ],
            "iat": now - 48 * 3600,
            "exp": now - 24 * 3600,
            "azp": "2TvmetzbRpLI25A1RYvceTMAMerxIjzv",
            "scope": "openid profile",
        }
        token = create_token(token_data, RS256_PRIVATE)

        monkeypatch.setattr(
            "app.auth_utils.get_key_from_jwks", lambda *args, **kwargs: RS256_PUBLIC
        )

        with pytest.raises(AppError) as exc:
            decode_token(token, "http://127.0.0.1:3000")

        assert exc.value.status == 401
        assert exc.value.code == 1

    def test_decode_token_bad_signature(self, monkeypatch):
        bad_public_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC/wUW1WukKX6P9SFsklQkmHynW
SLgq5CSLr0lQSOQaPtL/4gesnZk0c2hI7mk+qwGYORjyzVP0uDGGtPg1MiBTSJpN
IvxbtQXu/WzYNKlNHnqBRvuTrC/hOpMnrgrsE7DoaBF5HAvNsjipBPLvR5EMqQvr
hB9Bpl3kDeaLFIVYxQIDFAKE
-----END PUBLIC KEY-----"""
        now = math.floor(time.time())
        expiration_epoch = now + 24 * 3600
        token_data = {
            "iss": "https://simplebookmarks.fakeidp.com/",
            "sub": "auth0|123456789",
            "aud": [
                "http://127.0.0.1:3000",
                "https://simplebookmarks.fakeidp.com/userinfo",
            ],
            "iat": now,
            "exp": expiration_epoch,
            "azp": "2TvmetzbRpLI25A1RYvceTMAMerxIjzv",
            "scope": "openid profile",
        }
        token = create_token(token_data, RS256_PRIVATE)

        monkeypatch.setattr(
            "app.auth_utils.get_key_from_jwks", lambda *args, **kwargs: bad_public_key
        )
        with pytest.raises(AppError) as exc:
            decode_token(token, "http://127.0.0.1:3000")

        assert exc.value.status == 401
        assert exc.value.code == 3

    def test_decode_token_jwks(self, monkeypatch):
        now = math.floor(time.time())
        expiration_epoch = now + 24 * 3600
        token_data = {
            "iss": "https://simplebookmarks.fakeidp.com/",
            "sub": "auth0|123456789",
            "aud": [
                "http://127.0.0.1:3000",
                "https://simplebookmarks.fakeidp.com/userinfo",
            ],
            "iat": now,
            "exp": expiration_epoch,
            "azp": "2TvmetzbRpLI25A1RYvceTMAMerxIjzv",
            "scope": "openid profile",
        }

        # Create a token with the private RSA256 key
        token = create_token(token_data, RS256_PRIVATE)

        # Create a JWK from the public RSA256 key
        public_jwk = jwk.construct(RS256_PUBLIC, "RS256").to_dict()

        monkeypatch.setattr(
            "app.auth_utils.get_key_from_jwks", lambda *args, **kwargs: public_jwk
        )
        decode_token(token, "http://127.0.0.1:3000")
        assert True
