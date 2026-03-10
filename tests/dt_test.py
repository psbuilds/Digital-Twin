from datetime import datetime

from dt.models.twin_state import TwinState
from dt.engine.state_updater import update_state


# Create an initial TwinState
state = TwinState(
    grid_id="KL_001",
    latitude=9.97,
    longitude=76.28,
    timestamp=datetime.utcnow(),

    wind_speed=1.2,      # LOW WIND
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


# Run the Digital Twin for a few hours
for hour in range(6):
    state, report = update_state(state)
    print(
        f"{state.timestamp} | "
        f"PM2.5={state.pm25:.2f} | "
        f"NO2={state.no2:.2f} | "
        f"Wind={state.wind_speed:.1f}"
    )
