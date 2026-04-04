from fastapi import APIRouter
import pandas as pd
import os

from ml.training.train import train_model
from ml.realtime.dataset_builder import build_realtime_dataset
from ml.models.model_loader import ModelLoader

router = APIRouter()


@router.post("/retrain")
def retrain_model():

    dfs = []

    # -----------------------------
    # 1. Synthetic dataset
    # -----------------------------
    if os.path.exists("ml/training/synthetic_dataset.csv"):
        df_syn = pd.read_csv("ml/training/synthetic_dataset.csv")
        dfs.append(df_syn)
        print(f"✅ Synthetic: {len(df_syn)} rows")

    # -----------------------------
    # 2. Static real dataset
    # -----------------------------
    if os.path.exists("ml/training/combined_dataset.csv"):
        df_real = pd.read_csv("ml/training/combined_dataset.csv")

        # weight real data higher
        df_real = pd.concat([df_real]*2, ignore_index=True)

        dfs.append(df_real)
        print(f"✅ Static real: {len(df_real)} rows")

    # -----------------------------
    # 3. Realtime dataset (🔥 important)
    # -----------------------------
    df_rt = build_realtime_dataset()

    if df_rt is not None:
        dfs.append(df_rt)
        print(f"✅ Realtime: {len(df_rt)} rows")

    # -----------------------------
    # 4. Merge all
    # -----------------------------
    if not dfs:
        return {"status": "error", "message": "No datasets found"}

    df = pd.concat(dfs, ignore_index=True)

    print(f"\n📊 Total training data: {len(df)} rows")

    # -----------------------------
    # 5. Train model
    # -----------------------------
    train_model(df)

    # -----------------------------
    # 6. Reload model (🔥 IMPORTANT)
    # -----------------------------
    global model
    model = ModelLoader()

    print("🔄 Model reloaded")

    return {
        "status": "success",
        "message": "Model retrained successfully",
        "total_samples": len(df)
    }
