from fastapi import WebSocket

class ConnectionManager:

    def __init__(self):
        self.connections = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[job_id] = websocket

    def disconnect(self, job_id: str):
        self.connections.pop(job_id, None)

    async def send(self, job_id: str, message: dict):
        ws = self.connections.get(job_id)

        if ws:
            await ws.send_json(message)

manager = ConnectionManager()