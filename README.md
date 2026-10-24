GeoAI Outdoor Activity Assistant

An AI-powered assistant developed for the GeoAI Hackathon @ CSRE, IIT Bombay.

The system recommends suitable nearby outdoor places for activities such as running, cycling, cricket, football, tennis, hiking, picnics, outdoor events, and photography using live geospatial and weather information.

Features



Understands natural-language outdoor activity queries.

Supports 10 outdoor activities.

Finds nearby places using OpenStreetMap data.

Uses live weather information from Open-Meteo.

Checks temperature, precipitation, and wind conditions.

Ranks nearby places based on activity suitability and distance.

Uses an open-weight Small Language Model (SLM) for query understanding.

Provides recommendations through a Streamlit interface.



Supported Activities



Running / Jogging

Cycling

Golf

Cricket

Outdoor Football / Five-a-side

Outdoor Tennis

Hiking / Nature Walk

Picnic / Park Outing

Outdoor Event / Gathering

Outdoor Photography



Technology Stack



Python

Streamlit

PyDeck

Plotly

Pandas

Requests

PyTorch

Hugging Face Transformers

SmolLM2-1.7B-Instruct

OpenStreetMap / Overpass API

Open-Meteo



Project Structure

geoai-hackathon/

├── app.py

├── main.py

├── query\_service.py

├── slm\_service.py

├── data\_service.py

├── recommendation\_service.py

├── activity\_rules.py

├── requirements.txt

└── README.md



How It Works

User Query

&#x20;   ↓

Query Understanding

&#x20;   ↓

Live Geospatial Data + Weather

&#x20;   ↓

Activity Suitability Analysis

&#x20;   ↓

Place Ranking

&#x20;   ↓

Outdoor Recommendation



Running Locally

Install the required Python packages:

pip install -r requirements.txt



Run the Streamlit application:

streamlit run app.py



Data Sources

OpenStreetMap

Nearby places are retrieved using OpenStreetMap data through the Overpass API.

Attribution:

© OpenStreetMap contributors

Open-Meteo

Weather and air-quality information is retrieved from Open-Meteo.

Language Model

The project uses:

HuggingFaceTB/SmolLM2-1.7B-Instruct

The model is an open-weight Small Language Model used for understanding the user's activity and location query.

Important Note

Recommendations are generated from live API data available at runtime. The system does not intentionally hard-code weather conditions or place recommendations.

Team

Developed as a team project for the GeoAI Hackathon @ CSRE, IIT Bombay.

License

MIT License



