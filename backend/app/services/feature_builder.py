from sqlalchemy.orm import Session
from app.models.metrics_model import Metrics
from app.models.node_model import Node
import numpy as np


TIME_STEPS = 10


def get_time_series(db: Session, node_id: str):
    records = (
        db.query(Metrics)
        .filter(Metrics.node_id == node_id)
        .order_by(Metrics.node_timestamp.desc())
        .limit(TIME_STEPS)
        .all()
    )

    if len(records) < TIME_STEPS:
        return None

    records = list(reversed(records))

    ts = []
    for r in records:
        cpu = r.cpu_usage / 100
        mem = r.memory_usage / 100
        temp = r.temperature / 100

        power = cpu * 1.5  # simple proxy

        ts.append([cpu, mem, temp, power])

    return np.array(ts)


def get_static_features(node: Node):
    return np.array([
        node.cpu_cores / 16,
        node.total_memory / 32,
        node.cpu_frequency / 5
    ])


def get_script_features(script):
    return np.array([
        script["file_size"],
        script["line_count"],
        script["imports"],
        script["functions"],
        script["classes"],
        script["language"]
    ])


def build_features(db: Session, node: Node, script):

    ts = get_time_series(db, node.node_id)

    if ts is None:
        return None

    static = get_static_features(node)
    script_f = get_script_features(script)

    return ts, static, script_f
