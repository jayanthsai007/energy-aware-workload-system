from fastapi import FastAPI
from app.api.routes_metrics import router as metrics_router
from app.database import engine, Base
from app.models.device_metrics_model import DeviceMetricsDB

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Energy Aware Workload System Backend Running"}

app.include_router(metrics_router)


