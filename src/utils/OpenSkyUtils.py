

from opensky_api import OpenSkyApi, OpenSkyStates, OpenSkyApi

# Core Python Imports
import math
import logging
logger = logging.getLogger(__name__)
from typing import cast

from geopy.location import Location
from geopy.geocoders import Nominatim

# Custom imports
from utils.QtUtils import getScreenGeometry



def getBboxSize(locationName:str, bboxSize:str, displayName:str|None) -> tuple[float, float, float, float]:
    """
    Get boundingbox for a given size ('small', 'medium', 'large').
    ratio of lat and lon is scaled to the geometry of the screen that's connected to displayName and also corrected for latitude
    """
    
    # Get the location using geopy
    geolocator:Nominatim = Nominatim(user_agent="appname")
    location = cast(Location | None, geolocator.geocode(locationName))
        
    if location:
        latitude = location.latitude
        longitude= location.longitude
        logger.info(f"{location}\'s coordinates are: {location.latitude}, {location.longitude}")
    else:
        raise NameError("Location not found.")

    latitudeOffsets = {"local": 0.05, "small": 0.10, "medium": 0.30, "large": 0.50, "veryLarge": 1, "huge": 2}
    
    if bboxSize in latitudeOffsets.keys():
        latitudeOffset = latitudeOffsets[bboxSize]
    else:
        raise KeyError("The selected bboxSize is not \"small\", \"medium\", or \"large\"")
    
    
    # Use the selected screens' aspect ratio to set the boundingbox aspect ratio
    geom = getScreenGeometry(displayName)
    factor = geom.width() / geom.height()   
    
    longitudeOffset = factor * latitudeOffset / math.cos(math.radians(latitude))
    
    minLat:float  = latitude - latitudeOffset
    maxLat:float  = latitude + latitudeOffset
    minLong:float = longitude- longitudeOffset
    maxLong:float = longitude+ longitudeOffset
    
    return (minLat, maxLat, minLong, maxLong)

def getBboxOffset(locationName:str, latitudeOffset:float, longitudeOffset:float) -> tuple[float, float, float, float]:
    """
    Get boundingbox for given latitude and longitude offsets. Must be a positive, non-zero float 
    """
    
    assert latitudeOffset > 0, "Offsets should both be posive, non-zero floats."
    assert longitudeOffset > 0,"Offsets should both be posive, non-zero floats."

    # Get the location using geopy
    geolocator:Nominatim = Nominatim(user_agent="appname")
    location = cast(Location | None, geolocator.geocode(locationName))
        
    if location:
        latitude = location.latitude
        longitude= location.longitude
        logger.info(f"{location}\'s coordinates are: {location.latitude}, {location.longitude}")
    else:
        raise NameError("Location not found.")

    minLat:float  = latitude - latitudeOffset
    maxLat:float  = latitude + latitudeOffset
    minLong:float = longitude- longitudeOffset
    maxLong:float = longitude+ longitudeOffset
    
    return (minLat, maxLat, minLong, maxLong)

def fetchStatesInBbox(api:OpenSkyApi, bbox:tuple) -> OpenSkyStates|None:
    """Use the opensky_api to get all currently flying aircraft within the given boundingbox"""
    states:OpenSkyStates|None = api.get_states(bbox = bbox)
    return states








# # Code that can be used later for getting aircraft's wake turbulence classification

# def getAircraftMeta(icao24:str, username:str, password:str) -> dict:
#     url:str = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao24}"
#     response:Response = requests.get(url, auth=(username, password))
    
#     if response.status_code == 200:
#         return response.json()
#     return {}

# def getTypeCodes(states:list[StateVector], printCodes:bool = False) -> list[str]:
#     typecodes:list = []
#     for state in states:
#         meta:dict = getAircraftMeta(state.icao24, "", "") # The empty strings are the username and password for the api call ... ?!
        
#         # print(f"{meta=}")
        
#         typecode = meta.get("typecode")
#         typecodes.append(typecode)

#         if printCodes:
#             print(state.callsign, typecode, meta.get("model"))

#     return typecodes

# def printClassifications(typecodes:list[str], printClassifications = False) -> None:
    
#     with open("Data/AircraftClassifications/AircraftClassifications.json") as file:
        
#         aircraftClassifications = json.load(file)

#         if printClassifications: print("\nClassifications:")
#         for typecode in typecodes:
#             try:
#                 classification = aircraftClassifications[typecode]
#                 wake = classification["wake"]
#                 if printClassifications: print(f"Type \'{typecode}\' found, classification: {wake}")
#             except:
#                 if printClassifications: print(f"Type \'{typecode}\' not found, continuing")
#                 pass

# def getTrueTracks(states:list[StateVector]) -> list[float]:
#     tracks:list = []
#     for state in states:
#         tracks.append(state.true_track) # True_track, can be null.
#     return tracks
   