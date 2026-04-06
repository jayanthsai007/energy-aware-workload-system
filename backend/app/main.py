from fastapi import FastAPI
from app.api.routes_metrics import router as metrics_router
from app.api.routes_nodes import router as nodes_router
from app.api.routes_heartbeat import router as heartbeat_router
from app.api.routes_execution import router as execution_router
from app.api.routes_upload import router as upload_router
from app.api.routes_node_execution import router as node_execution_router
from app.api.routes_execute import router as execute_router
from app.models.execution_metrics_model import ExecutionMetrics
from app.api.routes_retrain import router as retrain_router
from app.database import engine, Base, SessionLocal
from app.models.metrics_model import Metrics
from app.models.node_model import Node
from app.services.retraining_service import retraining_worker
from app.api.routes_execution_metrics import router as execution_metrics_router
import threading
import time
from datetime import datetime, timedelta


app = FastAPI()

Base.metadata.create_all(bind=engine)


# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"message": "Energy Aware Workload System Backend Running"}


# =========================
# BACKGROUND NODE MONITOR
# =========================
def monitor_nodes():
    while True:
        db = SessionLocal()

        try:
            threshold = datetime.utcnow() - timedelta(seconds=30)

            # ✅ Mark inactive nodes as OFFLINE
            db.query(Node).filter(
                Node.last_heartbeat < threshold
            ).update({"status": "offline"}, synchronize_session=False)

            db.commit()

        except Exception as e:
            print("Monitor error:", e)

        finally:
            db.close()

        time.sleep(10)  # run every 10 seconds


# =========================
# STARTUP EVENT
# =========================
@app.on_event("startup")
def start_background_tasks():
    print("Starting Node Health Monitor...")
    threading.Thread(target=monitor_nodes, daemon=True).start()
   # line for automatic model retraiing using realtime data
    threading.Thread(target=retraining_worker, daemon=True).start()


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


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
