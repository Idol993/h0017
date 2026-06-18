from datetime import datetime, timedelta


def calculate_next_interval(card, rating: int) -> dict:
    strength = card.memory_strength or 2.5
    consecutive = card.consecutive_correct or 0
    prev_interval = card.interval_days or 0

    if rating == 1:
        new_interval = 1
        new_consecutive = 0
        new_strength = max(1.3, strength - 0.2)
    elif rating == 2:
        new_interval = 1
        new_consecutive = 0
        new_strength = max(1.3, strength - 0.1)
    elif rating == 3:
        if consecutive == 0:
            new_interval = 1
        else:
            new_interval = max(1, int(prev_interval * 0.8))
        new_consecutive = consecutive
        new_strength = strength
    elif rating == 4:
        new_consecutive = consecutive + 1
        if new_consecutive == 1:
            new_interval = 1
        elif new_consecutive == 2:
            new_interval = 6
        else:
            new_interval = int(prev_interval * strength * 0.8)
        new_strength = min(3.0, strength + 0.05)
    elif rating == 5:
        new_consecutive = consecutive + 1
        if new_consecutive == 1:
            new_interval = 1
        elif new_consecutive == 2:
            new_interval = 6
        else:
            new_interval = int(prev_interval * strength)
        new_strength = min(3.0, strength + 0.1)
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
