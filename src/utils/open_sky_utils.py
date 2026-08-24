import math
import requests
from typing import cast

from geopy.location import Location
from geopy.geocoders import Nominatim

from utils.qt_utils import get_screen_geometry
from opensky_api import OpenSkyApi, OpenSkyStates, OpenSkyApi, TokenManager

import logging
logger = logging.getLogger(__name__)


def get_bbox_size(location_name:str, bbox_size:str, display_name:str|None) -> tuple[float, float, float, float]:
    """
    Get boundingbox for a given size ('small', 'medium', 'large').
    ratio of lat and lon is scaled to the geometry of the screen that's connected to displayName and also corrected for latitude
    """
    
    # Get the location using geopy
    geolocator:Nominatim = Nominatim(user_agent="OverFlight")
    location = cast(Location | None, geolocator.geocode(location_name))
        
    if location:
        latitude = location.latitude
        longitude= location.longitude
        logger.info(f"{location}\'s coordinates are: {location.latitude}, {location.longitude}")
    else:
        raise NameError("Location not found.")

    latitude_offsets = {"local": 0.05, "small": 0.10, "medium": 0.30, "large": 0.50, "veryLarge": 1, "huge": 2}
    
    if bbox_size in latitude_offsets.keys():
        latitude_offset = latitude_offsets[bbox_size]
    else:
        raise KeyError("The selected bboxSize is not \"small\", \"medium\", or \"large\"")
    
    
    # Use the selected screens' aspect ratio to set the boundingbox aspect ratio
    geom = get_screen_geometry(display_name)
    factor = geom.width() / geom.height()   
    
    longitude_offset = factor * latitude_offset / math.cos(math.radians(latitude))
    
    min_lat:float  = latitude - latitude_offset
    max_lat:float  = latitude + latitude_offset
    min_long:float = longitude - longitude_offset
    max_long:float = longitude + longitude_offset
    
    return (min_lat, max_lat, min_long, max_long)

def get_bbox_offset(location_name:str, latitude_offset:float, longitude_offset:float) -> tuple[float, float, float, float]:
    """
    Get boundingbox for given latitude and longitude offsets. Must be a positive, non-zero float 
    """
    
    assert latitude_offset > 0, "Offsets should both be posive, non-zero floats."
    assert longitude_offset > 0,"Offsets should both be posive, non-zero floats."

    # Get the location using geopy
    geolocator:Nominatim = Nominatim(user_agent="OverFlight")
    location = cast(Location | None, geolocator.geocode(location_name))
        
    if location:
        latitude = location.latitude
        longitude= location.longitude
        logger.info(f"{location}\'s coordinates are: {location.latitude}, {location.longitude}")
    else:
        raise NameError("Location not found.")

    min_lat:float  = latitude - latitude_offset
    max_lat:float  = latitude + latitude_offset
    min_long:float = longitude - longitude_offset
    max_long:float = longitude + longitude_offset
    
    return (min_lat, max_lat, min_long, max_long)


def get_states_in_bbox_and_credits(api:OpenSkyApi, bbox:tuple) -> tuple[OpenSkyStates|None, int]:
    
    tm = api._token_manager
    resp = None
    remaining_credits = -1

    # Copied code from the opensky_api.OpenSkyApi class. This allows us acces to the request headers.
    params = {"extended": True}

    if len(bbox) == 4:
        OpenSkyApi._check_lat(bbox[0])
        OpenSkyApi._check_lat(bbox[1])
        OpenSkyApi._check_lon(bbox[2])
        OpenSkyApi._check_lon(bbox[3])

        params["lamin"] = bbox[0]
        params["lamax"] = bbox[1]
        params["lomin"] = bbox[2]
        params["lomax"] = bbox[3]
    elif len(bbox) > 0:
        raise ValueError(
            "Invalid bounding box! Must be [min_latitude, max_latitude, min_longitude, max_longitude]."
        )

    if isinstance(tm, TokenManager):
        resp = requests.get("https://opensky-network.org/api/states/all", headers={"Authorization": f"Bearer {tm.get_token()}"}, params=params)       

    elif tm is None:
        resp = requests.get("https://opensky-network.org/api/states/all", params = params)
    
    resp.raise_for_status()
    remaining_credits = int(resp.headers.get("X-Rate-Limit-Remaining", -1))
    states = OpenSkyStates(resp.json())

    return states, remaining_credits
