from statistics import mean, stdev


class DriftDetector:
    def __init__(self, z_threshold=3.0):
        self.z_threshold = z_threshold

    def detect(self, baseline, recent):
        mu, sigma = mean(baseline), stdev(baseline)
        z_scores = [(x - mu) / sigma for x in recent]
        max_z = max(abs(z) for z in z_scores)
        return {"drift": max_z > self.z_threshold, "max_z": round(max_z, 2)}
