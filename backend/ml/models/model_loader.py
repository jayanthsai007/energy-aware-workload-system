import sys
import os
import torch
import numpy as np
import joblib

# Fix import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from ml.models.cnn_lstm_model import CNNLSTMModel


TIME_STEPS = 10
TS_FEATURES = 4
STATIC_FEATURES = 3
SCRIPT_FEATURES = 6

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../saved_models/model_v1.pt")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "../saved_models/scaler_v1.pkl")


class ModelLoader:
    def __init__(self):
        self.model = CNNLSTMModel(
            time_steps=TIME_STEPS,
            ts_features=TS_FEATURES,
            static_features=STATIC_FEATURES,
            script_features=SCRIPT_FEATURES,
        )

        self.model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))
        self.model.eval()

        # Load scaler
        self.scaler = joblib.load(SCALER_PATH)

    def predict(self, time_series, static_features, script_features):
        """
        time_series: numpy array shape (10, 4)
        static_features: numpy array shape (3,)
        script_features: numpy array shape (6,)
        """

        # Flatten into single feature vector
        ts_flat = time_series.flatten()
        full_input = np.concatenate([ts_flat, static_features, script_features]).reshape(1, -1)

        # Apply scaler
        scaled_input = self.scaler.transform(full_input)

        # Split again
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
