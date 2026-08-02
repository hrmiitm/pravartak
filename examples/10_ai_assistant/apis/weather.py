"""
weather.py

Weather service using:

1. OpenStreetMap Nominatim
2. Open-Meteo

No LangChain code belongs here.
"""
WEATHER_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Snow",
    80: "Rain Showers",
    95: "Thunderstorm",
}

import httpx

from apis.exceptions import (
    CityNotFoundError,
)


GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


client = httpx.Client(
    timeout=10,
    headers={
        "User-Agent": "LangGraph-AI-Assistant/1.0"
    }
)


def geocode_city(city: str):
    """
    Convert a city name into latitude and longitude.
    """

    response = client.get(
        GEOCODE_URL,
        params={
            "q": city,
            "format": "json",
            "limit": 1,
        },
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        raise CityNotFoundError(
            f"City '{city}' not found."
        )

    return (
        float(data[0]["lat"]),
        float(data[0]["lon"]),
    )

def fetch_weather(latitude: float, longitude: float):
    """
    Fetch current weather from Open-Meteo.
    """

    response = client.get(
        WEATHER_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "wind_speed_10m",
                "weather_code",
            ],
        },
    )

    response.raise_for_status()

    return response.json()

def get_weather(city: str):
    """
    Complete weather pipeline.
    """

    latitude, longitude = geocode_city(city)

    data = fetch_weather(latitude, longitude)

    current = data["current"]

    return {
        "city": city.title(),
        "temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "condition": WEATHER_CODES.get(
            current["weather_code"],
            "Unknown",
        ),
    }