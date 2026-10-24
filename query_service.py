
import re


ACTIVITY_KEYWORDS = {
    "running": ["running", "run", "jogging", "jog"],
    "cycling": ["cycling", "cycle", "biking", "bike"],
    "golf": ["golf"],
    "cricket": ["cricket"],
    "football": ["football", "soccer"],
    "tennis": ["tennis"],
    "hiking": ["hiking", "hike", "nature walk", "trail walk", "trekking"],
    "picnic": ["picnic"],
    "outdoor_event": ["outdoor event", "outdoor gathering"],
    "outdoor_photography": [
        "outdoor photography",
        "nature photography"
    ]
}


TIME_PHRASES = [
    "tomorrow morning",
    "tomorrow afternoon",
    "tomorrow evening",
    "early morning",
    "this morning",
    "this afternoon",
    "this evening",
    "this weekend",
    "next weekend",
    "tomorrow",
    "tonight",
    "today",
    "morning",
    "afternoon",
    "evening",
    "night",
    "weekend"
]


def parse_query(query):
    """Extract basic activity details from a user's query."""

    text = query.lower().strip()

    # 1. Identify the activity using whole-word matching
    activity = None

    for activity_name, keywords in ACTIVITY_KEYWORDS.items():
        for keyword in sorted(keywords, key=len, reverse=True):
            pattern = r"\b" + re.escape(keyword) + r"\b"

            if re.search(pattern, text):
                activity = activity_name
                break

        if activity is not None:
            break

    # 2. Extract search radius in kilometres
    radius_match = re.search(
        r"\b(?:within|under|below|less than)\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(?:km|kilometers?|kilometres?)\b",
        text
    )

    radius_km = (
        float(radius_match.group(1))
        if radius_match
        else None
    )

    # 3. Extract time or date phrase
    time_range = None

    for phrase in sorted(TIME_PHRASES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(phrase) + r"\b", text):
            time_range = phrase
            break

    # 4. Extract a location after "near" or "in"
    stop_pattern = (
        r"\b(?:within|under|below|less than)\s+\d+(?:\.\d+)?\s*"
        r"(?:km|kilometers?|kilometres?|miles?|mi)\b"
        r"|\b(?:tomorrow|today|tonight|this weekend|next weekend|"
        r"this morning|this afternoon|this evening|"
        r"early morning|morning|afternoon|evening|night|weekend)\b"
    )

    near_match = re.search(r"\bnear\s+(.+)", query, re.IGNORECASE)

    if near_match:
        candidate = near_match.group(1)
    else:
        in_match = re.search(r"\bin\s+(.+)", query, re.IGNORECASE)

        if in_match:
            candidate = in_match.group(1)
        else:
            candidate = None

    location = None

    if candidate:
        candidate = re.split(
            stop_pattern,
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0]

        candidate = re.sub(r"[,.!?;:]+$", "", candidate).strip()

        generic_locations = {
            "a park",
            "the park",
            "a place",
            "a location",
            "an area",
            "somewhere",
            "outdoors",
            "the area",
            "a nearby place"
        }

        if candidate and candidate.lower() not in generic_locations:
            location = candidate

    # 5. Identify information that is missing
    missing_information = []

    if activity is None:
        missing_information.append("activity")

    # 6. Return the structured query
    return {
        "activity": activity,
        "location": location,
        "radius_km": radius_km,
        "time_range": time_range,
        "constraints": {},
        "missing_information": missing_information
    }


# Run sample queries when this file is executed directly
if __name__ == "__main__":

    test_queries = [
        "Find a park for running near Visakhapatnam within 5 km this evening",
        "Suggest something outdoors",
        "I want to go cycling near MVP Colony",
        "Find a place for cricket tomorrow",
        "Suggest an outdoor activity within 3 km",
        "Find a place for a picnic in Visakhapatnam this weekend",
        "I want to go hiking",
        "Find tennis courts within 2 km"
    ]

    for index, example_query in enumerate(test_queries, start=1):
        print("\n" + "=" * 55)
        print(f"TEST {index}: {example_query}")
        print("=" * 55)

        result = parse_query(example_query)
        print("Parsed:", result)
