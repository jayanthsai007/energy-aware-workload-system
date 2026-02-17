import numpy as np
import pandas as pd
import random

# Configuration
NUM_NODES = 20
NUM_SCRIPTS = 200
TIME_STEPS = 10

OUTPUT_FILE = "synthetic_dataset.csv"

random.seed(42)
np.random.seed(42)


# ----------------------------
# 1️⃣ Generate Node Profiles
# ----------------------------
nodes = []

for i in range(NUM_NODES):
    node_profile = {
        "cpu_cores": random.randint(2, 16),
        "total_memory": random.uniform(4, 32),  # GB
        "base_frequency": random.uniform(2.0, 4.5)  # GHz
    }
    nodes.append(node_profile)


# ----------------------------
# 2️⃣ Generate Script Profiles
# ----------------------------
scripts = []

for i in range(NUM_SCRIPTS):
    file_size = random.uniform(0.01, 1.0)  # normalized
    line_count = min(file_size * random.uniform(500, 5000), 1.0)

    script_profile = {
        "file_size_norm": file_size,
        "line_count_norm": line_count,
        "import_count_norm": random.uniform(0, 1),
        "function_count_norm": random.uniform(0, 1),
        "class_count_norm": random.uniform(0, 1),
        "language_encoded": random.randint(0, 1)
    }

    scripts.append(script_profile)


# ----------------------------
# 3️⃣ Generate Dataset Rows
# ----------------------------
rows = []

for script in scripts:
    for node in nodes:

        time_series_features = []

        # Simulate 10-step time-series
        for t in range(TIME_STEPS):
            cpu = random.uniform(20, 95) / 100
            memory = random.uniform(20, 90) / 100
            temp = cpu * random.uniform(0.8, 1.2)
            power = cpu * node["base_frequency"] * random.uniform(0.8, 1.2)

            time_series_features.extend([cpu, memory, temp, power])

        # Compute simulated execution time
        complexity = (
            script["file_size_norm"]
            + script["line_count_norm"]
            + script["function_count_norm"]
        )

        node_capacity = node["cpu_cores"] * node["base_frequency"]

        execution_time = complexity / node_capacity
        energy = np.mean(time_series_features[3::4]) * execution_time

        composite_score = 0.6 * execution_time + 0.4 * energy

        row = (
            time_series_features
            + [
                node["cpu_cores"],
                node["total_memory"],
                node["base_frequency"],
                script["file_size_norm"],
                script["line_count_norm"],
                script["import_count_norm"],
                script["function_count_norm"],
                script["class_count_norm"],
                script["language_encoded"],
                composite_score,
            ]
        )

        rows.append(row)


# ----------------------------
# 4️⃣ Create DataFrame
# ----------------------------
columns = []

for t in range(TIME_STEPS):
    columns.extend([
        f"cpu_t{t+1}",
        f"mem_t{t+1}",
        f"temp_t{t+1}",
        f"power_t{t+1}",
    ])

columns += [
    "cpu_cores",
    "total_memory",
    "base_frequency",
    "file_size_norm",
    "line_count_norm",
    "import_count_norm",
    "function_count_norm",
    "class_count_norm",
    "language_encoded",
    "composite_score",
]

df = pd.DataFrame(rows, columns=columns)

df.to_csv(OUTPUT_FILE, index=False)

print(f"Dataset generated successfully: {OUTPUT_FILE}")
print(f"Total samples: {len(df)}")
