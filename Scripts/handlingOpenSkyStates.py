

from opensky_api import OpenSkyApi, OpenSkyStates, OpenSkyApi, StateVector

import json
import requests
from typing import cast
from requests.models import Response

from geopy.location import Location
from geopy.geocoders import Nominatim



def getBbox(locationName:str, BboxSize:str) -> tuple[float, float, float, float]:

    geolocator:Nominatim = Nominatim(user_agent="appname")
    # location:Location    = geolocator.geocode(locationName)
    location = cast(Location | None, geolocator.geocode(locationName))
        
    if location:
        latitude = location.latitude
        longitude= location.longitude
        print(f"{location}\'s coordinates are: {location.latitude}, {location.longitude}")
    else:
        raise NameError("Location not found.")
     

    BboxSizes:dict[str, dict] = {"small": {"latitudeOffset": 0.15, "longitudeOffset": 0.25},
                                 "large": {"latitudeOffset": 0.3,  "longitudeOffset": 0.5}}

    latitudeOffset:dict  =  BboxSizes[BboxSize]["latitudeOffset"]
    longitudeOffset:dict = BboxSizes[BboxSize]["longitudeOffset"]

    minLat:float  = latitude - latitudeOffset
    maxLat:float  = latitude + latitudeOffset
    minLong:float = longitude- longitudeOffset
    maxLong:float = longitude+ longitudeOffset
    
    return (minLat, maxLat, minLong, maxLong)

def fetchStatesInBbox(api:OpenSkyApi, bbox:tuple) -> OpenSkyStates|None:
    states:OpenSkyStates|None = api.get_states(bbox = bbox)
    return states

def getAircraftMeta(icao24: str, username: str, password: str) -> dict:
    url:str = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao24}"
    response:Response = requests.get(url, auth=(username, password))
    
    if response.status_code == 200:
        return response.json()
    return {}

def getTypeCodes(states:list[StateVector], printCodes:bool = False) -> list[str]:
    typecodes:list = []
    for state in states:
        meta:dict = getAircraftMeta(state.icao24, "", "") # The empty strings are the username and password for the api call ... ?!
        
        # print(f"{meta=}")
        
        typecode = meta.get("typecode")
        typecodes.append(typecode)

        if printCodes:
            print(state.callsign, typecode, meta.get("model"))

    return typecodes

def printClassifications(typecodes:list[str], printClassifications = False) -> None:
    
    with open("Data/AircraftClassifications/AircraftClassifications.json") as file:
        
        aircraftClassifications = json.load(file)

        if printClassifications: print("\nClassifications:")
        for typecode in typecodes:
            try:
                classification = aircraftClassifications[typecode]
                wake = classification["wake"]
                if printClassifications: print(f"Type \'{typecode}\' found, classification: {wake}")
            except:
                if printClassifications: print(f"Type \'{typecode}\' not found, continuing")
                pass

def getTrueTracks(states:list[StateVector]) -> list[float]:
    tracks:list = []
    for state in states:
        tracks.append(state.true_track) # True_track, can be null.
    return tracks
   