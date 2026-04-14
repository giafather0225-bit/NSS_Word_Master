"""SM-2 Spaced Repetition Algorithm for NSS Word Master."""

from datetime import date, timedelta


def sm2_calculate(quality: int, repetitions: int, easiness: float, interval: int):
    """Run one SM-2 review cycle."""
    if quality < 0 or quality > 5:
        quality = max(0, min(5, quality))

    new_easiness = easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_easiness = max(1.3, new_easiness)

    if quality < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = max(1, round(interval * new_easiness))
        new_repetitions = repetitions + 1

    next_review = date.today() + timedelta(days=new_interval)
    return new_repetitions, new_easiness, new_interval, next_review


def quality_from_result(is_correct: bool, attempts: int = 1) -> int:
    """Convert quiz result into SM-2 quality score (0-5)."""
    if not is_correct:
        return 1
    if attempts <= 1:
        return 5
    elif attempts == 2:
        return 4
    else:
        return 3
