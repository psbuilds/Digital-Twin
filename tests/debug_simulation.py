from dt.models.twin_state import TwinState
from dt.engine.state_updater import update_state
from dt.rules.current_aqi_rules import evaluate_current_aqi
from dt.explainability.explainer import explain_step
from dt.explainability.audit_views import minimal_aqi_view,standard_aqi_view,debug_aqi_view
from dt.features.feature_builder import FeatureBuilder
from datetime import datetime
from pprint import pprint


def print_state(label, state):
    print(f"\n--- {label} ---")
    print(f"PM2.5: {state.pm25:.2f}")
    print(f"PM10 : {state.pm10:.2f}")
    print(f"NO2  : {state.no2:.2f}")
    print(f"O3   : {state.o3:.2f}")
    print(f"SO2  : {state.so2:.2f}")
    print(f"CO   : {state.co:.2f}")
    print(f"Wind : {state.wind_speed}")
    print(f"Rain : {state.precipitation}")
    print(f"Temp : {state.temperature}")

def run_debug_simulation():

    state = TwinState(
    grid_id="test_cell_001",
    timestamp=datetime.now(),
    latitude=9.9312,
    longitude=76.2673,
    wind_direction=180,     # south wind

    pm25=120,
    pm10=140,
    no2=60,
    o3=40,
    so2=20,
    co=1.2,

    wind_speed=1.0,        # low wind
    precipitation=0.0,     # dry
    temperature=35.0,      # hot
    is_coastal=True
)


    print_state("INITIAL STATE", state)

    for hour in range(1, 7):
        print(f"\n================ HOUR {hour} ================")

        state, effects = update_state(state)

        print_state("UPDATED STATE", state)

        features = FeatureBuilder().build(state)
        result = evaluate_current_aqi(state, features)


        print("\nAQI REPORT")
        pprint(debug_aqi_view(result))

        print("\nEXPLANATION")
        print(explain_step(state))


# Entry point
if __name__ == "__main__":
    run_debug_simulation()
