import requests

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 3


def safe_request(method, endpoint, payload=None):
    try:
        url = f"{BASE_URL}{endpoint}"

        if method == "GET":
            res = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            res = requests.post(url, json=payload, timeout=TIMEOUT)
        else:
            return None

        if res.status_code == 200:
            return res.json()
        return []

    except:
        return []


def get_nodes():
    data = safe_request("GET", "/nodes")
    return data if isinstance(data, list) else []


def get_metrics():
    data = safe_request("GET", "/metrics")
    return data if isinstance(data, list) else []


def get_executions():
    data = safe_request("GET", "/execution-metrics")
    return data if isinstance(data, list) else []


def get_model_performance():
    data = safe_request("GET", "/model-performance")
    if isinstance(data, dict):
        return [data]
    return data if isinstance(data, list) else []


def retrain_model():
    res = safe_request("POST", "/retrain")
    return res if res else {"message": "Triggered"}
