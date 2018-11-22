import abc
import logging

import redis
from werkzeug.contrib.cache import SimpleCache

from app import settings

_logger = logging.getLogger(__name__)


class SessionManager(abc.ABC):
    @abc.abstractmethod
    def create_session(self, session_id, payload: dict, expire_seconds=None):
        """
        Create a new session with the specified payload.
        """
        pass

    @abc.abstractmethod
    def destroy_session(self, session_id):
        pass

    @abc.abstractmethod
    def get(self, session_id):
        pass


class RedisSessionManager(SessionManager):
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
        )

    def create_session(self, session_id, payload: dict, expire_seconds=None):
        ret = self.redis.hmset(session_id, payload)
        if expire_seconds:
            self.redis.expire(session_id, expire_seconds)
        return ret

    def get(self, session_id):
        return self.redis.hgetall(session_id) or None

    def destroy_session(self, session_id):
        return self.redis.delete(session_id) and True or False


class LocalSessionManager(SessionManager):
    """
    Session manager that stores sessions in memory.
    Do not use it in a multi-threaded/multi-processes environment,
    and use RedisSessionManager instead.
    """

    def __init__(self):
        # The default timeout is 0, meaning no expiration.
        # When creating a session, the timeout of the key will be set accordingly
        # to the expiration time of the access token.
        self.sessions = SimpleCache(default_timeout=0)

    def create_session(self, session_id, payload: dict, expire_seconds=None):
        self.sessions.add(session_id, payload, timeout=expire_seconds)

    def get(self, session_id):
        return self.sessions.get(session_id)

    def destroy_session(self, session_id):
        return self.sessions.delete(session_id)


if settings.REDIS_HOST:
    session = RedisSessionManager()
else:
    session = LocalSessionManager()
