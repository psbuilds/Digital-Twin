from statistics import mean


class PredictionOrchestrator:
    def __init__(self, horizon=3):
        self.horizon = horizon

    def predict(self, history):
        values = [h["value"] for h in history]
        delta = mean(values[i+1] - values[i] for i in range(len(values)-1))

        preds = []
        current = values[-1]
        for _ in range(self.horizon):
            current = max(0, current + delta)
            preds.append(round(current, 2))
        return preds
