from fastapi import APIRouter
from app.websocket.event_dispatcher import dispatch_event

router = APIRouter()


@router.post("/execution-log")
def receive_log(payload: dict):

    dispatch_event({
        "type": "execution_log",
        "data": payload
    })

    return {"status": "ok"}
