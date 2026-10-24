import requests
import time
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "GeoAIHackathonOutdoorAssistant/1.0"
}


def current_timestamp():
    return datetime.now(timezone.utc).isoformat()


def get_coordinates(place):
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place,
        "format": "json",
        "limit": 1
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        results = response.json()

        if not results:
            return {
                "success": False,
                "error": "Place not found"
            }

        return {
            "success": True,
            "place": results[0]["display_name"],
            "latitude": float(results[0]["lat"]),
            "longitude": float(results[0]["lon"])
        }

    except (requests.RequestException, ValueError) as error:
        return {
            "success": False,
            "error": str(error)
        }




def get_nearby_places(latitude, longitude, radius=1000):
    urls = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    ]

    query = f"""
    [out:json][timeout:25];
    (
      node["leisure"="park"](around:{radius},{latitude},{longitude});
      way["leisure"="park"](around:{radius},{latitude},{longitude});
      relation["leisure"="park"](around:{radius},{latitude},{longitude});

      node["leisure"="garden"](around:{radius},{latitude},{longitude});
      way["leisure"="garden"](around:{radius},{latitude},{longitude});
      relation["leisure"="garden"](around:{radius},{latitude},{longitude});
    );
    out center tags;
    """

    errors = []

    for url in urls:
        print(f"Trying nearby-place service: {url}")

        try:
            response = None

            for attempt in range(2):
                try:
                    response = requests.post(
                        url,
                        data={"data": query},
                        headers=HEADERS,
                        timeout=45
                    )
                    response.raise_for_status()
                    break

                except requests.RequestException:
                    if attempt == 1:
                        raise

                    print("Retrying in 2 seconds...")
                    time.sleep(2)

            elements = response.json().get("elements", [])
            places = []

            for item in elements:
                tags = item.get("tags", {})
                center = item.get("center", {})

                place_lat = item.get("lat", center.get("lat"))
                place_lon = item.get("lon", center.get("lon"))

                if place_lat is None or place_lon is None:
                    continue

                places.append({
                    "name": tags.get(
                        "name", "Unnamed park or garden"
                    ),
                    "type": tags.get("leisure"),
                    "latitude": place_lat,
                    "longitude": place_lon
                })

            return {
                "success": True,
                "count": len(places),
                "places": places,
                "source": "OpenStreetMap"
            }

        except (requests.RequestException, ValueError) as error:
            errors.append(f"{url}: {error}")
            print(f"Service failed: {error}")

    return {
        "success": False,
        "error": "All nearby-place services failed. "
                 + " | ".join(errors),
        "count": 0,
        "places": [],
        "source": "OpenStreetMap"
    }




def get_weather(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,"
            "apparent_temperature,precipitation,"
            "weather_code,wind_speed_10m"
        ),
        "daily": (
            "temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max"
        ),
        "timezone": "auto",
        "forecast_days": 1
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "current": data.get("current", {}),
            "daily": data.get("daily", {}),
            "source": "Open-Meteo"
        }

    except (requests.RequestException, ValueError) as error:
        return {
            "success": False,
            "error": str(error),
            "current": {},
            "daily": {},
            "source": "Open-Meteo"
        }

def get_air_quality(latitude, longitude):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "pm10,pm2_5,us_aqi,european_aqi",
        "timezone": "auto"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "current": data.get("current", {}),
            "source": "Open-Meteo Air Quality API"
        }

    except (requests.RequestException, ValueError) as error:
        return {
            "success": False,
            "error": str(error),
            "current": {},
            "source": "Open-Meteo Air Quality API"
        }




if __name__ == "__main__":
    import json

    print("GeoAI Data Service started!")
    print("Current UTC time:", current_timestamp())

    location = get_coordinates("Rajahmundry, India")

    if location["success"]:
        latitude = location["latitude"]
        longitude = location["longitude"]

        weather = get_weather(latitude, longitude)
        air_quality = get_air_quality(latitude, longitude)

        # The parks server timed out in earlier tests.
        # Keep the failure visible instead of inventing results.
        places_result = {
            "success": False,
            "count": 0,
            "places": [],
            "source": "OpenStreetMap",
            "error": "Nearby parks unavailable: Overpass server timed out in previous tests"
        }

        output = {
            "location": {
                "name": location["place"],
                "latitude": latitude,
                "longitude": longitude
            },
            "places": places_result["places"],
            "weather_by_place": [
                {
                    "place": location["place"],
                    **weather
                }
            ],
            "air_quality_by_place": [
                {
                    "place": location["place"],
                    **air_quality
                }
            ],
            "sources": [
                "Nominatim",
                "OpenStreetMap",
                "Open-Meteo",
                "Open-Meteo Air Quality API"
            ],
            "retrieved_at": current_timestamp()
        }

        if not weather["success"]:
            output["weather_by_place"][0]["error"] = weather["error"]

        if not air_quality["success"]:
            output["air_quality_by_place"][0]["error"] = air_quality["error"]

        print("\nCombined JSON output:")
        print(json.dumps(output, indent=4, ensure_ascii=False))

        if not places_result["success"]:
            print("\nParks status:", places_result["error"])

    else:
        print("Could not find the location.")
        print("Error:", location.get("error", "Unknown error"))