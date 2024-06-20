import asyncio
import json
from typing import Dict, List

from fastapi import WebSocket
from common.util import DateTimeEncoder

class ConnectionManager:
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, ws_token: str):
        await websocket.accept()
        if ws_token in self.active_connections:
             self.active_connections.get(ws_token).append(websocket)
        else:
            self.active_connections.update({ws_token: [websocket]})


    def disconnect(self, websocket: WebSocket, ws_token: str):
        self.active_connections.get(ws_token).remove(websocket)
        if(len(self.active_connections.get(ws_token))==0):
            self.active_connections.pop(ws_token)

    # notice: changed from async to sync as background tasks messes up with async functions
    async def send_message(self, data: dict,ws_token: str):
        sockets = self.active_connections.get(ws_token)
        print(f"Sending message: {data}")
        if sockets:
            #notice: socket send is originally async. We have to change it to syncronous code - 
            for socket in sockets:
                msg = json.dumps(data, cls=DateTimeEncoder)
                await socket.send_text(msg)

socket_connections = ConnectionManager()