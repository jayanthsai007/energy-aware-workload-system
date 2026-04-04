from ml.models.cnn_lstm_model import CNNLSTMModel
import sys
import os
import torch
import numpy as np
import joblib

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")))


TIME_STEPS = 10
TS_FEATURES = 4
STATIC_FEATURES = 3
SCRIPT_FEATURES = 6

# ✅ UPDATED PATHS
MODEL_PATH = os.path.join(os.path.dirname(
    __file__), "../saved_models/model_latest.pt")
SCALER_PATH = os.path.join(os.path.dirname(
    __file__), "../saved_models/scaler_latest.pkl")


class ModelLoader:
    def __init__(self):

        # ✅ Check if model exists
        if not os.path.exists(MODEL_PATH):
            raise Exception("❌ Model not found. Train the model first.")

        if not os.path.exists(SCALER_PATH):
            raise Exception("❌ Scaler not found. Train the model first.")

        self.model = CNNLSTMModel(
            time_steps=TIME_STEPS,
            ts_features=TS_FEATURES,
            static_features=STATIC_FEATURES,
            script_features=SCRIPT_FEATURES,
        )

        # ✅ Load trained model
        self.model.load_state_dict(
            torch.load(MODEL_PATH, map_location=torch.device("cpu"))
        )
        self.model.eval()

        # ✅ Load scaler
        self.scaler = joblib.load(SCALER_PATH)

        print("✅ ML Model Loaded Successfully")

    def predict(self, time_series, static_features, script_features):

        ts_flat = time_series.flatten()
        full_input = np.concatenate(
            [ts_flat, static_features, script_features]
        ).reshape(1, -1)

        scaled_input = self.scaler.transform(full_input)

        ts_size = TIME_STEPS * TS_FEATURES

        ts = scaled_input[:, :ts_size].reshape(-1, TIME_STEPS, TS_FEATURES)
        static = scaled_input[:, ts_size:ts_size + STATIC_FEATURES]
        script = scaled_input[:, ts_size + STATIC_FEATURES:]

        ts_tensor = torch.tensor(ts, dtype=torch.float32)
        static_tensor = torch.tensor(static, dtype=torch.float32)
        script_tensor = torch.tensor(script, dtype=torch.float32)

        with torch.no_grad():
            output = self.model(ts_tensor, static_tensor, script_tensor)

        return output.item()
