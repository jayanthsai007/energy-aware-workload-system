def classify_workload(cpu: float, memory: float, temperature: float) -> str:
    """
    Classify workload intensity based on system metrics.
    Returns: LOW, MEDIUM, or HIGH
    """

    # Basic rule-based logic (temporary before ML integration)

    if cpu < 40 and memory < 50:
        return "LOW"

    elif cpu < 75:
        return "MEDIUM"

    else:
        return "HIGH"
