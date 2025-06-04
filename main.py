import asyncio
import json
import traceback
from typing import List

import websockets

import actions
from conf import BIND_HOST, BIND_PORT
from lib.connection import Connection


def format_message(text: str):
    return text.encode()


class Server:
    def __init__(self, host, port):
        self.client_list: List[Connection] = []
        self.host = host
        self.port = port

    async def handler(self, websocket):
        conn = Connection(websocket, websocket.remote_address)
        self.client_list.append(conn)
        print("client connected")
        try:
            async for message in websocket:
                await self.on_message(message, conn)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.remove_conn(websocket)

    def remove_conn(self, connection):
        if connection in self.client_list:
            self.client_list.remove(connection)

    async def send_message(self, conn, body: dict):
        print("[SENT]", body)
        print("--" * 30)
        online_user_conns = None

        if body.get('action', '') == "new_message":
            chat = body.get("data", {}).get('chat')
            if chat:
                body.get("data", {}).pop("chat")
                print("trying to get online user", chat)
                if chat:
                    user = chat.get("user")
                    online_user_conns = [connection for connection in self.client_list if connection.user and str(connection.user._id) == user.get("id")]
                    print("Found online", online_user_conns)

        data = json.dumps(body)
        await conn.send(data)

        if online_user_conns:
            body.get("data", {}).get("message", {})["is_mine"] = False
            print("[SENT]", body)
            print("--" * 30)
            data = json.dumps(body)
            for _conn in online_user_conns:
                if _conn.is_open:
                    await _conn.send(data)


    async def on_message(self, message: str, conn: Connection):
        print("[RECV]", message, "\n")
        try:
            data = json.loads(message)
            if data.get("action"):
                action = data.get("action")
                if hasattr(actions, action):
                    func = getattr(actions, action)
                    data = data.get("data")
                    response = func(data, conn)
                    body = {"action": action, "success": response.status, "data": response.data}
                    await self.send_message(conn, body)
                else:
                    print("[Aciton not found]", action)
        except json.JSONDecodeError:
            print("invalid json")
        except Exception:
            traceback.print_exc()

    async def start(self):
        print(f"Listening at {self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()


if __name__ == "__main__":
    server = Server(BIND_HOST, BIND_PORT)
    asyncio.run(server.start())
