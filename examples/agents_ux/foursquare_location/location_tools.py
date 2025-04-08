# Constants
import os
from urllib.parse import urlencode

import geocoder
import httpx
from function_calls import bedrock_agent_tool, get_bedrock_tools
import json

FSQ_PLACES_API_BASE = "https://places-api.foursquare.com"

FSQ_SERVICE_TOKEN = os.getenv("FOURSQUARE_SERVICE_TOKEN")

def submit_request(endpoint: str, params: dict[str, str]) -> str:
    headers = {
        "Authorization": f"Bearer {FSQ_SERVICE_TOKEN}",
        "X-Places-Api-Version": "2025-02-05"
    }
    encoded_params = urlencode(params)
    url = f"{FSQ_PLACES_API_BASE}{endpoint}?{encoded_params}"
    with httpx.Client() as client:
        try:
            print(url)
            response = client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.text, None
        except Exception as e:
            return "null", str(e)
            #return "Lake Washington Park; Summit at Snoqualmie Skiing; Rocket Bowling", None

@bedrock_agent_tool(action_group="LocationToolsActionGroup")
def search_near(what: str, where: str=None, ll: str=None, radius: int=1600) -> str:
    """Search for places near a particular named region or point. Either the
    region must be specified with the near parameter, or a circle around a point
    must be specified with the ll and radius parameters.

    Call with either where or ll/radius, but not both.

    Args:
        what: concept you are looking for (e.g., coffee shop, Hard Rock Cafe)
        where: a geographic region (e.g., Los Angeles or Fort Greene), this must be a named region.
        ll: comma separate latitude and longitude pair (e.g., 40.74,-74.0)
        radius: radius in meters around the point specified by ll
    """
    params = {
        "query": what,
        "fields": "fsq_place_id,name,location,latitude,longitude,distance,description,hours,hours_popular,price,tips,tastes",
        "limit": 5,
    }
    if where:
        params["near"] = where
    if ll:
        params["ll"] = ll
        params["radius"] = radius

    return submit_request("/places/search", params)

@bedrock_agent_tool(action_group="LocationToolsActionGroup")
def get_location() -> str:
    """Get user's location. Returns latitude and longitude, or else reports it could not find location. Tries to guess user's location
      based on ip address. Useful if the user has not provided their own precise location.

    """

    location = geocoder.ip('me')

    if not location.ok:
        return "I don't know where you are"

    return f"{location.lat},{location.lng} (using geoip, so this is an approximation)"

@bedrock_agent_tool(action_group="LocationToolsActionGroup")
def place_from_latitude_and_longitude(ll: str) -> str:
    """Get the most likely place the user is at based on their reported location. This returns the geographic
    area by name.
    Args:
        ll: comma separate latitude and longitude pair (e.g., 40.74,-74.0)
    """
    params = {
        "ll": ll,
        "limit": 1
    }
    return submit_request("/geotagging/candidates", params)


@bedrock_agent_tool(action_group="LocationToolsActionGroup")
def place_details(fsq_place_id: str) -> str:
    """
        Get detailed information about a place based on the fsq_id (foursquare id), including:
       description, phone, website, social media, hours, popular hours, rating (out of 10),
       price, menu, top photos, top tips (reviews from users), top tastes, and attributes
       such as takes reservations.
    Args:
        fsq_place_id: foursquare id (foursquare id) of the place which is returned from search_near.

    """

    params = {
      "fields": "description,tel,website,social_media,hours,hours_popular,rating,price,menu,photos,tips,tastes,attributes"
    }

    return submit_request(f"/places/{fsq_place_id}", params)



if __name__ == "__main__":
    print(search_near("Italian Restaurants", "Seattle"))