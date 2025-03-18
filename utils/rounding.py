# utils/rounding.py

def round_to_nearest_100(price):
    """Rounds price to the nearest 100."""
    return round(price / 100) * 100

def round_to_nearest_50(price):
    """Rounds price to the nearest 50."""
    return round(price / 50) * 50
