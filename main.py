import asyncio
import json
import traceback
from datetime import datetime
from typing import List, Optional

import websockets

import actions
from conf import BIND_HOST, BIND_PORT
from lib import db
from lib.connection import Connection
from utils.server_holder import use_server


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
            await self.remove_conn(conn)

    async def remove_conn(self, connection: Connection):
        if connection in self.client_list:
            if connection.user:
                connection.user.last_seen = datetime.now()
                db.users.update(connection.user._id, connection.user)
                chats = db.chats.get_user_chats(str(connection.user._id))
                for chat in chats:
                    user_to_notify = None
                    if chat.user1 == str(connection.user._id): # type: ignore
                        user_to_notify = chat.user2
                    elif chat.user2 == str(connection.user._id): # type: ignore
                        user_to_notify = chat.user1

                    if user_to_notify:
                        connections = [connection for connection in self.client_list if connection.user and str(connection.user._id) == user_to_notify]
                        for conn in connections:
                            data = {"action": "status_change", "success": True, "data": {"user_id": str(connection.user._id), "status": "offline", "last_seen": datetime.now().timestamp()}} # type: ignore
                            await self.send_message(conn, data)

            self.client_list.remove(connection)

    async def send_message(self, conn, body: dict, additional_data: Optional[dict] = {}):
        print("[BODY::: ]", body)
        if body.get('action', '') == "get_chats":
            for chat in body.get("data", {}).get("results", []):
                if chat and chat.get("user", {}).get("id"):
                    online_users = await self.find_online_user(chat["user"]["id"])
                    chat["user"]["is_online"] = any(online_users)

        elif body.get('action', '') == "authenticate" and body.get("success"):
            user_id = body.get("data", {}).get("user", {}).get("id", "")
            if user_id:
                chats = db.chats.get_user_chats(user_id)
                for chat in chats:
                    user_to_notify = None
                    if chat.user1 == user_id:
                        user_to_notify = chat.user2
                    elif chat.user2 == user_id:
                        user_to_notify = chat.user1

                    if user_to_notify:
                        connections = await self.find_online_user(user_to_notify)
                        for connection in connections:
                            data = {
                                "action": "status_change",
                                "status": True,
                                "data": {
                                    "user_id": user_id,
                                    "status": "online",
                                    "last_seen": datetime.now().timestamp()
                                }
                            }
                            data = json.dumps(data)
                            try:
                                if connection.is_open:
                                    await connection.send(data)
                            except Exception as e:
                                print(e)

        elif body.get("action", '') == "delete_message" or body.get('action', '') == "edit_message": # because responses nearly same
            if additional_data:
                other_user = additional_data.get("chat", {}).get("user")
                if other_user:
                    connections = await self.find_online_user(other_user)
                    data = json.dumps(body)
                    for connection in connections:
                        await connection.send(data)

        elif body.get('action', '') == "read_message":
            if additional_data:
                users_to_notify = additional_data.get("users_to_notify", [])
                for user_to_notify in users_to_notify:
                    connections = await self.find_online_user(user_to_notify)
                    data = json.dumps(body)
                    for connection in connections:
                        await connection.send(data)


        print("[SENT]", body)
        print("--" * 30)

        data = json.dumps(body)
        await conn.send(data)

    async def find_online_user(self, id: str) -> List[Connection]:
        return [connection for connection in self.client_list if connection.is_open and connection.user and str(connection.user._id) == id]

    async def handle_update(self, update: db.Update):
        for user in update.users:
            online_user_conns = await self.find_online_user(user)
            if online_user_conns:
                data = {"action": update.type, "success": True, "data": update.body}
                data = json.dumps(data)
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
                    response: actions.Response = func(data, conn)
                    if response.send_now:
                        body = {"action": action, "success": response.status, "data": response.data}
                        await self.send_message(conn, body, response.additional_data)
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
    use_server(server)
    asyncio.run(server.start())
