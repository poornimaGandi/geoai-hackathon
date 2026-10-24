
ACTIVITY_RULES = {
    "running": {
        "place_keywords": ["park", "track", "sports_centre", "pitch"],
        "ideal_temp": (10, 28),
        "max_rain": 0.5,
        "max_wind": 30
    },
    "cycling": {
        "place_keywords": ["cycleway", "park", "track", "path"],
        "ideal_temp": (10, 28),
        "max_rain": 0.5,
        "max_wind": 25
    },
    "golf": {
        "place_keywords": ["golf"],
        "ideal_temp": (10, 30),
        "max_rain": 0.5,
        "max_wind": 30
    },
    "cricket": {
        "place_keywords": ["cricket", "sports_centre", "pitch", "stadium"],
        "ideal_temp": (15, 32),
        "max_rain": 0.5,
        "max_wind": 30
    },
    "outdoor_football": {
        "place_keywords": ["soccer", "football", "pitch", "sports_centre"],
        "ideal_temp": (10, 30),
        "max_rain": 0.5,
        "max_wind": 35
    },
    "outdoor_tennis": {
        "place_keywords": ["tennis", "sports_centre"],
        "ideal_temp": (10, 30),
        "max_rain": 0.5,
        "max_wind": 25
    },
    "hiking": {
        "place_keywords": ["hiking", "footway", "path", "trail", "nature_reserve"],
        "ideal_temp": (8, 28),
        "max_rain": 0.5,
        "max_wind": 35
    },
    "picnic": {
        "place_keywords": ["park", "garden", "picnic", "recreation_ground"],
        "ideal_temp": (15, 30),
        "max_rain": 0.2,
        "max_wind": 25
    },
    "outdoor_event": {
        "place_keywords": ["park", "event_venue", "stadium", "amphitheatre"],
        "ideal_temp": (15, 30),
        "max_rain": 0.2,
        "max_wind": 30
    },
    "outdoor_photography": {
        "place_keywords": ["viewpoint", "park", "garden", "nature_reserve", "beach"],
        "ideal_temp": (5, 35),
        "max_rain": 0.5,
        "max_wind": 35
    }
}
print("Activity rules loaded successfully!")
print("Number of activities:", len(ACTIVITY_RULES))