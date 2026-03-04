from datetime import datetime,UTC
from dt.ingestion.state_deriver import derive_twin_state
from dt.engine.state_updater import update_state
from dt.rules.current_aqi_rules import evaluate_current_aqi
from dt.forecasting.prediction_orchestrator import PredictionOrchestrator
from dt.monitoring.feedback_evaluator import FeedbackEvaluator


def test_dt_end_to_end():
    raw = {
        "grid_id": "kochi",
        "time": datetime.now(UTC),
        "lat": 9.93,
        "lon": 76.26,
        "u10": 2.0,
        "v10": -1.0,
        "t2m": 303.15,
        "tp": 0.0002,
        "pm2p5": 80,
        "pm10": 130,
        "no2": 45,
        "o3": 60,
        "so2": 10,
        "co": 0.9,
    }

    state = derive_twin_state(raw)
    next_state = update_state(state)

    aqi = evaluate_current_aqi(next_state)
    assert aqi > 0

    preds = PredictionOrchestrator().predict([
        {"value": 140},
        {"value": 160},
        {"value": aqi},
    ])
    assert len(preds) == 3

    fb = FeedbackEvaluator()
    fb.add_feedback(1)
    fb.add_feedback(0)
    assert fb.summary()["count"] == 2
