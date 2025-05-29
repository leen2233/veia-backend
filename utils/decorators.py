from functools import wraps

from lib.connection import Connection
from utils.exceptions import UnauthorizedException


def protected(func):
    @wraps(func)
    def wrapper(data, conn: Connection, *args, **kwargs):
        if not conn.is_authenticated:
            raise UnauthorizedException()
        return func(data, conn, *args, **kwargs)

    return wrapper
