import math

from copy import deepcopy
from datetime import timedelta
from typing import Dict, Tuple

from dt.models.twin_state import TwinState
from dt.features.feature_builder import FeatureBuilder
from dt.rules.current_aqi_rules import evaluate_current_aqi

MAX_CONCENTRATION = 1000.0

# ensure that the values dont exceed a certain limit
def clamp_upper_bounds(state: TwinState):
    for p in ("pm25", "pm10", "no2", "o3", "so2", "co"):
        setattr(state, p, min(getattr(state, p), MAX_CONCENTRATION))


# Adds a daily temperature cycle.
def apply_diurnal_temperature(state: TwinState):
    """
    Applies a simple diurnal temperature cycle.
    Temperature oscillates gently over day.
    """
    hour = state.timestamp.hour
    # Simple sinusoidal cycle (°C) 
    diurnal_variation = 3.0 * math.sin((hour - 6) * math.pi / 12)
    state.temperature = round(state.temperature + diurnal_variation, 2)



def update_state(
    state: TwinState,
    dt_hours: float = 1.0
) -> Tuple[TwinState, Dict]:
    if dt_hours <= 0:
        raise ValueError("dt_hours must be positive")

    next_state = deepcopy(state)                            # Ensure original state is preserved.
    next_state.timestamp += timedelta(hours=dt_hours)       # Moves clock forward
    apply_diurnal_temperature(next_state)

    # BEFORE snapshot captures pollutant values before AQI rules and clamping.
    # Used for debugging and auditing.
    before = {
        p: getattr(next_state, p)
        for p in ("pm25", "pm10", "no2", "o3", "so2", "co")
    }

    features = FeatureBuilder().build(next_state)
    aqi_report = evaluate_current_aqi(next_state, features)
    clamp_upper_bounds(next_state)

    # AFTER snapshot captures pollutant values after AQI rules and clamping.
    after = {
        p: getattr(next_state, p)
        for p in before
    }

    # Stores the updated metadata 
    next_state.metadata["features"] = features
    next_state.metadata["snapshots"] = {
        "before": before,
        "after": after,
    }
    next_state.metadata["aqi_report"] = {
    "aqi": aqi_report["aqi"],
    "dominant_pollutant": aqi_report["dominant_pollutant"],
    "sub_indices": aqi_report["sub_indices"],
    }

    next_state.metadata["rule_effects"] = aqi_report["rule_effects"]
    next_state.metadata["rule_reasons"] = aqi_report["rule_reasons"]


    return next_state, aqi_report


"""
copy state
   ↓
advance time
   ↓
apply temperature wave
   ↓
record pollutants (before)
   ↓
build features
   ↓
evaluate AQI rules
   ↓
clamp extreme values
   ↓
record pollutants (after)
   ↓
store metadata
   ↓
return new state + report
"""