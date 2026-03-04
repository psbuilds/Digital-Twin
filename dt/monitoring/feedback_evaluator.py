from statistics import mean


class FeedbackEvaluator:
    def __init__(self):
        self.ratings = []

    def add_feedback(self, rating: int):
        if rating not in (-1, 0, 1):
            raise ValueError("Invalid rating")
        self.ratings.append(rating)

    def summary(self):
        if not self.ratings:
            return {"health": "unknown"}
        avg = mean(self.ratings)
        return {
            "count": len(self.ratings),
            "average": round(avg, 2),
            "health": "healthy" if avg > 0.3 else "degrading" if avg < -0.3 else "unstable"
        }
