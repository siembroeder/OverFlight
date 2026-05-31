
import os
import yaml

import logging
logger = logging.getLogger(__name__)

from typing import Optional, ClassVar, Callable
from dataclasses import dataclass, field, fields
from opensky_api import OpenSkyApi, TokenManager
from utils.OpenSkyUtils import getBboxSize, getBboxOffset
from utils.TypeHints import Seconds, Latitude, Longitude, MetersPerSecond, Meters

SETTINGS_SECTIONS = ("core", "api", "setup", "tracking", "visuals")
SETTINGS_PATH = "settings.yaml"


@dataclass
class CoreSettings:
    bboxSize: Optional[str]
    location: str = "Schiphol"
    openskyCredentialsPath: str = ".credentials.json"
    latitudeOffset: Optional[Latitude] = None
    longitudeOffset: Optional[Longitude] = None

@dataclass
class ApiSettings:
    apiCallDelay: Seconds = Seconds(5.0)

@dataclass
class SetupSettings:
    maxWindows: int = 25
    displayName: Optional[str] = None

@dataclass
class TrackingSettings:
    icao24: Optional[str] = None
    callsign: Optional[str] = None
    airline: Optional[str] = None
    allowedTimePositionLag: Optional[int] = None
    allowedLastContactLag: Optional[int] = None
    squawk: Optional[str] = None
    inAir: Optional[bool] = None
    onGround: Optional[bool] = None
    minVelocity: Optional[MetersPerSecond] = None
    maxVelocity: Optional[MetersPerSecond] = None
    trueTrackRange: Optional[list[float]] = None
    minVerticalRate: Optional[float] = None
    maxVerticalRate: Optional[float] = None
    minGeoAltitude: Optional[Meters] = None
    maxGeoAltitude: Optional[Meters] = None
    minBaroAltitude: Optional[Meters] = None
    maxBaroAltitude: Optional[Meters] = None
    spi: Optional[int] = None
    positionSource: Optional[list[int]] = None
    category: Optional[list[int]] = None
    arrivalAirport: Optional[str] = None
    departureAirport: Optional[str] = None
    originCountry: Optional[str] = None
    sensors: Optional[list[int]] = None
    modelName: Optional[str] = None
    wtc: Optional[str] = None
    wtg: Optional[str] = None
    typecode: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    engineCount: Optional[int] = None
    engineType: Optional[str] = None

@dataclass
class VisualsSettings:
    windowTheme:str = "aircraft"
    windowSize:str = "small"
    updateInterval:Seconds = Seconds(1.0)
    tooltipFields:list = field(default_factory=lambda: ["callsign"])
    fallbackTypecode:str = "C172"









@dataclass
class Settings:
    """
    Central configuration combining all config sections, API, boundingbox, callbacks.
    
    Should be initialized via Settings.build()
    """
    
    openSkyApi: ClassVar[OpenSkyApi]
    bboxAtLocation: tuple

    core:       CoreSettings
    api:        ApiSettings
    setup:      SetupSettings
    tracking:   TrackingSettings
    visuals:    VisualsSettings
    
    callbacks: dict[str, list[Callable]] = field(default_factory=dict)
    
    @classmethod
    def build(cls) -> "Settings":
        settings = cls.loadSettings()
            
        cls.raw = settings # include raw data dictionary in class
        
        # Build settings sections
        core      = CoreSettings(**settings.get("core", {}))
        api       = ApiSettings(**settings.get("api", {}))
        setup     = SetupSettings(**settings.get("setup", {}))
        tracking  = TrackingSettings(**settings.get("tracking", {}))
        visuals   = VisualsSettings(**settings.get("visuals", {}))

        if not core.location:
            raise KeyError("Location not defined in settings file.")

        # Create API
        if not hasattr(cls, "openSkyApi"):
            cls.openSkyApi:OpenSkyApi = cls.getOpenSkyApi(core.openskyCredentialsPath)
            
            # if not an authenticated user, set ratelimiting to 10 seconds if not already.
            if (cls.openSkyApi._token_manager is None) and (api.apiCallDelay < 10.0):
                api.apiCallDelay = Seconds(10.0)
    
        bboxAtLocation = cls.getBbox(core, setup)

        return cls(bboxAtLocation, core, api, setup, tracking, visuals)

    @staticmethod
    def loadSettings() -> dict:
        with open(SETTINGS_PATH) as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def getOpenSkyApi(customCredentialsPath:str) -> OpenSkyApi:
        credentialsPaths = ["credentials.json", ".credentials.json", customCredentialsPath]

        # Look for credential files in OverFlight/ directory (not in subdirectories)
        for file in credentialsPaths:
            if os.path.isfile(file):
                try:
                    return OpenSkyApi(token_manager=TokenManager.from_json_file(file))
                except(FileNotFoundError, ValueError, OSError):
                    pass
        
        # If no credential files found, use anonymous opensky account, less credits and rate limited to 10 seconds  
        return OpenSkyApi()

    @staticmethod
    def getBbox(core:CoreSettings, setup:SetupSettings) -> tuple[float, float, float, float]:
        """Helper function for finding boundingbox. settings should include either bboxSize or BOTH lat/lonOffset"""
        location  = core.location
        bboxSize  = core.bboxSize
        latOffset = core.latitudeOffset
        lonOffset = core.longitudeOffset

        hasBbox = (bboxSize not in (None, ""))
        hasLatOffset = (latOffset is not None)
        hasLonOffset = (lonOffset is not None)
        
        if hasBbox and (hasLonOffset or hasLatOffset):
            raise KeyError("Invalid configuration, use either bboxSize or the offsets, not both.")
        
        if hasBbox:
            return getBboxSize(location, bboxSize, setup.displayName)
            
        if hasLatOffset and hasLonOffset:
            if latOffset <= 0.0 or lonOffset <= 0.0:
                raise KeyError("longitudeOffset and latitudeOffset should both be non-zero.")
            return getBboxOffset(location, latOffset, lonOffset)
        
        if hasLatOffset or hasLonOffset:
            raise KeyError("Both offsets should be set together.")
        
        raise KeyError("Missing bbox configuration, set bboxSize or both latitudeOffset and LongitudeOffset in your settings file.")
    
    def onChange(self, key: str, func: Callable) -> None:
        """
        Registers a callback function to be triggered when a setting changes
        Should be used in __init__ functions like in WindowTracker: settings.onChange("windowSize", lambda _: self.CloseAllWindows())
        """
        self.callbacks.setdefault(key, []).append(func)

    def applyUpdate(self, newSettings:"Settings") -> None:
        """Executes the registered callbacks for each field that changed values in newSetings"""
        
        # Some fields can not be changed during runtime, if they're changed the change is ignored.
        RESTART_REQUIRED = {"openskyCredentialsPath", "displayName"}
        
        for sectionName in SETTINGS_SECTIONS:
            oldSection = getattr(self, sectionName)
            newSection = getattr(newSettings, sectionName)
            
            for field in fields(oldSection):
                if field.name in RESTART_REQUIRED:
                    continue
                oldVal = getattr(oldSection, field.name)
                newVal = getattr(newSection, field.name)
                if oldVal == newVal:
                    continue
                
                # Set the new value in the oldSection and execute the callback
                setattr(oldSection, field.name, newVal)
                for callback in self.callbacks.get(field.name, []):
                    callback(newVal)

        if newSettings.bboxAtLocation != self.bboxAtLocation:
            self.bboxAtLocation = newSettings.bboxAtLocation
            for cb in self.callbacks.get("bboxAtLocation", []):
                cb(newSettings.bboxAtLocation)

        # update raw data dictionary
        self.raw = newSettings.raw