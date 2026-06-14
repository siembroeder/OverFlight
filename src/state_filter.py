import time
import logging
logger = logging.getLogger(__name__)
import pandas as pd
from pandas import DataFrame
from typing import TYPE_CHECKING
    
from custom_qt_window import MainWindow
from opensky_api import StateVector, OpenSkyApi
from utils.aircraft_record import AircraftRecord
from FlightRadarAPI import FlightRadar24API, Flight

if TYPE_CHECKING:
    from settings import TrackingSettings

type icao24 = str


class StateFilter():
    """
    Filters OpenSky aircraft state vectors using opensky_api and local configuration settings.
    """
    def __init__(self, settings:"TrackingSettings", api:OpenSkyApi, max_windows:int, bbox:tuple):
        """Initialize filter with tracking configuration, OpenSky API client, and maximum number of windows (default=25)"""
        
        self.settings:TrackingSettings = settings
        self.api:OpenSkyApi = api
        self.max_windows = max_windows
        self.bbox = bbox
    
    def filter_states(self, states:list[StateVector]) -> list[StateVector]:
        
        # states = self.applyLocalFilters(states)
        
        if self.settings.departureAirport or self.settings.arrivalAirport:
            states = self.apply_airport_filters(states)
        

        return states    
    
    def filter_aircraft(self, aircraft:list[AircraftRecord]) -> list[AircraftRecord]:
        
        # Filter by opensky statevector information
        states = [ac.state for ac in aircraft]
        states = self.apply_local_state_filters(states)
        if self.settings.departureAirport or self.settings.arrivalAirport:
            states = self.apply_airport_filters(states)

        # Filter by icao8643 entry
        aircraft = [ac for ac in aircraft if ac.state in states]
        aircraft = self.apply_icao_entry_filter(aircraft)

        assert self.max_windows > 0.0, "maxWindows should be larger than 0"
        if len(aircraft) >= self.max_windows: # must be last filter
            logger.debug(f"Restricting number of windows to: {self.max_windows}")
            aircraft = aircraft[:self.max_windows]
        
        return aircraft
    
    def apply_icao_entry_filter(self, aircraft:list[AircraftRecord]) -> list[AircraftRecord]:
        settings = self.settings
        
        if settings.modelName:
            aircraft = [ac for ac in aircraft if ac.entry.modelFullName.lower() == settings.modelName.lower()]
            
        if settings.wtc:
            aircraft = [ac for ac in aircraft if ac.entry.wtc == settings.wtc.upper()]
            
        if settings.wtg:
            aircraft = [ac for ac in aircraft if ac.entry.wtg == settings.wtg.upper()]
            
        if settings.typecode:
            aircraft = [ac for ac in aircraft if ac.entry.typecode == settings.typecode.upper()]
        
        if settings.manufacturer:
            aircraft = [ac for ac in aircraft if ac.entry.manufacturerCode == settings.manufacturer.upper()]
        
        if settings.description:
            aircraft = [ac for ac in aircraft if ac.entry.aircraftDescription.lower() == settings.description.lower()]
        
        if settings.engineCount:
            aircraft = [ac for ac in aircraft if ac.entry.engineCount == settings.engineCount]
        
        if settings.engineType:
            aircraft = [ac for ac in aircraft if ac.entry.engineType.lower() == settings.engineType.lower()]

        return aircraft
         
    def apply_local_state_filters(self, states:list[StateVector]) -> list[StateVector]:
        settings = self.settings
        filter_timestamp = time.monotonic()
        
        if settings.icao24:
            logger.debug(f"Filtering for icao24: {settings.icao24}")
            states = [state for state in states if state.icao24.lower() == settings.icao24.lower()]
        
        if settings.callsign:
            logger.debug(f"Filtering for callsign {settings.callsign}")
            states = [state for state in states if (state.callsign is not None) and (state.callsign.strip() == settings.callsign)]
        
        if settings.airline:
            logger.debug(f"Filtering for airline: {settings.airline}")
            states = [state for state in states if (state.callsign is not None) and (state.callsign.lower().startswith(settings.airline.strip().lower()))]
            
        if settings.allowedTimePositionLag:
            logger.debug(f"Filtering for timePositionLag: {settings.allowedTimePositionLag}")
            states = [state for state in states if (state.time_position is not None) and (state.time_position > (filter_timestamp - settings.allowedTimePositionLag))]
            
        if settings.allowedLastContactLag:
            logger.debug(f"Filtering for lastContactLag: {settings.allowedLastContactLag}")
            states = [state for state in states if state.last_contact > (filter_timestamp - settings.allowedLastContactLag)]
            
        if settings.originCountry:
            logger.debug(f"Filtering for registration country: {settings.originCountry}")
            states = [state for state in states if state.origin_country.lower().strip() == settings.originCountry.lower().strip()]
                
        if (settings.minVelocity) or (settings.maxVelocity):
            logger.debug(f"Filtering for velocity: minVelocity: {settings.minVelocity}, maxVelocity: {settings.maxVelocity}")
            states = self.filter_states_velocity(states)
            
        if settings.trueTrackRange:
            logger.debug(f"Filtering for true track range: {settings.trueTrackRange}")
            states = self.filter_states_true_track_range(states)
            
        if settings.minVerticalRate:
            logger.debug(f"Filtering for minimum vertical range: {settings.minVerticalRate}")
            states = [state for state in states if (state.vertical_rate is not None) and (state.vertical_rate >= settings.minVerticalRate)]
             
        if (settings.maxVerticalRate is not None) and (settings.maxVerticalRate > 0.0):
            logger.debug(f"Filtering for maximum vertical range: {settings.maxVerticalRate}")
            states = [state for state in states if (state.vertical_rate is not None) and (state.vertical_rate <= settings.maxVerticalRate)]

        if settings.squawk:
            logger.debug(f"Filtering for squawk: {settings.squawk}")
            states = [state for state in states if (state.squawk is not None) and (state.squawk.lower().strip() == settings.squawk.lower().strip())]
        
        if settings.onGround == 1:
            logger.debug(f"Filtering for aircraft on the ground")
            states = [state for state in states if state.on_ground == True]
            
        if settings.inAir == 1:
            logger.debug(f"Filtering for aircraft in the air")
            states = [state for state in states if state.on_ground == False]
        
        if settings.minBaroAltitude:
            logger.debug(f"Filtering for minBaroAltitude: {settings.minBaroAltitude}")            
            states = [state for state in states if (state.baro_altitude is not None) and (state.baro_altitude*3.28084 >= settings.minBaroAltitude)] # convert from meters to feet
        
        if (settings.maxBaroAltitude is not None) and (settings.maxBaroAltitude > 0.0):
            logger.debug(f"Filtering for maxBaroAltitude: {settings.maxBaroAltitude}")
            states = [state for state in states if (state.baro_altitude is not None) and (state.baro_altitude*3.28084 <= settings.maxBaroAltitude)] # convert from meters to feet   
                 
        if settings.minGeoAltitude:
            logger.debug(f"Filtering for minGeoAltitude: {settings.minGeoAltitude}")
            states = [state for state in states if (state.geo_altitude) and (state.geo_altitude*3.28084 >= settings.minGeoAltitude)] # convert from meters to feet

        if (settings.maxGeoAltitude is not None) and (settings.maxGeoAltitude > 0.0):
            logger.debug(f"Filtering for maxGeoAltitude: {settings.maxGeoAltitude}")
            states = [state for state in states if (state.geo_altitude) and (state.geo_altitude*3.28084 <= settings.maxGeoAltitude)] # convert from meters to feet
        
        if settings.spi == 1:
            logger.debug(f"Filtering for spi: {settings.spi}")
            states = [state for state in states if state.spi == True]
            
        if settings.positionSource:
            logger.debug(f"Filtering for positionSource: {settings.positionSource}")
            states = [state for state in states if state.position_source in settings.positionSource]
        
        if settings.category:
            logger.debug(f"Filtering for category: {settings.category}")
            states = self.filter_states_category(states)
            
        if settings.sensors:
            logger.debug(f"Filtering for sensors: {settings.sensors}")
            logger.warning(f"Untested, because the dev team doesn't have access to a paid openskyapi account")
            states = [state for state in states if (state.sensors) and any(sensor in settings.sensors for sensor in state.sensors)]
            
            
        return states        
           
    def filter_states_velocity(self, states:list[StateVector]) -> list[StateVector]:
        """Helper function to filter states by velocity"""
        min_velocity = self.settings.minVelocity
        max_velocity = self.settings.maxVelocity
        
        if (min_velocity is None) and (max_velocity is None):
            return states
        
        filtered_states = []
        for state in states:
            
            if state.velocity is None:
                continue
                
            # apply minimum velocity filtering
            if (min_velocity is not None) and (state.velocity < min_velocity):
                # logger.debug(f"Filtered out callsign {state.callsign} because velocity too slow")
                continue
            
            # apply maximum velocity filtering
            if (max_velocity is not None) and (max_velocity > 0.0) and (state.velocity > max_velocity):
                # logger.debug(f"Filtered out callsign {state.callsign} because velocity too fast")
                continue

            # logger.debug(f"Callsign {state.callsign} passed velocity filter: {state.velocity}")  
            filtered_states.append(state)
                
        return filtered_states

    def filter_states_true_track_range(self, states:list[StateVector]) -> list[StateVector]:
        range = self.settings.trueTrackRange
        assert range is not None
        assert range[0] != range[1]

        filtered_states = []
        for state in states:
            if state.true_track is None:
                continue
            
            # Eg if range is [0, 90]
            if range[0] < range[1]:
                if (state.true_track >= range[0]) and (state.true_track <= range[1]):
                    filtered_states.append(state)

            # Eg if range is [350, 10], notice the 'or' conditional instead of 'and'
            elif range[0] > range[1]:
                if (state.true_track >= range[0]) or (state.true_track <= range[1]):
                    filtered_states.append(state) 
        
        return filtered_states
    
    def filter_states_category(self, states:list[StateVector]) -> list[StateVector]:
        if not self.settings.category:
            return states
        
        excluded_categories = []
        for cat in self.settings.category:
            if isinstance(cat, str) and (cat.startswith("!")):
                num = int(cat.lstrip("!"))
                excluded_categories.append(num)
        
        filtered_states = []
        for state in states:
            cat = state.category
            
            if excluded_categories and cat not in excluded_categories:
                filtered_states.append(state)
                            
            elif cat in self.settings.category:
                filtered_states.append(state)
        
        return filtered_states
    
    def apply_airport_filters(self, states:list[StateVector]) -> list[StateVector]:
        """Apply arrivalAirport and departureAirport filters, they require an api call since the data isn't part of StateVector."""
        
        logger.debug(f"Applying airport filters")
        
        if not hasattr(self, "fr24api"):
            self.fr24api = FlightRadar24API()
            
        airports:DataFrame = pd.read_csv("data/airports.csv")
        flights:list[Flight] = self.fr24api.get_flights(bounds=f"{self.bbox[1]},{self.bbox[0]},{self.bbox[2]},{self.bbox[3]}") # fr24api expects north, south, west, east 
        
        icao_from_iata = airports.dropna(subset=["iata"]).set_index("iata")["icao"]

        filtered_states = []
        for state in states:
            matched_flight:Flight|None = next((f for f in flights if f.icao_24bit.lower().strip() == state.icao24.lower().strip()), None)
            
            if matched_flight is None:
                continue

            # Flight stores its airport codes in IATA format but we need ICAO, convert using airports.csv
            if self.settings.departureAirport:

                departure_iata:str = matched_flight.origin_airport_iata
                try:
                    departure_icao:str = icao_from_iata[departure_iata]
                except:
                    continue
                
                if departure_icao.lower().strip() == self.settings.departureAirport.lower().strip():
                    filtered_states.append(state)

            if self.settings.arrivalAirport:                
                destination_iata:str = matched_flight.destination_airport_iata
                try:
                    destination_icao:str = icao_from_iata[destination_iata]
                except:
                    logger.debug(f"Arrival airport: {destination_iata} not found, continuing to next flight.")
                    continue
                
                if destination_icao.lower().strip() == self.settings.arrivalAirport.lower().strip():
                    print("adding state to filtered states")
                    if state not in filtered_states:
                        filtered_states.append(state)

        return filtered_states

    def extract_untracked_states(self, active_windows:dict[icao24,MainWindow],  new_states:list[StateVector]) -> list[StateVector]:
        active_icaos = active_windows.keys()
        
        untracked_states = []
        for state in new_states:
            if not state.icao24:
                continue
            
            if state.icao24 not in active_icaos:
                untracked_states.append(state)
        return untracked_states