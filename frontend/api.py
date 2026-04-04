import requests

BASE_URL = "http://127.0.0.1:8000"


def get_nodes():
    return requests.get(f"{BASE_URL}/nodes").json()


def get_metrics():
    return requests.get(f"{BASE_URL}/metrics").json()


def get_executions():
    return requests.get(f"{BASE_URL}/execution-metrics").json()


def get_model_performance():
    try:
        return requests.get(f"{BASE_URL}/model-performance").json()
    except:
        return []


def retrain_model():
    return requests.post(f"{BASE_URL}/retrain").json()
