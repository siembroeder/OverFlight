

import csv
import math
from typing import cast
import logging
logger = logging.getLogger(__name__)
import requests
import pandas as pd
from requests import Response
from dataclasses import dataclass

from geopy.location import Location
from geopy.geocoders import Nominatim

from utils.qt_utils import get_screen_geometry
from opensky_api import OpenSkyApi, OpenSkyStates, OpenSkyApi



def get_bbox_size(location_name:str, bbox_size:str, display_name:str|None) -> tuple[float, float, float, float]:
    """
    Get boundingbox for a given size ('small', 'medium', 'large').
    ratio of lat and lon is scaled to the geometry of the screen that's connected to displayName and also corrected for latitude
    """
    
    # Get the location using geopy
    geolocator:Nominatim = Nominatim(user_agent="appname")
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
    geolocator:Nominatim = Nominatim(user_agent="appname")
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

def fetch_states_in_bbox(api:OpenSkyApi, bbox:tuple) -> OpenSkyStates|None:
    """Use the opensky_api to get all currently flying aircraft within the given boundingbox"""
    states:OpenSkyStates|None = api.get_states(bbox = bbox)
    return states

def get_aircraft_meta(icao24:str) -> dict:
    url:str = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao24.lower().strip()}"
    response:Response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    return {}

def get_single_type_code(icao24:str) -> str:
    meta:dict = get_aircraft_meta(icao24) 
    typecode = meta.get("typecode")
    
    if typecode:
        return typecode

    return ""

# type Icao24 = str
# type Typecode = str
# def getAllTypeCodes(icao24s:list[str]) -> dict[Icao24, Typecode]:
#     icao24_df = pd.read_csv("data/icao24_typecode_aircraft.csv")
#     typecode_from_icao24 = icao24_df.set_index("icao24")["typecode"]

#     typecodes = {}
#     for icao24 in icao24s:
#         try:
#             typecode = typecode_from_icao24[icao24]
#         except:
#             typecode = getSingleTypeCode(icao24)
            
#         if typecode:
#             typecodes.update({icao24:typecode})
            
#     return typecodes