import torch
import torch.nn as nn


class CNNLSTMModel(nn.Module):
    def __init__(self, time_steps=10, ts_features=4, static_features=3, script_features=6):
        super(CNNLSTMModel, self).__init__()

        # --- Time Series CNN ---
        self.conv1 = nn.Conv1d(
            in_channels=ts_features,
            out_channels=16,
            kernel_size=3,
            padding=1
        )

        self.relu = nn.ReLU()

        # --- LSTM ---
        self.lstm = nn.LSTM(
            input_size=16,
            hidden_size=32,
            num_layers=1,
            batch_first=True
        )

        # --- Static Feature Dense ---
        self.static_dense = nn.Linear(static_features, 16)

        # --- Script Feature Dense ---
        self.script_dense = nn.Linear(script_features, 16)

        # --- Final Fully Connected ---
        self.final_dense = nn.Sequential(
            nn.Linear(32 + 16 + 16, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, time_series, static_features, script_features):

        # time_series shape: (batch_size, time_steps, ts_features)

        # Convert to (batch_size, ts_features, time_steps) for CNN
        x = time_series.permute(0, 2, 1)

        x = self.conv1(x)
        x = self.relu(x)

        # Convert back to (batch_size, time_steps, features)
        x = x.permute(0, 2, 1)

        # LSTM
        lstm_out, _ = self.lstm(x)

        # Take last time step output
        lstm_last = lstm_out[:, -1, :]

        # Process static features
        static_out = self.relu(self.static_dense(static_features))

        # Process script features
        script_out = self.relu(self.script_dense(script_features))

        # Concatenate all
        combined = torch.cat((lstm_last, static_out, script_out), dim=1)

        output = self.final_dense(combined)

        return output
