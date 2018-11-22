from flask import jsonify
from werkzeug.exceptions import HTTPException

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

ERROR_UNKNOWN = {"status": 500, "code": 500, "title": "Unknown Error"}


ERROR_TOKEN_EXPIRED = {"status": 401, "code": 1, "title": "Token has expired."}

ERROR_TOKEN_CLAIMS = {
    "status": 401,
    "code": 2,
    "title": "Invalid claims. Please verify the audience and issuer.",
}

ERROR_TOKEN_SIGNATURE = {"status": 401, "code": 3, "title": "Invalid token signature."}

ERROR_JWKS_KEY_NOT_FOUND = {
    "status": 401,
    "code": 4,
    "title": "No key could be found in JWKS corresponding to the token's kid.",
}


def init_app(app):
    app.register_error_handler(AppError, AppError.handle)


class AppError(HTTPException):
    def __init__(self, error=ERROR_UNKNOWN, description=None):
        self.error = error
        self.error["description"] = description

    @property
    def code(self):
        return self.error["code"]

    @property
    def title(self):
        return self.error["title"]

    @property
    def status(self):
        return self.error["status"]

    @property
    def description(self):
        return self.error["description"]

    def to_dict(self):
        meta = OrderedDict()
        meta["code"] = self.code
        meta["message"] = self.title
        if self.description:
            meta["description"] = self.description
        return meta

    @staticmethod
    def handle(exception):
        """
        This method is called by flask when an AppError is encountered,
        via `register_error_handler`.
        """
        return jsonify({"error": exception.to_dict()}), exception.status


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code
