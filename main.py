
from query_service import parse_query
from data_service import (
    get_coordinates,
    get_nearby_places,
    get_weather,
)
from recommendation_service import (
    check_weather_suitability,
    recommend_and_rank,
    calculate_distance_km,
)

DEFAULT_RADIUS_KM = 5

ACTIVITY_MAP = {
    "football": "outdoor_football",
    "tennis": "outdoor_tennis",
}



def run_assistant(user_query):
    """Run GeoAI and return structured results for the frontend."""

    print("\n" + "=" * 50)
    print("GeoAI Outdoor Activity Assistant")
    print("=" * 50)

    # 1. Understand the user's query.
    parsed = parse_query(user_query)

    try:
        from slm_service import extract_query_details

        slm_parsed = extract_query_details(user_query)

        if isinstance(slm_parsed, dict):
            for key in (
                "activity", "location", "radius_km", "time_range"
            ):
                if slm_parsed.get(key) is not None:
                    parsed[key] = slm_parsed[key]

    except Exception as error:
        print("SLM unavailable; using rule-based parser.")
        print("Reason:", str(error))

    activity = parsed.get("activity")
    location_name = parsed.get("location")
    radius_km = parsed.get("radius_km") or DEFAULT_RADIUS_KM

    if not activity:
        return {
            "success": False,
            "error": "Please specify an outdoor activity."
        }

    if not location_name:
        return {
            "success": False,
            "error": "Please specify a location."
        }

    activity = ACTIVITY_MAP.get(activity, activity)

    # 2. Find the location coordinates.
    location = get_coordinates(location_name)

    if not location.get("success"):
        return {
            "success": False,
            "error": location.get("error", "Location lookup failed.")
        }

    latitude = location["latitude"]
    longitude = location["longitude"]

    # 3. Retrieve nearby places.
    places_result = get_nearby_places(
        latitude,
        longitude,
        radius=int(radius_km * 1000),
    )

    if not places_result.get("success"):
        return {
            "success": False,
            "error": places_result.get(
                "error", "Nearby-place lookup failed."
            )
        }

    places = places_result.get("places", [])

    # 4. Retrieve current weather.
    weather_result = get_weather(latitude, longitude)

    if not weather_result.get("success"):
        return {
            "success": False,
            "error": weather_result.get(
                "error", "Weather lookup failed."
            )
        }

    current = weather_result.get("current", {})

    temperature = current.get("temperature_2m")
    rain = current.get("precipitation")
    wind = current.get("wind_speed_10m")

    if any(v is None for v in (temperature, rain, wind)):
        return {
            "success": False,
            "error": "Weather data is incomplete."
        }

    # 5. Check weather suitability.
    suitability = check_weather_suitability(
        activity, temperature, rain, wind
    )

    # 6. Keep places inside the requested radius.
    places_in_radius = []

    for place in places:
        place_lat = place.get("latitude")
        place_lon = place.get("longitude")

        if place_lat is None or place_lon is None:
            continue

        distance = calculate_distance_km(
            latitude,
            longitude,
            float(place_lat),
            float(place_lon),
        )

        if distance <= radius_km:
            places_in_radius.append(place)

    # 7. Rank places for the selected activity.
    ranked = []

    if places_in_radius:
        ranking_result = recommend_and_rank(
            places_in_radius,
            activity,
            temperature,
            rain,
            wind,
            latitude,
            longitude,
        )

        ranked = ranking_result.get("recommended_places", [])
        suitability = ranking_result.get("status", suitability)

    # 8. Prepare actual place details for Streamlit.
    frontend_places = []

    for item in ranked:
        details = item.get("details", item)

        place_lat = details.get("latitude")
        place_lon = details.get("longitude")

        if place_lat is None or place_lon is None:
            continue

        distance = calculate_distance_km(
            latitude,
            longitude,
            float(place_lat),
            float(place_lon),
        )

        frontend_places.append({
            "name": details.get("name", "Unnamed place"),
            "latitude": float(place_lat),
            "longitude": float(place_lon),
            "distance_km": round(distance, 2),
        })

    # 9. Return structured data for the frontend.
    result = {
        "success": True,
        "activity": activity,
        "location": location.get("place", location_name),
        "radius_km": radius_km,
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "weather": {
            "temperature": temperature,
            "rain": rain,
            "wind": wind,
        },
        "weather_status": suitability,
        "places": frontend_places,
    }

    print("\nSearch completed.")
    print("Weather suitability:", suitability)
    print("Places returned:", len(frontend_places))

    return result



if __name__ == "__main__":
    query = input(
        "\nEnter an activity and location "
        "(example: running near Rajamahendravaram within 5 km): "
    )

    run_assistant(query)
