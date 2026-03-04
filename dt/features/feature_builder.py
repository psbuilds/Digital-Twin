from math import sqrt, exp,cos, pi
from datetime import datetime
from typing import Dict

from dt.models.twin_state import TwinState


class FeatureBuilder:
    """
    Builds higher-level, interpretable features from TwinState.
    Features describe *conditions*, not physics.
    """
    def build(self, state: TwinState) -> Dict[str, float]:
        features = {}
        hour = state.timestamp.hour
        if 6 <= hour <= 18:
            solar_potential = cos((hour - 12) * pi / 12) ** 2
        else:
            solar_potential = 0.0

        features["solar_potential"] = round(solar_potential, 3)

        #POLLUTION STRUCTURE FEATURES

        # Ratio of fine to coarse particles
        features["pm25_pm10_ratio"] = state.pm25 / max(state.pm10, 1.0)

        # Composite pollution load (normalized importance)
        features["pollution_load"] = (
            state.pm25 * 0.45 +
            state.pm10 * 0.30 +
            state.no2 * 0.10 +
            state.o3 * 0.05 +
            state.so2 * 0.05 +
            state.co * 0.05
        )

        # Gas dominance indicator
        features["gas_fraction"] = (
            state.no2 + state.o3 + state.so2 + state.co
        ) / max(
            state.pm25 + state.pm10 + state.no2 + state.o3 + state.so2 + state.co,
            1.0
        )

        # 2. DISPERSION & STAGNATION FEATURES
        # Ventilation index (classic air-quality metric)
        features["ventilation_index"] = (
            state.wind_speed * max(state.temperature + 273.15, 1.0)
        )

        # Stagnation probability proxy (0–1)
        features["stagnation_index"] = exp(
            -state.wind_speed / 2.0
        )

        # Dispersion strength (higher = cleaner air potential)
        features["dispersion_potential"] = (
            state.wind_speed / max(features["stagnation_index"], 0.1)
        )

        # 3. METEOROLOGY–CHEMISTRY INTERACTION FEATURES
        # Ozone formation potential (temp-driven proxy)
        features["ozone_formation_potential"] = max(
            0.0,
            (state.temperature - 25.0) / 15.0
        )

        # Rain washout potential (0–1)
        features["washout_potential"] = min(
            state.precipitation / 10.0,
            1.0
        )

        # 4. TEMPORAL CONTEXT FEATURES
        hour = state.timestamp.hour

        # Traffic emission proxy (morning + evening peaks)
        features["traffic_activity_index"] = (
            1.0 if 7 <= hour <= 10 or 17 <= hour <= 21 else 0.5
        )

        # Nighttime accumulation tendency
        features["night_accumulation_index"] = (
            1.0 if hour >= 22 or hour <= 5 else 0.0
        )

        # 5. GEOGRAPHICAL CONTEXT FEATURES

        # Coastal influence strength
        features["coastal_influence"] = (
            1.0 if state.is_coastal else 0.0
        )

        # Marine aerosol potential
        features["marine_aerosol_potential"] = (
            state.wind_speed * features["coastal_influence"]
        )


        prev_temp = state.metadata.get("prev_temperature", state.temperature)
        delta_temp = state.temperature - prev_temp

        features["delta_temperature"] = delta_temp
        features["ozone_driving_factor"] = max(0.0, delta_temp) * features["solar_potential"]

        state.metadata["prev_temperature"] = state.temperature


    
        # 6. SAFETY / NORMALIZATION

        # Ensure no NaNs or infinities
        for k, v in features.items():
            if not isinstance(v, (int, float)) or v != v:
                features[k] = 0.0

        return features
