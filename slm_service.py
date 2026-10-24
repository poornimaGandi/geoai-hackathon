
import json
import re
from functools import lru_cache
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# --------------------------------------------------
# 1. MODEL CONFIGURATION
# --------------------------------------------------

MODEL_NAME = "HuggingFaceTB/SmolLM2-1.7B-Instruct"

tokenizer = None
model = None


# --------------------------------------------------
# 2. SUPPORTED ACTIVITIES
# --------------------------------------------------

ACTIVITIES = {
    "running": ["running", "run", "jogging", "jog"],
    "cycling": ["cycling", "cycle", "biking", "bike"],
    "golf": ["golf"],
    "cricket": ["cricket"],
    "football": ["football", "soccer"],
    "tennis": ["tennis"],
    "hiking": ["hiking", "hike", "trekking", "trek"],
    "picnic": ["picnic"],
    "outdoor_event": ["outdoor event", "outdoor events"],
    "outdoor_photography": [
        "outdoor photography",
        "nature photography"
    ]
}


# --------------------------------------------------
# 3. TIME PHRASES
# --------------------------------------------------

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


# --------------------------------------------------
# 4. LOAD THE SLM MODEL
# --------------------------------------------------

@lru_cache(maxsize=1)
def load_model():
    print("Loading SLM tokenizer...")
    loaded_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print("Loading SLM model...")
    loaded_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32
    )

    loaded_model.eval()
    print("SLM loaded successfully!\n")

    return loaded_tokenizer, loaded_model

# --------------------------------------------------
# 5. FIND ACTIVITY FROM THE USER'S ACTUAL QUERY
# --------------------------------------------------

def find_activity(query):
    text = query.lower()

    # Check longer activity phrases before shorter ones.
    for activity, keywords in ACTIVITIES.items():
        for keyword in sorted(keywords, key=len, reverse=True):
            pattern = r"\b" + re.escape(keyword) + r"\b"

            if re.search(pattern, text):
                return activity

    # Do not guess an activity if the user did not specify one.
    return None


# --------------------------------------------------
# 6. FIND DISTANCE / RADIUS
# --------------------------------------------------

def find_radius(query):
    patterns = [
        r"\bwithin\s+(\d+(?:\.\d+)?)\s*(?:km|kilometers?|kilometres?)\b",
        r"\b(?:under|below|less than)\s+(\d+(?:\.\d+)?)\s*(?:km|kilometers?|kilometres?)\b",
        r"\bwithin\s+(\d+(?:\.\d+)?)\s*(?:miles?|mi)\b"
    ]

    text = query.lower()

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            distance = float(match.group(1))

            if "mile" in match.group(0) or re.search(
                r"\bmi\b", match.group(0)
            ):
                distance *= 1.60934

            return round(distance, 2)

    return None


# --------------------------------------------------
# 7. FIND TIME FROM THE USER'S ACTUAL QUERY
# --------------------------------------------------

def find_time(query):
    text = query.lower()

    for phrase in sorted(TIME_PHRASES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(phrase) + r"\b", text):
            return phrase

    return None


# --------------------------------------------------
# 8. FIND LOCATION
# --------------------------------------------------

def find_location(query):
    text = query.strip()

    stop_pattern = (
        r"\b(?:within|under|below|less than)\s+\d+(?:\.\d+)?\s*"
        r"(?:km|kilometers?|kilometres?|miles?|mi)\b"
        r"|\b(?:tomorrow|today|tonight|this weekend|next weekend|"
        r"this morning|this afternoon|this evening|"
        r"morning|afternoon|evening|night|weekend)\b"
    )

    # Check "near" first so the activity description is not
    # incorrectly extracted as the location.
    near_match = re.search(r"\bnear\s+(.+)", text, re.IGNORECASE)

    if near_match:
        candidate = near_match.group(1)
    else:
        in_match = re.search(r"\bin\s+(.+)", text, re.IGNORECASE)

        if not in_match:
            return None

        candidate = in_match.group(1)

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
        "a nearby place",
        "somewhere",
        "outdoors",
        "the area"
    }

    if not candidate or candidate.lower() in generic_locations:
        return None

    candidate = re.sub(
        r"^(?:the city of|the area of)\s+",
        "",
        candidate,
        flags=re.IGNORECASE
    ).strip()

    return candidate or None


# --------------------------------------------------
# 9. SAFELY READ JSON FROM THE SLM
# --------------------------------------------------

def parse_model_json(raw_output):
    if not raw_output:
        return {}

    # Remove Markdown JSON fences if the model adds them.
    cleaned = re.sub(
        r"```(?:json)?",
        "",
        raw_output,
        flags=re.IGNORECASE
    ).replace("```", "").strip()

    # Extract the first JSON object if extra text is present.
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end < start:
        return {}

    cleaned = cleaned[start:end + 1]

    try:
        result = json.loads(cleaned)

        if isinstance(result, dict):
            return result

    except (json.JSONDecodeError, TypeError):
        pass

    return {}


# --------------------------------------------------
# 10. NORMALIZE AND VALIDATE THE RESULT
# --------------------------------------------------

def normalize_result(result, query):
    if not isinstance(result, dict):
        result = {}

    # The original query is the source of truth.
    activity = find_activity(query)
    location = find_location(query)
    radius_km = find_radius(query)
    time_range = find_time(query)

    # Do not accept invented weather, temperature, or distance
    # preferences from the model.
    constraints = {}

    # Only ask for the activity if it is not specified.
    missing_information = []

    if activity is None:
        missing_information.append("activity")

    return {
        "activity": activity,
        "location": location,
        "radius_km": radius_km,
        "time_range": time_range,
        "constraints": constraints,
        "missing_information": missing_information
    }


# --------------------------------------------------
# 11. EXTRACT QUERY DETAILS USING THE SLM
# --------------------------------------------------

def extract_query_details(query):
    global tokenizer, model
    tokenizer, model = load_model()

    prompt = f"""You extract information from outdoor activity requests.

Return one JSON object with these keys:
activity, location, radius_km, time_range, constraints,
missing_information.

Use null when information is not provided.
Do not invent locations, distances, times, or preferences.
Supported activities: running, cycling, golf, cricket,
football, tennis, hiking, picnic, outdoor_event,
outdoor_photography.

User request: {query}

JSON response:"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        )

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=180,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )

        # Decode only the newly generated tokens.
        # FIX: Use inputs["input_ids"], not undefined input_ids.
        new_tokens = output_ids[0][
            inputs["input_ids"].shape[-1]:
        ]

        raw_output = tokenizer.decode(
            new_tokens,
            skip_special_tokens=True
        )

        print("\nRaw SLM output:")
        print(raw_output)

        parsed_result = parse_model_json(raw_output)

        if not parsed_result:
            print("Warning: invalid model JSON; using safe defaults.")

    except Exception as error:
        print("Warning: SLM generation failed:")
        print(repr(error))
        parsed_result = {}

    # Always validate using the user's original query.
    result = normalize_result(parsed_result, query)

    return result


# --------------------------------------------------
# 12. TEST WITH EIGHT EXAMPLE QUERIES
# --------------------------------------------------

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

    for index, query in enumerate(test_queries, start=1):
        print("\n" + "=" * 60)
        print(f"TEST {index} OF {len(test_queries)}")
        print("User query:", query)
        print("=" * 60)

        try:
            result = extract_query_details(query)

            print("\nCorrected query details:")
            print(json.dumps(result, indent=2))

        except Exception as error:
            print("\nTest failed:")
            print(type(error).__name__ + ":", str(error))
