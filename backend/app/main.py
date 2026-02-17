from fastapi import FastAPI
from app.api.routes_metrics import router as metrics_router
from app.api.routes_nodes import router as nodes_router
from app.database import engine, Base
from app.models.device_metrics_model import DeviceMetricsDB
from app.models.node_model import Node

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Energy Aware Workload System Backend Running"}

app.include_router(metrics_router)
app.include_router(nodes_router)
