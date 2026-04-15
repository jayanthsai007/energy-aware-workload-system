from fastapi import APIRouter
from app.websocket.connection_manager import manager
import asyncio

router = APIRouter()


@router.get("/test-execute/{node_id}")
def test_execute(node_id: str):
    asyncio.run(manager.send_to_node(node_id, {
        "type": "execute",
        "script": "for i in range(3): print('Hello from WS', i)",
        "language": "python"
    }))
    return {"status": "sent"}
