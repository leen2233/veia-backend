from typing import Optional

from websockets import WebSocketServerProtocol

from lib.db import User


class Connection:
    def __init__(self, websocket: WebSocketServerProtocol, addr) -> None:
        self.websocket = websocket
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
