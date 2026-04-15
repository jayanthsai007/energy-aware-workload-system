from fastapi import WebSocket
from typing import Dict, List
import asyncio


class ConnectionManager:
    def __init__(self):
        # Dashboard / frontend clients
        self.active_connections: List[WebSocket] = []

        # Node-specific connections
        self.node_connections: Dict[str, WebSocket] = {}
        self.ws_node_map: Dict[WebSocket, str] = {}

        # 🔥 Lock for thread safety
        self.lock = asyncio.Lock()

    # =========================
    # CONNECT
    # =========================
    async def connect(self, websocket: WebSocket):
        await websocket.accept()

        async with self.lock:
            self.active_connections.append(websocket)

        print(f"[WS] Client connected. Total: {len(self.active_connections)}")

    # =========================
    # DISCONNECT
    # =========================
    async def disconnect(self, websocket: WebSocket):
        await self._cleanup_connection(websocket)

        print(
            f"[WS] Client disconnected. Total: {len(self.active_connections)}")

        try:
            await websocket.close(code=1000)
        except Exception:
            pass

    async def _cleanup_connection(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

            node_id = self.ws_node_map.pop(websocket, None)
            if node_id and self.node_connections.get(node_id) == websocket:
                del self.node_connections[node_id]
                print(f"[WS] Node cleanup removed: {node_id}")

    # =========================
    # BROADCAST
    # =========================
    async def broadcast(self, message: dict):
        dead_connections = []

        async with self.lock:
            connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print("[WS BROADCAST ERROR]", e)
                dead_connections.append(connection)

        # Cleanup dead connections
        for conn in dead_connections:
            await self.disconnect(conn)

    # =========================
    # REGISTER NODE
    # =========================
    async def register_node(self, node_id: str, websocket: WebSocket):
        # If this node reconnects, remove the old socket first
        old_ws = None
        async with self.lock:
            old_ws = self.node_connections.get(node_id)

        if old_ws and old_ws is not websocket:
            print(
                f"[WS] Duplicate node register: disconnecting stale socket for {node_id}")
            await self._cleanup_connection(old_ws)
            try:
                await old_ws.close(code=1000)
            except Exception:
                pass

        async with self.lock:
            # Clean up an old node mapping for this websocket if it exists
            previous_node = self.ws_node_map.get(websocket)
            if previous_node and previous_node != node_id:
                self.node_connections.pop(previous_node, None)
                self.ws_node_map.pop(websocket, None)

            self.node_connections[node_id] = websocket
            self.ws_node_map[websocket] = node_id

        print(f"[WS] Node registered: {node_id}")

    # =========================
    # SEND TO NODE
    # =========================
    async def send_to_node(self, node_id: str, message: dict) -> bool:
        async with self.lock:
            ws = self.node_connections.get(node_id)

        if not ws:
            print(f"[WS ERROR] Node {node_id} not connected")
            return False

        try:
            await ws.send_json(message)
            print(f"[WS] Sent task to node {node_id}")
            return True

        except Exception as e:
            print(f"[WS ERROR] Failed to send to {node_id}: {e}")

            # 🔥 Remove broken connection safely
            await self.disconnect(ws)

            return False

    # =========================
    # CHECK NODE STATUS
    # =========================
    async def is_node_connected(self, node_id: str) -> bool:
        async with self.lock:
            return node_id in self.node_connections

    # =========================
    # GET ALL CONNECTED NODES
    # =========================
    async def get_connected_nodes(self) -> List[str]:
        async with self.lock:
            return list(self.node_connections.keys())


# 🔥 Global instance
manager = ConnectionManager()
