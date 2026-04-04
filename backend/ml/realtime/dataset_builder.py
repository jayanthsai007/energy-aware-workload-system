import pandas as pd

from app.database import SessionLocal
from app.models.execution_metrics_model import ExecutionMetrics
from app.models.node_model import Node


TIME_STEPS = 10


def build_realtime_dataset():
    db = SessionLocal()

    try:
        rows = db.query(ExecutionMetrics).order_by(
            ExecutionMetrics.timestamp
        ).all()

        if len(rows) < TIME_STEPS:
            print("⚠️ Not enough execution data")
            return None

        data = []

        for i in range(len(rows) - TIME_STEPS):

            window = rows[i:i + TIME_STEPS]
            last = window[-1]

            # -----------------------
            # 1️⃣ TIME SERIES (40 features)
            # -----------------------
            ts = []

            for r in window:
                cpu = (r.cpu_avg or 0) / 100
                mem = (r.memory_avg or 0) / 100
                temp = (r.temperature_avg or 50) / 100
                power = cpu * 1.5  # proxy

                ts.extend([cpu, mem, temp, power])

            # -----------------------
            # 2️⃣ NODE FEATURES (3)
            # -----------------------
            node = db.query(Node).filter(
                Node.node_id == last.node_id
            ).first()

            if node:
                static = [
                    (node.cpu_cores or 0) / 16,
                    (node.total_memory or 0) / 32,
                    (node.cpu_frequency or 0) / 5
                ]
            else:
                static = [0, 0, 0]

            # -----------------------
            # 3️⃣ SCRIPT FEATURES (6) 🔥 FROM DB
            # -----------------------
            script_features = [
                last.file_size or 0,
                last.line_count or 0,
                last.imports or 0,
                last.functions or 0,
                last.classes or 0,
                1 if last.language == "python" else 0
            ]

            # -----------------------
            # 4️⃣ TARGET (IMPORTANT)
            # -----------------------
            composite_score = last.composite_score or 0

            # -----------------------
            # FINAL ROW
            # -----------------------
            row = ts + static + script_features + [composite_score]

            data.append(row)

        df = pd.DataFrame(data)

        if len(df) < 20:
            print("⚠️ Dataset too small")
            return None

        print(f"✅ Real-time dataset built: {len(df)} rows")

        return df

    finally:
        db.close()
