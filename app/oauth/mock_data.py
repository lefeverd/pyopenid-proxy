import math
import time

from app.oauth.utils import create_token
from app import settings

# Private RSA 256 key
# Generated using openssl genrsa -out test.rsa 1024
RS256_PRIVATE = """-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQC/wUW1WukKX6P9SFsklQkmHynWSLgq5CSLr0lQSOQaPtL/4ges
nZk0c2hI7mk+qwGYORjyzVP0uDGGtPg1MiBTSJpNIvxbtQXu/WzYNKlNHnqBRvuT
rC/hOpMnrgrsE7DoaBF5HAvNsjipBPLvR5EMqQvrhB9Bpl3kDeaLFIVYxQIDAQAB
AoGAf/JlIfJMBtj0Ih+yeQFcvmwSzWFuSWg7Hl1SbNiGIyECRyy5dCsgO8g5sFgs
L12JTdnjVLc+qs5wdXKxH0WYHPIh9CYf7LEcFcuXl85ChhyjJiCTUTNKNFspKub0
BE/2+qN6MqBoVr6kV1Q7e1NpHpAN3pjru/ltmgPFl2XzWS0CQQDnh/D1R8SyqyuE
j14ffi969YLJSJg4Qev39IPBjRevhOX5LKO/gZYHwu7uei5evzH0WW4ROz5j4izs
EFJ5/dInAkEA1AUxNrzzaAzBosL777kINJeErvi/nnVMZIA+qA5Sid2bI2kIgySZ
QxFSLvMKGwpoCzDqE058AJ6lH1JgdkONMwJBAJMlV2NbiEwQ8yhdQXF8bcqUi9lG
1M80Pjao5K+27u2y5cGVuD/2qJYoMlfHuP6oPqRPzd8PqtgqH2ir+u7i/JMCQHw2
aoWyHzwXNR5g826XTZpaJm7H5qMz/0Rl6c9VTL/eZ7RQJZ+HQo8LR8Wft4zuBNSB
nLEg6v8F8qEuBrtiigcCQEIKuC7vZHPbXrA07k2KpBTbZZ78HCzHMQcZEPb25Szl
kr9Vy60eO+WrxzgUuEt8wE2Z6eHhlmY7YP/4pw7BngQ=
-----END RSA PRIVATE KEY-----"""

# Public key
# Generated using openssl rsa -in test.rsa -pubout > test.pem
RS256_PUBLIC = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC/wUW1WukKX6P9SFsklQkmHynW
SLgq5CSLr0lQSOQaPtL/4gesnZk0c2hI7mk+qwGYORjyzVP0uDGGtPg1MiBTSJpN
IvxbtQXu/WzYNKlNHnqBRvuTrC/hOpMnrgrsE7DoaBF5HAvNsjipBPLvR5EMqQvr
hB9Bpl3kDeaLFIVYxQIDAQAB
-----END PUBLIC KEY-----"""

# The tokens data is based on auth0 tokens.
TOKEN_HEADER = {"typ": "JWT", "alg": "RS256", "kid": "1234"}


_now = math.floor(time.time())
_expiration_epoch = _now + 24 * 3600

ACCESS_TOKEN_DATA = {
    "iss": f"{settings.OAUTH_BASE_URL}/",
    "sub": "idp|123456789",
    "aud": ["https://127.0.0.1:8080", f"{settings.OAUTH_BASE_URL}/userinfo"],
    "iat": _now,
    "exp": _expiration_epoch,
    "azp": settings.OAUTH_CLIENT_ID,  # Authorized party, token to which the token was issued
    "scope": "openid profile",
}

ID_TOKEN_DATA = {
    "nickname": "name.lastname",
    "name": "name.lastname@mailprovider.com",
    "picture": "https://s.gravatar.com/avatar/bc6873f57cb217f19092eed1ba32b6ca?s=480&r=pg&d=https%3A%2F%2Fcdn.auth0.com%2Favatars%2Fle.png",
    "updated_at": "2018-11-11T17:57:10.507Z",
    "iss": f"{settings.OAUTH_BASE_URL}/",
    "sub": "idp|123456789",
    "aud": settings.OAUTH_CLIENT_ID,
    "iat": _now,
    "exp": _expiration_epoch,
}


ACCESS_TOKEN = create_token(ACCESS_TOKEN_DATA, RS256_PRIVATE)
ID_TOKEN = create_token(ID_TOKEN_DATA, RS256_PRIVATE)
