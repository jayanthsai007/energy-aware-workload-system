import asyncio
from app.websocket.connection_manager import manager

# 🔥 Store main event loop
main_loop = None


def set_main_loop(loop):
    global main_loop
    main_loop = loop


def dispatch_event(event: dict):
    global main_loop

    try:
        # ✅ Case 1: inside async loop
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(event))

    except RuntimeError:
        # ❌ No running loop → use main loop
        if main_loop:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast(event),
                main_loop
            )
        else:
            print("❌ No event loop available for dispatch")
