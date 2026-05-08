
from opensky_api import OpenSkyApi, TokenManager

# Core imports
import json

# Custom imports
from Mover import Mover
from typing import Optional, ClassVar
from dataclasses import dataclass, field
from Utils.OpenSkyUtils import getBboxSize, getBboxOffset


@dataclass
class CoreConfig:
    bboxSize: Optional[str]
    location: str = "Schiphol"
    openskyCredentialsPath: str = "credentials.json"
    latitudeOffset: Optional[float] = None
    longitudeOffset: Optional[float] = None

@dataclass
class ApiConfig:
    apiCallDelay: float = 10.0

@dataclass
class SetupConfig:
    maxWindows: int = 25
    displayName: Optional[str] = None

@dataclass
class TrackingConfig:
    minVelocity: Optional[float] = None
    callsign: Optional[str] = None
    airline: Optional[str] = None
    icao24: Optional[str] = None
    squawk: Optional[str] = None
    inAir: Optional[bool] = None
    onGround: Optional[bool] = None
    minGeoAltitude: Optional[float] = None
    maxGeoAltitude: Optional[float] = None
    minBaroAltitude: Optional[float] = None
    maxBaroAltitude: Optional[float] = None
    arrivalAirport: Optional[str] = None
    departureAirport: Optional[str] = None
    registrationCountry: Optional[str] = None

@dataclass
class VisualsConfig:
    windowTheme:str = "aircraft"
    windowSize:str = "small"
    updateInterval:float = 1.0
    tooltipFields:list = field(default_factory=lambda: ["callsign"])

@dataclass
class WindowTrackerConfig:
    api: ClassVar[OpenSkyApi]
    bboxAtLocation: tuple

    core:       CoreConfig
    apiConfig:  ApiConfig
    setup:      SetupConfig
    tracking:   TrackingConfig
    visuals:    VisualsConfig
    
    mover: Mover = Mover()
    
    
    @classmethod
    def loadSettings(cls, settingsPath:str = "Settings/settings.json", printFlag:bool = True):
        with open(settingsPath) as f:
            configData = json.load(f)

        # Build config sections
        coreConfig      = CoreConfig(**configData["core"])
        apiConfig       = ApiConfig(**configData.get("api", {}))
        setupConfig     = SetupConfig(**configData.get("setup", {}))
        trackingConfig  = TrackingConfig(**configData.get("tracking", {}))
        visualsConfig   = VisualsConfig(**configData.get("visuals", {}))


        # Create API
        if not hasattr(cls, "api"):
            cls.api = OpenSkyApi(token_manager=TokenManager.from_json_file(coreConfig.openskyCredentialsPath))
        
        if not coreConfig.location:
            raise KeyError("Location not defined in settings.json.")

        bboxAtLocation = cls.getBbox(coreConfig, setupConfig)

        return cls(bboxAtLocation, coreConfig, apiConfig, setupConfig, trackingConfig, visualsConfig)


    @staticmethod
    def getBbox(core:CoreConfig, setup:SetupConfig) -> tuple[float, float, float, float]:
        
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
            return getBboxOffset(location, lonOffset, latOffset)
        
        if hasLatOffset or hasLonOffset:
            raise KeyError("Both offsets should be set together.")
        
        raise KeyError("Missing bbox configuration, set bboxSize or both latitudeOffset and LongitudeOffset in your settings.json file.")