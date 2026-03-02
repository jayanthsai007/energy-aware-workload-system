import torch
import torch.nn as nn


class CNNLSTMModel(nn.Module):
    """
    Hybrid CNN + LSTM model for energy workload prediction.

    Inputs:
        time_series      -> (batch, time_steps, ts_features)
        static_features  -> (batch, static_features)
        script_features  -> (batch, script_features)

    Output:
        predicted energy value (batch, 1)
    """

    def __init__(self, time_steps=10, ts_features=4, static_features=3, script_features=6):
        super(CNNLSTMModel, self).__init__()

        # ---------- CNN for time series ----------
        self.conv1 = nn.Conv1d(
            in_channels=ts_features,
            out_channels=16,
            kernel_size=3,
            padding=1
        )

        self.relu = nn.ReLU()

        # ---------- LSTM ----------
        self.lstm = nn.LSTM(
            input_size=16,
            hidden_size=32,
            num_layers=1,
            batch_first=True
        )

        # ---------- Static feature branch ----------
        self.static_dense = nn.Linear(static_features, 16)

        # ---------- Script feature branch ----------
        self.script_dense = nn.Linear(script_features, 16)

        # ---------- Final prediction head ----------
        self.final_dense = nn.Sequential(
            nn.Linear(32 + 16 + 16, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, time_series, static_features, script_features):

        # VERY IMPORTANT: ensure tensors are float32
        time_series = time_series.float()
        static_features = static_features.float()
        script_features = script_features.float()

        # Input shape: (batch, time_steps, ts_features)
        # CNN expects: (batch, channels, sequence)
        x = time_series.permute(0, 2, 1)

        # CNN
        x = self.conv1(x)
        x = self.relu(x)

        # Back to LSTM shape: (batch, time_steps, features)
        x = x.permute(0, 2, 1)

        # LSTM
        lstm_out, _ = self.lstm(x)

        # Take last timestep
        lstm_last = lstm_out[:, -1, :]

        # Static features branch
        static_out = self.relu(self.static_dense(static_features))

        # Script features branch
        script_out = self.relu(self.script_dense(script_features))

        # Combine all features
        combined = torch.cat((lstm_last, static_out, script_out), dim=1)

        # Final prediction
        output = self.final_dense(combined)

        return output
