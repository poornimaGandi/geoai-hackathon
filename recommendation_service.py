
from activity_rules import ACTIVITY_RULES




def matches_activity(place, activity):
    """Check whether a place matches the requested activity."""

    if activity not in ACTIVITY_RULES:
        return False

    rules = ACTIVITY_RULES[activity]
    keywords = [
        word.lower()
        for word in rules["place_keywords"]
    ]

    name = str(place.get("name", "")).strip().lower()
    category = str(place.get("category", "")).lower()
    place_type = str(place.get("type", "")).lower()

    # Reject places that are clearly not usable recommendations.
    excluded_terms = [
        "parking",
        "under preparation",
        "under construction",
        "proposed park",
    ]

    if any(term in name for term in excluded_terms):
        return False

    tags = place.get("tags", {})

    if isinstance(tags, dict):
        tag_text = " ".join(
            f"{key}={value}"
            for key, value in tags.items()
        ).lower()
    elif isinstance(tags, (list, tuple, set)):
        tag_text = " ".join(
            str(tag) for tag in tags
        ).lower()
    else:
        tag_text = str(tags).lower()

    specific_terms = {
        "running": ["sport=running", "sport=jogging"],
        "cycling": ["sport=cycling", "sport=mountain_biking"],
        "golf": ["sport=golf"],
        "cricket": ["sport=cricket"],
        "outdoor_football": ["sport=football", "sport=soccer"],
        "outdoor_tennis": ["sport=tennis"],
        "hiking": ["sport=hiking", "route=hiking"],
    }

    terms = specific_terms.get(activity, [])

    other_sports = [
        "sport=cricket",
        "sport=tennis",
        "sport=football",
        "sport=soccer",
        "sport=golf",
        "sport=running",
        "sport=cycling",
        "sport=hiking",
    ]

    # Reject places explicitly tagged for a different sport.
    for term in other_sports:
        if term in tag_text and term not in terms:
            return False

    # Prefer explicit matching activity tags.
    if any(term in tag_text for term in terms):
        return True

    # Do not recommend a completely unnamed place without
    # evidence that it is a relevant park or sports facility.
    if not name and not category and not place_type:
        return False

    searchable_text = f"{name} {category} {place_type}"

    return any(
        keyword in searchable_text
        for keyword in keywords
    )



def check_weather_suitability(activity, temperature, rain, wind):

    """Check whether weather meets the activity's prototype rules."""

    if activity not in ACTIVITY_RULES:
        return "Unknown activity"

    if temperature is None or rain is None or wind is None:
        return "Weather data unavailable"

    rules = ACTIVITY_RULES[activity]
    min_temp, max_temp = rules["ideal_temp"]

    if temperature < min_temp or temperature > max_temp:
        return "Not ideal: temperature"

    if rain > rules["max_rain"]:
        return "Not ideal: rain"

    if wind > rules["max_wind"]:
        return "Not ideal: wind"

    return "Suitable"

def recommend_places(places, activity, temperature, rain, wind):
    """Return places matching the activity and weather conditions."""

    weather_result = check_weather_suitability(
        activity, temperature, rain, wind
    )

    if weather_result != "Suitable":
        return {
            "status": weather_result,
            "recommended_places": []
        }

    recommended = []

    for place in places:
        if matches_activity(place, activity):
            recommended.append(place)

    return {
        "status": "Suitable",
        "recommended_places": recommended
    }


def rank_places(places, activity, reference_lat=None, reference_lon=None):
    """Rank matching places by relevance, information, and distance."""

    ranked_places = []

    for place in places:
        if not matches_activity(place, activity):
            continue

        name = str(place.get("name", "")).strip()
        tags = place.get("tags", {})

        # Start with a basic activity match score.
        score = 1

        # Prefer places with a meaningful name.
        if name and not name.lower().startswith("unnamed"):
            score += 2

        # Prefer places with useful map tags.
        if tags:
            score += 1

        # Calculate distance when reference coordinates are available.
        distance_km = None
        place_lat = place.get("latitude")
        place_lon = place.get("longitude")

        if (
            reference_lat is not None
            and reference_lon is not None
            and place_lat is not None
            and place_lon is not None
        ):
            distance_km = calculate_distance_km(
                reference_lat,
                reference_lon,
                float(place_lat),
                float(place_lon),
            )

        ranked_places.append({
            "name": name or "Unnamed place",
            "score": score,
            "distance_km": distance_km,
            "details": place,
        })

    # Rank by relevance score first, then by nearest distance.
    ranked_places.sort(
        key=lambda item: (
            -item["score"],
            item["distance_km"]
            if item["distance_km"] is not None
            else float("inf"),
        )
    )

    return ranked_places[:10]


from math import radians, sin, cos, sqrt, atan2
def recommend_and_rank(
    places,
    activity,
    temperature,
    rain,
    wind,
    reference_lat=None,
    reference_lon=None
):
    """Check weather and rank matching places."""

    weather_status = check_weather_suitability(
        activity,
        temperature,
        rain,
        wind
    )

    
    ranked_places = rank_places(
           places,
           activity,
           reference_lat,
           reference_lon,
    )

    return {
        "status": weather_status,
        "recommended_places": ranked_places
    }





def calculate_distance_km(lat1, lon1, lat2, lon2):
    """Calculate the approximate distance between two coordinates."""

    earth_radius_km = 6371

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    a = max(0, min(1, a))

    distance = 2 * earth_radius_km * atan2(
        sqrt(a), sqrt(1 - a)
    )

    return distance


def rank_places_by_distance(places, activity, user_lat, user_lon):
    """Rank matching places with nearer places first."""

    ranked_places = []

    for place in places:
        if not matches_activity(place, activity):
            continue

        if place.get("latitude") is None or place.get("longitude") is None:
            continue

        distance = calculate_distance_km(
            user_lat,
            user_lon,
            place["latitude"],
            place["longitude"]
        )

        ranked_places.append({
            "name": place.get("name", "Unknown place"),
            "distance_km": round(distance, 2),
            "details": place
        })

    ranked_places.sort(key=lambda item: item["distance_km"])

    return ranked_places







