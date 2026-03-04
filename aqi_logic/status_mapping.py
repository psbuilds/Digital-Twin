def get_aqi_status(aqi_value):
    """
    Returns the status category and color for a given AQI value.
    """
    if aqi_value is None:
        return {"category": "N/A", "color": "#808080", "description": "No data available"}
    
    if 0 <= aqi_value <= 50:
        return {
            "category": "Good",
            "color": "#00B050",
            "description": "Minimal impact"
        }
    elif 51 <= aqi_value <= 100:
        return {
            "category": "Satisfactory",
            "color": "#92D050",
            "description": "Minor breathing discomfort to sensitive people"
        }
    elif 101 <= aqi_value <= 200:
        return {
            "category": "Moderate",
            "color": "#FFFF00",
            "textColor": "#000000",
            "description": "Breathing discomfort to the people with lungs, asthma and heart diseases"
        }
    elif 201 <= aqi_value <= 300:
        return {
            "category": "Poor",
            "color": "#FF9900",
            "description": "Breathing discomfort to most people on prolonged exposure"
        }
    elif 301 <= aqi_value <= 400:
        return {
            "category": "Very Poor",
            "color": "#FF0000",
            "description": "Respiratory illness on prolonged exposure"
        }
    elif aqi_value > 400:
        return {
            "category": "Severe",
            "color": "#C00000",
            "description": "Affects healthy people and seriously impacts those with existing diseases"
        }
    else:
        return {"category": "N/A", "color": "#808080", "description": "Out of range"}
