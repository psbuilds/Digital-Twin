"""
Explainable AQI rule engine for the Digital Twin.

Adds:
- Per-rule, per-pollutant attribution
- Rule firing reasons
- Feature-driven physics
"""

from typing import Dict, Tuple
from dt.models.twin_state import TwinState

# NUMERICAL SAFETY (no rule can redeuce pollution by more than 30 percent or increase by more than 70 percent )
MIN_FACTOR = 0.7
MAX_FACTOR = 1.3


def clamp_factor(value: float) -> float:
    return max(MIN_FACTOR, min(value, MAX_FACTOR))


# RULES (WITH EXPLAINABILITY)
def _record(
    effects: Dict,
    pollutant: str,
    rule: str,
    delta: float
):
    effects[pollutant][rule] = delta

# If wind mixing is strong → pollution spreads out → lower values.
def apply_wind_dispersion(state: TwinState, features: Dict, effects: Dict):
    dispersion = features["dispersion_potential"]
    if dispersion < 1.5:
        return

    factor = clamp_factor(1.0 - 0.05 * dispersion)          

    for p in ("pm25", "pm10", "no2", "so2", "co"):
        before = getattr(state, p)
        after = before * factor
        setattr(state, p, after)
        _record(effects, p, "wind_dispersion", before - after)

    state.metadata.setdefault("rule_reasons", {})["wind_dispersion"] = {
        "dispersion_potential": round(dispersion, 3),
        "factor": round(factor, 3)
        }

# Rain removes particles from air. Only affects PM2.5 and PM10. more rain -> more reduction
def apply_rain_washout(state: TwinState, features: Dict, effects: Dict):
    washout = features["washout_potential"]
    if washout <= 0:
        return

    factor = clamp_factor(1.0 - 0.6 * washout)

    for p in ("pm25", "pm10"):
        before = getattr(state, p)
        after = before * factor
        setattr(state, p, after)
        _record(effects, p, "rain_washout", before - after)

    state.metadata.setdefault("rule_reasons", {})["rain_washout"] = {
        "washout_potential": washout
    }

#If air is stagnant: Pollution builds up instead of dispersing. ie stagnation => increase values 
def apply_stagnant_accumulation(state: TwinState, features: Dict, effects: Dict):
    stagnation = features["stagnation_index"]
    if stagnation < 0.7:
        return

    factor = clamp_factor(1.0 + 0.2 * stagnation)           # Hardcoded 0.2 * stagnation updates

    for p in ("pm25", "no2", "co"):
        before = getattr(state, p)
        after = before * factor
        setattr(state, p, after)
        _record(effects, p, "stagnant_accumulation", after - before)

    state.metadata.setdefault("rule_reasons", {})["stagnant_accumulation"] = {
        "stagnation_index": stagnation
    }


def apply_temperature_ozone_effect(state: TwinState, features: Dict, effects: Dict):
    """
    Ozone formation driven by temperature increase under sunlight,
    not by absolute temperature.
    """

    delta_temp = features.get("delta_temperature", 0.0)
    solar = features.get("solar_potential", 0.0)

    # No heating or no sunlight → no ozone production
    if delta_temp <= 0 or solar <= 0:
        return

    # Ozone driving strength (bounded, interpretable)
    driving = min(0.3, delta_temp * solar)

    before = state.o3
    state.o3 *= clamp_factor(1.0 + driving)

    delta = state.o3 - before
    _record(effects, "o3", "temperature_ozone_effect", delta)

    # Explainability
    state.metadata.setdefault("rule_reasons", {})["temperature_ozone_effect"] = {
        "delta_temperature": round(delta_temp, 2),
        "solar_potential": round(solar, 2),
        "ozone_driving_factor": round(driving, 3),
    }



def apply_coastal_sea_breeze(state: TwinState, features: Dict, effects: Dict):
    if features["coastal_influence"] == 0:
        return

    before = state.pm25
    state.pm25 *= clamp_factor(0.9)
    _record(effects, "pm25", "coastal_dilution", before - state.pm25)

    before = state.pm10
    state.pm10 *= clamp_factor(1.05)
    _record(effects, "pm10", "marine_aerosol", state.pm10 - before)

    state.metadata.setdefault("rule_reasons", {})["coastal_sea_breeze"] = {
        "coastal": True
    }


# CPCB AQI COMPUTATION
def compute_sub_index(value: float, breakpoints):
    for cl, ch, il, ih in breakpoints:
        if cl <= value <= ch:
            return ((ih - il) / (ch - cl)) * (value - cl) + il
    return None


PM25_BREAKPOINTS = (
    (0, 30, 0, 50),
    (31, 60, 51, 100),
    (61, 90, 101, 200),
    (91, 120, 201, 300),
    (121, 250, 301, 500),
)

PM10_BREAKPOINTS = (
    (0, 50, 0, 50),
    (51, 100, 51, 100),
    (101, 250, 101, 200),
    (251, 350, 201, 300),
    (351, 430, 301, 500),
)

NO2_BREAKPOINTS = (
    (0, 40, 0, 50),
    (41, 80, 51, 100),
    (81, 180, 101, 200),
    (181, 280, 201, 300),
    (281, 400, 301, 500),
)

O3_BREAKPOINTS = (
    (0, 50, 0, 50),
    (51, 100, 51, 100),
    (101, 168, 101, 200),
    (169, 208, 201, 300),
    (209, 748, 301, 500),
)

SO2_BREAKPOINTS = (
    (0, 40, 0, 50),
    (41, 80, 51, 100),
    (81, 380, 101, 200),
    (381, 800, 201, 300),
    (801, 1600, 301, 500),
)

CO_BREAKPOINTS = (
    (0, 1, 0, 50),
    (1.1, 2, 51, 100),
    (2.1, 10, 101, 200),
    (10.1, 17, 201, 300),
    (17.1, 34, 301, 500),
)


def compute_aqi(state: TwinState):
    sub = {
        "pm25": compute_sub_index(state.pm25, PM25_BREAKPOINTS),
        "pm10": compute_sub_index(state.pm10, PM10_BREAKPOINTS),
        "no2": compute_sub_index(state.no2, NO2_BREAKPOINTS),
        "o3": compute_sub_index(state.o3, O3_BREAKPOINTS),
        "so2": compute_sub_index(state.so2, SO2_BREAKPOINTS),
        "co": compute_sub_index(state.co, CO_BREAKPOINTS),
    }

    sub = {k: v for k, v in sub.items() if v is not None}
    dominant = max(sub, key=sub.get)
    return round(sub[dominant], 2), dominant, sub


# PIPELINE + API

RULE_PIPELINE = [
    apply_wind_dispersion,
    apply_rain_washout,
    apply_stagnant_accumulation,
    apply_temperature_ozone_effect,
    apply_coastal_sea_breeze,
]


def evaluate_current_aqi(state: TwinState, features: Dict) -> Dict:
    effects = {p: {} for p in ("pm25", "pm10", "no2", "o3", "so2", "co")}

    for rule in RULE_PIPELINE:
        rule(state, features, effects)

    state.clamp_non_negative()

    aqi, dominant, sub = compute_aqi(state)

    return {
        "aqi": aqi,
        "dominant_pollutant": dominant,
        "sub_indices": sub,
        "rule_effects": effects,
        "rule_reasons": state.metadata.get("rule_reasons", {}),
    }
