import math
import time
import pytest

from jose import jwt, jwk
from unittest.mock import MagicMock

from app.errors import AppError
from app import settings
from app.oauth.mock_data import RS256_PRIVATE, RS256_PUBLIC
from app.oauth.token_decoders import SimpleTokenDecoder, JWKSTokenDecoder


def create_token(payload, key, headers=None):
    """
    Create a token based on the private RS256 test key.
    It can be decoded using decode_token method from auth_utils.
    """
    token = jwt.encode(payload, key, settings.OAUTH_SIGNING_ALGORITHM, headers=headers)
    return token


def get_token_data():
    now = math.floor(time.time())
    expiration_epoch = now + 24 * 3600
    token_data = {
        "iss": "https://simplebookmarks.fakeidp.com/",
        "sub": "auth0|123456789",
        "aud": [
            "https://127.0.0.1:8080",
            "https://simplebookmarks.fakeidp.com/userinfo",
        ],
        "iat": now,
        "exp": expiration_epoch,
        "azp": "2TvmetzbRpLI25A1RYvceTMAMerxIjzv",
        "scope": "openid profile",
    }
    return token_data


class TestTokenDecoders:
    def test_simple_token_decoder(self):
        token_decoder = SimpleTokenDecoder(RS256_PUBLIC)
        token = create_token(get_token_data(), RS256_PRIVATE)
        token_decoder.decode_token(token, audience="https://127.0.0.1:8080")
        assert True

    def test_decode_token_bad_audience(self, monkeypatch):
        token_decoder = SimpleTokenDecoder(RS256_PUBLIC)
        token = create_token(get_token_data(), RS256_PRIVATE)
        with pytest.raises(AppError) as exc:
            token_decoder.decode_token(token, audience="bad_audience")

        assert exc.value.status == 401
        assert exc.value.code == 2

    def test_decode_token_bad_exp(self, monkeypatch):
        now = math.floor(time.time())
        token_data = get_token_data()
        token_data.update({"iat": now - 48 * 3600, "exp": now - 24 * 3600})
        token = create_token(token_data, RS256_PRIVATE)
        token_decoder = SimpleTokenDecoder(RS256_PUBLIC)
        token = create_token(token_data, RS256_PRIVATE)

        with pytest.raises(AppError) as exc:
            token_decoder.decode_token(token, audience="https://127.0.0.1:8080")

        assert exc.value.status == 401
        assert exc.value.code == 1

    def test_decode_token_bad_signature(self, monkeypatch):
        bad_public_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC/wUW1WukKX6P9SFsklQkmHynW
SLgq5CSLr0lQSOQaPtL/4gesnZk0c2hI7mk+qwGYORjyzVP0uDGGtPg1MiBTSJpN
IvxbtQXu/WzYNKlNHnqBRvuTrC/hOpMnrgrsE7DoaBF5HAvNsjipBPLvR5EMqQvr
hB9Bpl3kDeaLFIVYxQIDFAKE
-----END PUBLIC KEY-----"""

        token_decoder = SimpleTokenDecoder(bad_public_key)
        token = create_token(get_token_data(), RS256_PRIVATE)

        with pytest.raises(AppError) as exc:
            token_decoder.decode_token(token, audience="https://127.0.0.1:8080")

        assert exc.value.status == 401
        assert exc.value.code == 3

    def test_decode_token_jwks(self, monkeypatch):
        # Create a token with the private RSA256 key
        token = create_token(get_token_data(), RS256_PRIVATE)

        # Create a JWK from the public RSA256 key
        public_jwk = jwk.construct(RS256_PUBLIC, "RS256").to_dict()

        token_decoder = JWKSTokenDecoder("https://fake-jwks-url")
        token_decoder.get_key_from_jwks = MagicMock(return_value=public_jwk)

        token_decoder.decode_token(token, audience="https://127.0.0.1:8080")
        assert True
