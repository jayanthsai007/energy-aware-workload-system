from fastapi import FastAPI
from app.api.routes_metrics import router as metrics_router

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Energy Aware Workload System Backend Running"}

app.include_router(metrics_router)

