import os
import select
import socket
import sys

from dotenv import load_dotenv

load_dotenv()


HOST = os.getenv("BIND_HOST")
PORT = int(os.getenv("BIND_PORT", "9090"))


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.connect((HOST, PORT))


def format_message(text: str):
    return text.encode()


while True:
    # maintains a list of possible input streams
    sockets_list = [sys.stdin, server]

    read_sockets, write_socket, error_socket = select.select(sockets_list, [], [])

    for socks in read_sockets:
        if socks == server:
            message = socks.recv(2048)
            print(message.decode("utf-8"))
        else:
            message = sys.stdin.readline()
            server.send(format_message(message))
            sys.stdout.write("<You>")
            sys.stdout.write(message)
            sys.stdout.flush()
server.close()
