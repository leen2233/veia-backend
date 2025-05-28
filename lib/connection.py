import socket
from typing import Optional

from lib.db import User


class Connection:
    def __init__(self, socket: socket.socket, addr) -> None:
        self.socket = socket
        self.addr = addr
        self.user: Optional[User] = None

    @property
    def is_authenticated(self) -> bool:
        if self.user:
            return True
        return False

    def authenticate(self, user: User):
        self.user = user

    def send(self, data):
        self.socket.send(data)

    def recv(self, *args, **kwargs):
        return self.socket.recv(*args, **kwargs)

    def close(self):
        return self.socket.close()
