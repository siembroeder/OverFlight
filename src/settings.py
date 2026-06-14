
import os
import yaml

import logging
logger = logging.getLogger(__name__)

from typing import Optional, ClassVar, Callable
from dataclasses import dataclass, field, fields
from opensky_api import OpenSkyApi, TokenManager
from utils.open_sky_utils import getBboxSize, getBboxOffset
from utils.type_hints import Seconds, Latitude, Longitude, MetersPerSecond, Meters

SETTINGS_SECTIONS = ("core", "api", "setup", "tracking", "visuals")
SETTINGS_PATH = "settings.yaml"


@dataclass
class CoreSettings:
    bbox_size: Optional[str]
    location: str = "Schiphol"
    opensky_credentials_path: str = ".credentials.json"
    latitude_offset: Optional[Latitude] = None
    longitude_offset: Optional[Longitude] = None

@dataclass
class ApiSettings:
    api_call_delay: Seconds = Seconds(5.0)

@dataclass
class SetupSettings:
    max_windows: int = 25
    display_name: Optional[str] = None

@dataclass
class TrackingSettings:
    icao24: Optional[str] = None
    callsign: Optional[str] = None
    airline: Optional[str] = None
    allowed_time_position_lag: Optional[int] = None
    allowed_last_contact_lag: Optional[int] = None
    squawk: Optional[str] = None
    in_air: Optional[bool] = None
    on_ground: Optional[bool] = None
    min_velocity: Optional[MetersPerSecond] = None
    max_velocity: Optional[MetersPerSecond] = None
    true_track_range: Optional[list[float]] = None
    min_vertical_Rate: Optional[float] = None
    max_vertical_rate: Optional[float] = None
    minGeo_altitude: Optional[Meters] = None
    maxGeo_altitude: Optional[Meters] = None
    minBaro_altitude: Optional[Meters] = None
    maxBaro_altitude: Optional[Meters] = None
    spi: Optional[int] = None
    position_source: Optional[list[int]] = None
    category: Optional[list[int]] = None
    arrival_airport: Optional[str] = None
    departure_airport: Optional[str] = None
    origin_country: Optional[str] = None
    sensors: Optional[list[int]] = None
    model_name: Optional[str] = None
    wtc: Optional[str] = None
    wtg: Optional[str] = None
    typecode: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    engine_count: Optional[int] = None
    engine_type: Optional[str] = None

@dataclass
class VisualsSettings:
    window_theme:str = "aircraft"
    window_size:str = "small"
    update_interval:Seconds = Seconds(1.0)
    tooltip_fields:list = field(default_factory=lambda: ["callsign"])
    fallback_typecode:str = "C172"









@dataclass
class Settings:
    """
    Central configuration combining all config sections, API, boundingbox, callbacks.
    
    Should be initialized via Settings.build()
    """
    
    open_sky_api: ClassVar[OpenSkyApi]
    bbox_at_location: tuple

    core:       CoreSettings
    api:        ApiSettings
    setup:      SetupSettings
    tracking:   TrackingSettings
    visuals:    VisualsSettings
    
    callbacks: dict[str, list[Callable]] = field(default_factory=dict)
    
    @classmethod
    def build(cls) -> "Settings":
        settings = cls.load_settings()
            
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
        if not hasattr(cls, "open_sky_api"):
            cls.open_sky_api:OpenSkyApi = cls.get_open_sky_api(core.opensky_credentials_path)
            
            # if not an authenticated user, set ratelimiting to 10 seconds if not already.
            if (cls.open_sky_api._token_manager is None) and (api.api_call_delay < 10.0):
                api.api_call_delay = Seconds(10.0)
    
        bbox_at_location = cls.get_bbox(core, setup)

        return cls(bbox_at_location, core, api, setup, tracking, visuals)

    @staticmethod
    def load_settings() -> dict:
        with open(SETTINGS_PATH) as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def get_open_sky_api(custom_credentials_path:str) -> OpenSkyApi:
        credentials_paths = ["credentials.json", ".credentials.json", custom_credentials_path]

        # Look for credential files in OverFlight/ directory (not in subdirectories)
        for file in credentials_paths:
            if os.path.isfile(file):
                try:
                    return OpenSkyApi(token_manager=TokenManager.from_json_file(file))
                except(FileNotFoundError, ValueError, OSError):
                    pass
        
        # If no credential files found, use anonymous opensky account, less credits and rate limited to 10 seconds  
        return OpenSkyApi()

    @staticmethod
    def get_bbox(core:CoreSettings, setup:SetupSettings) -> tuple[float, float, float, float]:
        """Helper function for finding boundingbox. settings should include either bboxSize or BOTH lat/lonOffset"""
        location  = core.location
        bbox_size  = core.bbox_size
        lat_offset = core.latitude_offset
        lon_offset = core.longitude_offset

        has_bbox = (bbox_size not in (None, ""))
        has_lat_offset = (lat_offset is not None)
        has_lon_offset = (lon_offset is not None)
        
        if has_bbox and (has_lon_offset or has_lat_offset):
            raise KeyError("Invalid configuration, use either bboxSize or the offsets, not both.")
        
        if has_bbox:
            return getBboxSize(location, bbox_size, setup.display_name)
            
        if has_lat_offset and has_lon_offset:
            if lat_offset <= 0.0 or lon_offset <= 0.0:
                raise KeyError("longitudeOffset and latitudeOffset should both be non-zero.")
            return getBboxOffset(location, lat_offset, lon_offset)
        
        if has_lat_offset or has_lon_offset:
            raise KeyError("Both offsets should be set together.")
        
        raise KeyError("Missing bbox configuration, set bboxSize or both latitudeOffset and LongitudeOffset in your settings file.")
    
    def on_change(self, key: str, func: Callable) -> None:
        """
        Registers a callback function to be triggered when a setting changes
        Should be used in __init__ functions like in WindowTracker: settings.onChange("windowSize", lambda _: self.CloseAllWindows())
        """
        self.callbacks.setdefault(key, []).append(func)

    def apply_update(self, new_settings:"Settings") -> None:
        """Executes the registered callbacks for each field that changed values in newSetings"""
        
        # Some fields can not be changed during runtime, if they're changed the change is ignored.
        RESTART_REQUIRED = {"openskyCredentialsPath", "displayName"}
        
        for section_name in SETTINGS_SECTIONS:
            old_section = getattr(self, section_name)
            new_section = getattr(new_settings, section_name)
            
            for field in fields(old_section):
                if field.name in RESTART_REQUIRED:
                    continue
                old_val = getattr(old_section, field.name)
                new_val = getattr(new_section, field.name)
                if old_val == new_val:
                    continue
                
                # Set the new value in the oldSection and execute the callback
                setattr(old_section, field.name, new_val)
                for callback in self.callbacks.get(field.name, []):
                    callback(new_val)

        if new_settings.bbox_at_location != self.bbox_at_location:
            self.bbox_at_location = new_settings.bbox_at_location
            for cb in self.callbacks.get("bboxAtLocation", []):
                cb(new_settings.bbox_at_location)

        # update raw data dictionary
        self.raw = new_settings.raw