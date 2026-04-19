import time
from datetime import datetime
from app.database import SessionLocal
from app.models.execution_metrics_model import ExecutionMetrics
from ml.realtime.dataset_builder import build_realtime_dataset
import pandas as pd
import os

RETRAIN_THRESHOLD = 50   # 🔥 retrain after 50 new executions
CHECK_INTERVAL = 30      # seconds


def retraining_worker():
    print("🤖 Retraining service started...")

    last_count = 0

    while True:
        db = SessionLocal()

        try:
            total = db.query(ExecutionMetrics).count()

            # First run initialization
            if last_count == 0:
                last_count = total

            new_data = total - last_count

            if new_data >= RETRAIN_THRESHOLD:
                print(f"\n🔥 Triggering retraining... New samples: {new_data}")

                dfs = []

                # -----------------------------
                # Synthetic
                # -----------------------------
                if os.path.exists("ml/training/synthetic_dataset.csv"):
                    dfs.append(pd.read_csv(
                        "ml/training/synthetic_dataset.csv"))

                # -----------------------------
                # Static dataset
                # -----------------------------
                if os.path.exists("ml/training/combined_dataset.csv"):
                    df_real = pd.read_csv("ml/training/combined_dataset.csv")
                    df_real = pd.concat([df_real]*2, ignore_index=True)
                    dfs.append(df_real)

                # -----------------------------
                # Realtime dataset
                # -----------------------------
                df_rt = build_realtime_dataset()
                if df_rt is not None:
                    dfs.append(df_rt)

                if dfs:
                    df = pd.concat(dfs, ignore_index=True)

                    print(f"📊 Training on {len(df)} samples")

                    from ml.training.train import train_model
                    train_model(df)

                    print("✅ Auto retraining complete")

                    # update checkpoint
                    last_count = total

                else:
                    print("⚠️ No data available for retraining")

        except Exception as e:
            print("❌ Retraining error:", e)

        finally:
            db.close()

        time.sleep(CHECK_INTERVAL)
