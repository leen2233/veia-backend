from functools import wraps

from lib.connection import Connection
from utils.exceptions import UnauthorizedException


def protected(func):
    @wraps(func)
    def wrapper(data, conn: Connection, *args, **kwargs):
        print("conn.is_authenticated", conn.is_authenticated)
        print("conn.user", conn.user)
        if not conn.is_authenticated:
            raise UnauthorizedException()
        return func(data, conn, *args, **kwargs)

    return wrapper
