from dt.simulation.scenario_simulator import run_scenario
from dt.models.twin_state import TwinState
from datetime import datetime, timezone
initial_state = TwinState(
    grid_id="KL_001",
    latitude=9.97,
    longitude=76.28,
    timestamp=datetime.now(timezone.utc),

    wind_speed=1.2,
    wind_direction=270.0,
    temperature=29.0,
    precipitation=0.0,

    pm25=40.0,
    pm10=65.0,
    no2=22.0,
    o3=30.0,
    so2=5.0,
    co=0.8,

    sea_surface_temp=28.0,
    metadata={"is_coastal": 1.0}
)


history = run_scenario(initial_state, 24)
print(len(history))
