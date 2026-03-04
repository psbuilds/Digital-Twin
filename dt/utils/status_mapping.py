def get_aqi_status(aqi):
    if aqi <= 50:
        return {"label": "Good", "severity": 1}
    if aqi <= 100:
        return {"label": "Moderate", "severity": 2}
    if aqi <= 200:
        return {"label": "Poor", "severity": 3}
    if aqi <= 300:
        return {"label": "Very Poor", "severity": 4}
    return {"label": "Severe", "severity": 5}
