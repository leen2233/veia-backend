import asyncio

_server = None


def use_server(s):
    global _server
    _server = s

def handle_update(update):
    if _server:
        asyncio.create_task(_server.handle_update(update))
