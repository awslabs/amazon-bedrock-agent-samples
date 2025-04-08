# Constants
import os

import httpx
from function_calls import bedrock_agent_tool, get_bedrock_tools
import json
import requests

WEATHER_API = "https://api.weather.gov"

API_EMAIL = os.getenv("WEATHER_API_EMAIL")

def submit_request(url: str) -> str:
    headers = {
        "User-Agent": API_EMAIL,
    }
    with httpx.Client() as client:
        try:
            print(url)
            response = client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(e)
            return "Could not retrieve weather data"

@bedrock_agent_tool(action_group="WeatherToolsActionGroup")
def get_weather(latitude: str, longitude:str) -> str:
    """Get the weather forecast for a point specified by latitude and longitude.

    Args:
        latitude: The latitude of the location in a string format (e.g., "40.74")
        longitude: The longitude of the location in a string format (e.g.,"-74.0")
    """

    # Step 1: Get the forecast grid endpoint for these coordinates
    response = requests.get(f"https://api.weather.gov/points/{latitude},{longitude}")
    response.raise_for_status()  # Raise an exception for HTTP errors

    data = response.json()

    # Step 2: Extract the forecast URL from the response
    forecast_url = data['properties']['forecast']
    print(f"Forecast URL: {forecast_url}")

    # Step 3: Fetch the actual forecast data
    forecast_response = requests.get(forecast_url)
    forecast_response.raise_for_status()

    forecast_data = forecast_response.json()
    detailed_forecasts = ""
    for entry in forecast_data["properties"]["periods"]:
        day_name = entry['name']
        forecast = entry['detailedForecast']
        detailed_forecasts += f"{day_name}: {forecast}\n"

    return detailed_forecasts
