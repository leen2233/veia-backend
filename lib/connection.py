from typing import Optional

from websockets import ServerConnection
from websockets.protocol import State

from lib.db import User


class Connection:
    def __init__(self, websocket: ServerConnection, addr) -> None:
        self.websocket: ServerConnection = websocket
        self.addr = addr
        self.user: Optional[User] = None

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    def authenticate(self, user: User):
        self.user = user

    async def send(self, data):
        await self.websocket.send(data)

    async def recv(self):
        return await self.websocket.recv()

    async def close(self):
        await self.websocket.close()

    @property
    def is_open(self) -> bool:
        return self.websocket.state == State.OPEN

    def __repr__(self) -> str:
        return f"<Connection user={self.user}>"
