import asyncio
from datetime import datetime
import json
import traceback
from typing import List

import websockets

import actions
from conf import BIND_HOST, BIND_PORT
from lib import db
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
            await self.remove_conn(conn)

    async def remove_conn(self, connection: Connection):
        if connection in self.client_list:
            if connection.user:
                connection.user.last_seen = datetime.now()
                db.users.update(connection.user._id, connection.user)
                chats = db.chats.get_user_chats(str(connection.user._id))
                for chat in chats:
                    user_to_notify = None
                    if chat.user1 == str(connection.user._id):
                        user_to_notify = chat.user2
                    elif chat.user2 == str(connection.user._id):
                        user_to_notify = chat.user1

                    if user_to_notify:
                        connections = [connection for connection in self.client_list if connection.user and str(connection.user._id) == user_to_notify]
                        for conn in connections:
                            data = {"action": "status_change", "success": True, "data": {"user_id": str(connection.user._id), "status": "offline", "last_seen": datetime.now().timestamp()}}
                            await self.send_message(conn, data)

            self.client_list.remove(connection)

    async def send_message(self, conn, body: dict):
        online_user_conns = None

        if body.get('action', '') == "new_message":
            chat = body.get("data", {}).get('chat')
            if chat:
                if chat:
                    user = chat.get("user")
                    online_user_conns = [connection for connection in self.client_list if connection.user and str(connection.user._id) == user.get("id")]
                    print("Found online", online_user_conns)

            if online_user_conns:
                body_changed = body.copy()
                body_changed.get("data", {}).get("message", {})["is_mine"] = False
                print("[SENT TO ONLINE USER]", body_changed)
                print("--" * 30)
                data = json.dumps(body_changed)
                for _conn in online_user_conns:
                    if _conn.is_open:
                        await _conn.send(data)

        elif body.get('action', '') == "get_chats":
            for chat in body.get("data", {}).get("results", []):
                print("[[[chat finddd]]]", chat)
                if chat and chat.get("user", {}).get("id"):
                    print( "[[[user ifddd]]]", chat["user"]["id"])
                    print("[[[online]]]]", [connection for connection in self.client_list if connection.user and str(connection.user._id) == chat["user"]["id"]])
                    chat["user"]["is_online"] = any([connection for connection in self.client_list if connection.user and str(connection.user._id) == chat["user"]["id"]])
                    print(chat["user"]["is_online"], end="\n"*4)

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
                        print("notifying user: ", user_to_notify)
                        connections = [connection for connection in self.client_list if connection.user and str(connection.user._id) == user_to_notify]
                        print(connections)
                        for connection in connections:
                            data = {"action": "status_change", "status": True, "data": {"user_id": user_id, "status": "online", "last_seen": datetime.now().timestamp()}}
                            try:
                                await self.send_message(connection, data)
                            except Exception as e:
                                print(e)


        print("[SENT]", body)
        print("--" * 30)

        data = json.dumps(body)
        await conn.send(data)


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
