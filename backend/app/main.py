from fastapi import FastAPI

# =========================
# ROUTES
# =========================
from app.api.routes_metrics import router as metrics_router
from app.api.routes_nodes import router as nodes_router
from app.api.routes_heartbeat import router as heartbeat_router
from app.api.routes_execution import router as execution_router
from app.api.routes_upload import router as upload_router
from app.api.routes_node_execution import router as node_execution_router
from app.api.routes_execute import router as execute_router
from app.api.routes_retrain import router as retrain_router
from app.api.routes_execution_metrics import router as execution_metrics_router
from app.api.routes_ws import router as ws_router
from app.api.routes_execution_log import router as log_router
from app.api.routes_ws_test import router as ws_test_router

# =========================
# DATABASE & MODELS
# =========================
from app.database import engine, Base, SessionLocal
from app.models.node_model import Node

# =========================
# SERVICES
# =========================
from app.services.retraining_service import retraining_worker
from app.services.scheduler import scheduler_loop

# =========================
# WEBSOCKET DISPATCH
# =========================
from app.websocket.event_dispatcher import dispatch_event, set_main_loop

# =========================
# UTILS
# =========================
import threading
import time
import asyncio
from datetime import datetime, timedelta

# =========================
# APP INIT
# =========================
app = FastAPI()

Base.metadata.create_all(bind=engine)

# =========================
# ROOT
# =========================


@app.get("/")
def root():
    return {"message": "Energy Aware Workload System Backend Running"}

# =========================
# NODE MONITOR
# =========================


def monitor_nodes():
    while True:
        print("🔄 Monitor running...")

        db = SessionLocal()

        try:
            threshold = datetime.utcnow() - timedelta(seconds=30)
            nodes = db.query(Node).all()

            for node in nodes:
                old_status = node.status

                if node.last_heartbeat and node.last_heartbeat >= threshold:
                    new_status = "ACTIVE"
                else:
                    new_status = "OFFLINE"

                if old_status != new_status:
                    print(f"🔥 STATUS CHANGE → {node.node_id} → {new_status}")

                    node.status = new_status

                    # ✅ SAFE DISPATCH (FIXED)
                    dispatch_event({
                        "type": "node_status",
                        "data": {
                            "node_id": node.node_id,
                            "status": new_status
                        }
                    })

            db.commit()

        except Exception as e:
            print("Monitor error:", e)

        finally:
            db.close()

        time.sleep(10)

# =========================
# STARTUP
# =========================


@app.on_event("startup")
async def start_background_tasks():
    print("🚀 Starting services...")

    # ✅ SET MAIN EVENT LOOP (CRITICAL FIX)
    loop = asyncio.get_running_loop()
    set_main_loop(loop)

    # ✅ THREAD SERVICES
    threading.Thread(target=monitor_nodes, daemon=True).start()
    threading.Thread(target=retraining_worker, daemon=True).start()

    # ✅ ASYNC SCHEDULER
    asyncio.create_task(scheduler_loop())

# =========================
# ROUTERS
# =========================
app.include_router(metrics_router)
app.include_router(nodes_router)
app.include_router(heartbeat_router)
app.include_router(execution_router)
app.include_router(upload_router)
app.include_router(node_execution_router)
app.include_router(execute_router)
app.include_router(retrain_router)
app.include_router(execution_metrics_router)
app.include_router(ws_router)
app.include_router(log_router)
app.include_router(ws_test_router)
