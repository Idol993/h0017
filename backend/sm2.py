from datetime import datetime, timedelta


def calculate_next_interval(card, rating: int) -> dict:
    strength = card.memory_strength or 2.5
    consecutive = card.consecutive_correct or 0
    prev_interval = card.interval_days or 0

    if rating == 1:
        new_interval = 1
        new_consecutive = 0
        new_strength = max(1.3, round(strength - 0.2, 2))
    elif rating == 2:
        new_interval = 1
        new_consecutive = 0
        new_strength = max(1.3, round(strength - 0.1, 2))
    elif rating == 3:
        if consecutive == 0:
            new_interval = 1
        else:
            new_interval = max(1, int(prev_interval * 0.9))
        new_consecutive = consecutive
        new_strength = strength
    elif rating == 4:
        new_consecutive = consecutive + 1
        if new_consecutive == 1:
            new_interval = 1
        elif new_consecutive == 2:
            new_interval = 6
        else:
            multiplier = 1.3 + (strength - 1.3) / (3.0 - 1.3) * 0.4
            new_interval = max(1, int(prev_interval * multiplier))
        new_strength = min(3.0, round(strength + 0.05, 2))
    elif rating == 5:
        new_consecutive = consecutive + 1
        if new_consecutive == 1:
            new_interval = 1
        elif new_consecutive == 2:
            new_interval = 6
        else:
            multiplier = 1.5 + (strength - 1.3) / (3.0 - 1.3) * 0.5
            new_interval = max(1, int(prev_interval * multiplier))
        new_strength = min(3.0, round(strength + 0.1, 2))
    else:
        raise ValueError("Rating must be between 1 and 5")

    new_interval = min(new_interval, 30)

    now = datetime.now()
    next_review = now + timedelta(days=new_interval)

    return {
        "memory_strength": round(new_strength, 2),
        "consecutive_correct": new_consecutive,
        "interval_days": new_interval,
        "last_reviewed": now,
        "next_review": next_review,
    }
