from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class TwinState:
    grid_id: str
    timestamp: datetime
    latitude: float
    longitude: float

    # meteorology
    wind_speed: float          # m/s
    wind_direction: float      # degrees
    temperature: float         # °C
    precipitation: float       # mm

    # pollutants
    pm25: float
    pm10: float
    no2: float
    o3: float
    so2: float
    co: float                  # mg/m³

    # coastal info 
    sea_surface_temp: Optional[float] = None
    is_coastal: Optional[bool] = None

    # derived flags / helper signals
    metadata: Dict[str, float] = field(default_factory=dict)

    def clamp_non_negative(self) -> None:
        """
        Safety guard: ensure no pollutant becomes negative.
        Called after rule application.
        """
        for attr in ("pm25", "pm10", "no2", "o3", "so2", "co"):
            if getattr(self, attr) < 0:
                setattr(self, attr, 0.0)