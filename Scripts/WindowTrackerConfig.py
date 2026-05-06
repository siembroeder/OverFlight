
from opensky_api import OpenSkyApi, TokenManager

# Core imports
import json

# Custom imports
from Mover import Mover
from dataclasses import dataclass, fields
from HandlingOpenSkyStates import getBboxSize, getBboxOffset


@dataclass
class WindowTrackerConfig:
    # non-keyword arguments, required settings
    api:OpenSkyApi
    bboxAtLocation:tuple 
    
    # required keyword arguments
    openskyCredentialsPath:str = "credentials.json"
    mover:Mover = Mover()
    apiCallDelay:float = 10.0
    
    # Optional keyword arguments
    bboxSize:str|None = None
    latitudeOffset:float|None = None
    longitudeOffset:float|None = None
    maxWindows:int = 25
    displayName:str|None = None
    minVelocity:float|None = None
    callsign:str|None = None
    airline:str|None = None
    icao24:str|None = None
    squawk:str|None = None
    inAir:bool|None = None
    onGround:bool|None = None
    minGeoAltitude:float|None = None
    maxGeoAltitude:float|None = None
    minBaroAltitude:float|None = None
    maxBaroAltitude:float|None = None
    arrivalAirport:str|None = None
    departureAirport:str|None = None
    registrationCountry:str|None = None
    
    @classmethod
    def loadSettings(cls, settingsPath:str="Settings/userDefinedTrackerSettings.json"):
        settings = {}
        validKeys = {field.name for field in fields(cls)}
        
        with open(settingsPath) as f:
            groupedSettings = json.load(f)

        for group in groupedSettings.values():      # Flatten all groups into one dict, groups are merely for userfriendliness
            settings.update(group)
                
        api:OpenSkyApi = OpenSkyApi(token_manager=TokenManager.from_json_file(settings["openskyCredentialsPath"]))
        location = settings.get("location")
        if not location:
            raise KeyError("Location not defined in settings.json.")
        
        bboxAtLocation = cls.getBbox(location, settings)     
        filteredSettings = {key: value for key,value in settings.items() if key in validKeys}
        return cls(api, bboxAtLocation, **filteredSettings)

    @staticmethod
    def getBbox(location:str, settings:dict) -> tuple[float, float, float, float]:
        
        bboxSize  = settings.get("bboxSize")
        latOffset = settings.get("latitudeOffset")
        lonOffset = settings.get("longitudeOffset")

        hasBbox = (bboxSize not in (None, ""))
        hasLatOffset = (latOffset is not None)
        hasLonOffset = (lonOffset is not None)
        
        if hasBbox and (hasLonOffset or hasLatOffset):
            raise KeyError("Invalid configuration, use either bboxSize or the offsets, not both.")
        
        if hasBbox:
            if bboxSize in ["small", "medium", "large"]:
                return getBboxSize(location, bboxSize)
            else:
                raise KeyError("The selected bboxSize is not \"small\", \"medium\", or \"large\"")
            
        if hasLatOffset and hasLonOffset:
            if latOffset <= 0.0 or lonOffset <= 0.0:
                raise KeyError("longitudeOffset and latitudeOffset should both be non-zero.")
            return getBboxOffset(location, lonOffset, latOffset)
        
        if hasLatOffset or hasLonOffset:
            raise KeyError("Both offsets should be set together.")
        
        raise KeyError("Missing bbox configuration, set bboxSize or both latitudeOffset and LongitudeOffset in your settings.json file.")
        
