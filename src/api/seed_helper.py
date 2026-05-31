from datetime import datetime, timedelta
import random

SAMPLE_OPTIONS = ["Option 1", "Option 2", "Option 3"]


def make_recommendation():
    opt = random.choice(SAMPLE_OPTIONS)
    return {
        "recommended_option": opt,
        "confidence_score": round(random.uniform(0.5, 0.95), 2),
        "reasoning": "Auto-generated recommendation for demo.",
        "cost_delta": random.randint(0, 20000),
        "risk_level": random.choice(["low", "medium", "high"]),
    }


def make_penalty():
    return {"total_penalty": random.randint(0, 50000)}
