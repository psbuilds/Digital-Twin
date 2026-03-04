def minimal_aqi_view(aqi_report: dict) -> dict:
    return {
        "aqi": aqi_report["aqi"],
        "dominant_pollutant": aqi_report["dominant_pollutant"],
    }


def standard_aqi_view(aqi_report: dict) -> dict:
    return {
        "aqi": aqi_report["aqi"],
        "dominant_pollutant": aqi_report["dominant_pollutant"],
        "sub_indices": aqi_report["sub_indices"],
    }


def debug_aqi_view(aqi_report: dict) -> dict:
    return aqi_report
