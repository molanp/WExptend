import asyncio
from server import WebSocketServer

if __name__ == '__main__':
    server = WebSocketServer()
    asyncio.get_event_loop().run_until_complete(server.run())
