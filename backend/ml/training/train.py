import os
import sys

# Add backend directory to path BEFORE imports
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")))

from ml.models.cnn_lstm_model import CNNLSTMModel
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib


# CONFIG
TIME_STEPS = 10
TS_FEATURES = 4
STATIC_FEATURES = 3
SCRIPT_FEATURES = 6
TOTAL_FEATURES = 49

EPOCHS = 10
BATCH_SIZE = 32
LR = 0.001

MODEL_PATH = "ml/saved_models/model_latest.pt"
SCALER_PATH = "ml/saved_models/scaler_latest.pkl"


# -----------------------
# CLEAN DATASET
# -----------------------
def clean_dataset(df):
    drop_cols = ["execution_time", "energy", "node_id"]
    df = df.drop([c for c in drop_cols if c in df.columns], axis=1)
    df = df.dropna()
    return df


# -----------------------
# PREP INPUT
# -----------------------
def prepare_inputs(X):
    ts_size = TIME_STEPS * TS_FEATURES

    ts = X[:, :ts_size].reshape(-1, TIME_STEPS, TS_FEATURES)
    static = X[:, ts_size:ts_size + STATIC_FEATURES]
    script = X[:, ts_size + STATIC_FEATURES:]

    return (
        torch.tensor(ts, dtype=torch.float32),
        torch.tensor(static, dtype=torch.float32),
        torch.tensor(script, dtype=torch.float32),
    )


# -----------------------
# LOAD INITIAL DATASETS
# -----------------------
def load_initial_datasets():
    dfs = []

    if os.path.exists("ml/training/synthetic_dataset.csv"):
        df_syn = pd.read_csv("ml/training/synthetic_dataset.csv")
        dfs.append(df_syn)

    if os.path.exists("ml/training/combined_dataset.csv"):
        df_real = pd.read_csv("ml/training/combined_dataset.csv")
        df_real = pd.concat([df_real]*2, ignore_index=True)  # weight real data
        dfs.append(df_real)

    if not dfs:
        return None

    df = pd.concat(dfs, ignore_index=True)
    return df


# -----------------------
# TRAIN MODEL
# -----------------------
def train_model(df):

    if df is None or len(df) < 50:
        print("⚠️ Not enough data")
        return

    df = clean_dataset(df)

    if "composite_score" not in df.columns:
        print("❌ Missing target")
        return

    if len(df.columns) != TOTAL_FEATURES + 1:
        print("❌ Feature mismatch:", len(df.columns))
        return

    X = df.drop("composite_score", axis=1).values
    y = df["composite_score"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    os.makedirs("ml/saved_models", exist_ok=True)
    joblib.dump(scaler, SCALER_PATH)

    X_train_ts, X_train_static, X_train_script = prepare_inputs(X_train)
    X_test_ts, X_test_static, X_test_script = prepare_inputs(X_test)

    y_train = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    y_test = torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)

    model = CNNLSTMModel(TIME_STEPS, TS_FEATURES,
                         STATIC_FEATURES, SCRIPT_FEATURES)

    optimizer = optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()

    print("🚀 Training...")

    for epoch in range(EPOCHS):
        model.train()
        perm = torch.randperm(X_train_ts.size(0))
        loss_total = 0

        for i in range(0, len(perm), BATCH_SIZE):
            idx = perm[i:i+BATCH_SIZE]

            out = model(
                X_train_ts[idx],
                X_train_static[idx],
                X_train_script[idx]
            )

            loss = loss_fn(out, y_train[idx])

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            loss_total += loss.item()

        print(f"Epoch {epoch+1}: {loss_total:.4f}")

# -----------------------
# Evaluation
# -----------------------
    model.eval()
    with torch.no_grad():
        test_outputs = model(X_test_ts, X_test_static, X_test_script)
        test_loss = loss_fn(test_outputs, y_test)

    print(f"✅ Test Loss: {test_loss.item():.6f}")

    print("\n📊 Sample predictions vs actual:\n")

    for i in range(min(5, len(test_outputs))):
        print(
            f"Predicted: {test_outputs[i].item():.6f} | Actual: {y_test[i].item():.6f}"
        )

    torch.save(model.state_dict(), MODEL_PATH)
    print("💾 Model saved")


# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    df = load_initial_datasets()
    train_model(df)
