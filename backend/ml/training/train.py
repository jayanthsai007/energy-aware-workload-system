import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


from ml.models.cnn_lstm_model import CNNLSTMModel

# -----------------------
# Configuration
# -----------------------
DATA_PATH = "synthetic_dataset.csv"
MODEL_SAVE_PATH = "../saved_models/model_v1.pt"

TIME_STEPS = 10
TS_FEATURES = 4
STATIC_FEATURES = 3
SCRIPT_FEATURES = 6

EPOCHS = 30
BATCH_SIZE = 32
LEARNING_RATE = 0.001


# -----------------------
# Load Dataset
# -----------------------
df = pd.read_csv(DATA_PATH)

X = df.drop("composite_score", axis=1).values
y = df["composite_score"].values

# -----------------------
# Split Dataset
# -----------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------
# Feature Scaling
# -----------------------
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# -----------------------
# Convert to Tensors
# -----------------------
def prepare_inputs(X):
    # Time series part
    ts_size = TIME_STEPS * TS_FEATURES
    ts = X[:, :ts_size]
    ts = ts.reshape(-1, TIME_STEPS, TS_FEATURES)

    # Static part
    static = X[:, ts_size:ts_size + STATIC_FEATURES]

    # Script part
    script = X[:, ts_size + STATIC_FEATURES:]

    return (
        torch.tensor(ts, dtype=torch.float32),
        torch.tensor(static, dtype=torch.float32),
        torch.tensor(script, dtype=torch.float32),
    )


X_train_ts, X_train_static, X_train_script = prepare_inputs(X_train)
X_test_ts, X_test_static, X_test_script = prepare_inputs(X_test)

y_train = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
y_test = torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)

# -----------------------
# Model Setup
# -----------------------
model = CNNLSTMModel(
    time_steps=TIME_STEPS,
    ts_features=TS_FEATURES,
    static_features=STATIC_FEATURES,
    script_features=SCRIPT_FEATURES,
)

criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# -----------------------
# Training Loop
# -----------------------
for epoch in range(EPOCHS):
    model.train()

    permutation = torch.randperm(X_train_ts.size()[0])

    epoch_loss = 0

    for i in range(0, X_train_ts.size()[0], BATCH_SIZE):
        indices = permutation[i:i+BATCH_SIZE]

        batch_ts = X_train_ts[indices]
        batch_static = X_train_static[indices]
        batch_script = X_train_script[indices]
        batch_y = y_train[indices]

        optimizer.zero_grad()

        outputs = model(batch_ts, batch_static, batch_script)

        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    print(f"Epoch [{epoch+1}/{EPOCHS}], Loss: {epoch_loss:.4f}")

# -----------------------
# Evaluation
# -----------------------
model.eval()
with torch.no_grad():
    test_outputs = model(X_test_ts, X_test_static, X_test_script)
    test_loss = criterion(test_outputs, y_test)

print(f"Test Loss: {test_loss.item():.4f}")

# -----------------------
# Save Model
# -----------------------
os.makedirs("../saved_models", exist_ok=True)
torch.save(model.state_dict(), MODEL_SAVE_PATH)

print(f"Model saved to {MODEL_SAVE_PATH}")
