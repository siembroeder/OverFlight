
from opensky_api import OpenSkyApi, TokenManager

# Core imports
import json

# Custom imports
from typing import Optional, ClassVar, Callable
from dataclasses import dataclass, field, fields
from Utils.OpenSkyUtils import getBboxSize, getBboxOffset
from Utils.TypeHints import Seconds, Latitude, Longitude, MetersPerSecond, Meters

CONFIG_SECTIONS = ("core", "apiConfig", "setup", "tracking", "visuals")
SETTINGS_PATH = "settings.json"

@dataclass
class CoreConfig:
    bboxSize: Optional[str]
    location: str = "Schiphol"
    openskyCredentialsPath: str = ".credentials.json"
    latitudeOffset: Optional[Latitude] = None
    longitudeOffset: Optional[Longitude] = None

@dataclass
class ApiConfig:
    apiCallDelay: Seconds = Seconds(10.0)

@dataclass
class SetupConfig:
    maxWindows: int = 25
    displayName: Optional[str] = None

@dataclass
class TrackingConfig:
    minVelocity: Optional[MetersPerSecond] = None
    callsign: Optional[str] = None
    airline: Optional[str] = None
    icao24: Optional[str] = None
    squawk: Optional[str] = None
    inAir: Optional[bool] = None
    onGround: Optional[bool] = None
    minGeoAltitude: Optional[Meters] = None
    maxGeoAltitude: Optional[Meters] = None
    minBaroAltitude: Optional[Meters] = None
    maxBaroAltitude: Optional[Meters] = None
    arrivalAirport: Optional[str] = None
    departureAirport: Optional[str] = None
    registrationCountry: Optional[str] = None

@dataclass
class VisualsConfig:
    windowTheme:str = "aircraft"
    windowSize:str = "small"
    updateInterval:Seconds = Seconds(1.0)
    tooltipFields:list = field(default_factory=lambda: ["callsign"])










@dataclass
class WindowTrackerConfig:
    """
    Central configuration combining all config sections, API, boundingbox, callbacks.
    
    Should be initialized via WindowTrackerConfig.buildTrackerConfig()
    
    
    """
    api: ClassVar[OpenSkyApi]
    bboxAtLocation: tuple

    core:       CoreConfig
    apiConfig:  ApiConfig
    setup:      SetupConfig
    tracking:   TrackingConfig
    visuals:    VisualsConfig
    
    callbacks: dict[str, list[Callable]] = field(default_factory=dict)
    
    @classmethod
    def buildTrackerConfig(cls):
        configData = cls.loadSettings()
        cls.raw = configData # include raw data dictionary in class
        
        # Build config sections
        coreConfig      = CoreConfig(**configData.get("core", {}))
        apiConfig       = ApiConfig(**configData.get("api", {}))
        setupConfig     = SetupConfig(**configData.get("setup", {}))
        trackingConfig  = TrackingConfig(**configData.get("tracking", {}))
        visualsConfig   = VisualsConfig(**configData.get("visuals", {}))

        if not coreConfig.location:
            raise KeyError("Location not defined in settings file.")

        # Create API
        if not hasattr(cls, "api"):
            cls.api = OpenSkyApi(token_manager=TokenManager.from_json_file(coreConfig.openskyCredentialsPath))
    
        bboxAtLocation = cls.getBbox(coreConfig, setupConfig)

        return cls(bboxAtLocation, coreConfig, apiConfig, setupConfig, trackingConfig, visualsConfig)

    @staticmethod
    def loadSettings() -> dict:
        with open(SETTINGS_PATH) as f:
            configData = json.load(f)

        return configData

    @staticmethod
    def getBbox(core:CoreConfig, setup:SetupConfig) -> tuple[float, float, float, float]:
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
        Should be used in __init__ functions like in WindowTracker: config.onChange("windowSize", lambda _: self.CloseAllWindows())
        """
        self.callbacks.setdefault(key, []).append(func)

    def applyUpdate(self, newConfig:"WindowTrackerConfig") -> None:
        """Executes the registered callbacks for each field that changed values in newConfig"""
        
        # Some fields can not be changed during runtime, if they're changed the change is ignored.
        RESTART_REQUIRED = {"openskyCredentialsPath", "displayName"}
        
        for sectionName in CONFIG_SECTIONS:
            oldSection = getattr(self, sectionName)
            newSection = getattr(newConfig, sectionName)
            
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

        if newConfig.bboxAtLocation != self.bboxAtLocation:
            self.bboxAtLocation = newConfig.bboxAtLocation
            for cb in self.callbacks.get("bboxAtLocation", []):
                cb(newConfig.bboxAtLocation)

        # update raw data dictionary
        self.raw = newConfig.raw