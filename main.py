import os
import socket
from _thread import *

from dotenv import load_dotenv

load_dotenv()

BIND_HOST = os.getenv("BIND_HOST", "127.0.0.1")
BIND_PORT = int(os.getenv("BIND_PORT", "9090"))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


server.bind((BIND_HOST, BIND_PORT))

server.listen()

clients_list = []


def format_message(text: str):
    return text.encode()


def clientthread(conn, addr):
    conn.send(format_message("Weolcome you fool"))
    while True:
        try:
            message = conn.recv(2048)
            print("Message received", message)
            message = message.decode()
            if message:
                print("<" + addr[0] + "> " + message)
                message_to_send = "<" + addr[0] + "> " + message
                broadcast(message_to_send, conn)

            else:
                """message may have no content if the connection
                    is broken, in this case we remove the connection"""
                remove(conn)

        except:
            continue


def broadcast(message, connection):
    print("client_list", clients_list)
    for client in clients_list:
        print(client, "sending")
        if client != connection:
            try:
                client.send(format_message(message))
            except Exception as e:
                print("error sending message", e)
                client.close()
                remove(client)


def remove(connection):
    if connection in clients_list:
        clients_list.remove(connection)


while True:
    """Accepts a connection request and stores two parameters,
    conn which is a socket object for that user, and addr
    which contains the IP address of the client that just
    connected"""
    conn, addr = server.accept()

    """Maintains a list of clients for ease of broadcasting
    a message to all available people in the chatroom"""
    clients_list.append(conn)

    # prints the address of the user that just connected
    print(addr[0] + " connected")

    # creates and individual thread for every user
    # that connects
    start_new_thread(clientthread, (conn, addr))

conn.close()
server.close()
