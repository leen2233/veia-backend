import json
import socket
from _thread import start_new_thread

from actions import ACTIONS
from conf import BIND_HOST, BIND_PORT
from lib.connection import Connection


def format_message(text: str):
    return text.encode()


class Server:
    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen()
        self.client_list = []

    def clientthread(self, conn: Connection):
        while True:
            try:
                message = conn.recv(2048)
                message = self._decode(message)
                if message:
                    self.on_message(message, conn)
                else:
                    self.remove_conn(conn)

            except:
                continue

    def broadcast(self, message, connection):
        for client in self.client_list:
            print(client, "sending")
            if client != connection:
                try:
                    client.send(format_message(message))
                except Exception as e:
                    print("error sending message", e)
                    client.close()
                    self.remove_conn(client)

    def remove_conn(self, connection):
        if connection in self.client_list:
            self.client_list.remove(connection)

    def send_message(self, conn, body: dict):
        print("sending message", body)
        data = json.dumps(body)
        data = self._encode(data)
        conn.send(data)

    def on_message(self, message: str, conn: Connection):
        try:
            data = json.loads(message)
            if data.get("action"):
                action = data.get("action")
                if ACTIONS.get(action):
                    func = ACTIONS[action]
                    data = data.get("data")
                    response = func(data, conn)
                    print(conn.user, "user")
                    body = {"action": action, "success": response.status, "data": response.data}
                    self.send_message(conn, body)
                else:
                    print("[Aciton not found]", action)
        except json.JSONDecodeError:
            print("invalid json")
        except Exception:
            import traceback

            traceback.print_exc()

    def start(self):
        while True:
            conn, addr = self.server.accept()
            conn = Connection(conn, addr)
            self.client_list.append(conn)
            print("client connected")
            start_new_thread(self.clientthread, (conn,))

    def close(self):
        self.server.close()

    def _encode(self, text: str):
        return text.encode()

    def _decode(self, text: bytes):
        return text.decode()


if __name__ == "__main__":
    server = Server(BIND_HOST, BIND_PORT)
    server.start()
