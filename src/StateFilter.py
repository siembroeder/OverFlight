import time
import logging
logger = logging.getLogger(__name__)
import pandas as pd
from pandas import DataFrame
from typing import TYPE_CHECKING
    
from CustomQtWindow import MainWindow
from opensky_api import StateVector, OpenSkyApi
from utils.AircraftRecord import AircraftRecord
from FlightRadarAPI import FlightRadar24API, Flight

if TYPE_CHECKING:
    from Settings import TrackingSettings

type icao24 = str


class StateFilter():
    """
    Filters OpenSky aircraft state vectors using opensky_api and local configuration settings.
    """
    def __init__(self, settings:"TrackingSettings", api:OpenSkyApi, maxWindows:int, bbox:tuple):
        """Initialize filter with tracking configuration, OpenSky API client, and maximum number of windows (default=25)"""
        
        self.settings:TrackingSettings = settings
        self.api:OpenSkyApi = api
        self.maxWindows = maxWindows
        self.bbox = bbox
    
    def filterStates(self, states:list[StateVector]) -> list[StateVector]:
        
        # states = self.applyLocalFilters(states)
        
        if self.settings.departureAirport or self.settings.arrivalAirport:
            states = self.applyAirportFilters(states)
        

        return states    
    
    def filterAircraft(self, aircraft:list[AircraftRecord]) -> list[AircraftRecord]:
        
        # Filter by opensky statevector information
        states = [ac.state for ac in aircraft]
        states = self.applyLocalStateFilters(states)
        if self.settings.departureAirport or self.settings.arrivalAirport:
            states = self.applyAirportFilters(states)

        # Filter by icao8643 entry
        aircraft = [ac for ac in aircraft if ac.state in states]
        aircraft = self.applyIcaoEntryFilter(aircraft)

        assert self.maxWindows > 0.0, "maxWindows should be larger than 0"
        if len(aircraft) >= self.maxWindows: # must be last filter
            logger.debug(f"Restricting number of windows to: {self.maxWindows}")
            aircraft = aircraft[:self.maxWindows]
        
        return aircraft
    
    def applyIcaoEntryFilter(self, aircraft:list[AircraftRecord]) -> list[AircraftRecord]:
        settings = self.settings
        
        if settings.modelName:
            aircraft = [ac for ac in aircraft if ac.entry.modelFullName == settings.modelName]
            
        if settings.wtc:
            aircraft = [ac for ac in aircraft if ac.entry.wtc == settings.wtc]
            
        if settings.wtg:
            aircraft = [ac for ac in aircraft if ac.entry.wtg == settings.wtg]
            
        if settings.typecode:
            aircraft = [ac for ac in aircraft if ac.entry.typecode == settings.typecode]
        
        if settings.manufacturer:
            aircraft = [ac for ac in aircraft if ac.entry.manufacturerCode == settings.manufacturer]
        
        if settings.description:
            aircraft = [ac for ac in aircraft if ac.entry.aircraftDescription == settings.description]
        
        if settings.engineCount:
            aircraft = [ac for ac in aircraft if ac.entry.engineCount == settings.engineCount]
        
        if settings.engineType:
            aircraft = [ac for ac in aircraft if ac.entry.engineType == settings.engineType]

        return aircraft
         
    def applyLocalStateFilters(self, states:list[StateVector]) -> list[StateVector]:
        settings = self.settings
        filterTimestamp = time.monotonic()
        
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
            states = [state for state in states if (state.time_position is not None) and (state.time_position > (filterTimestamp - settings.allowedTimePositionLag))]
            
        if settings.allowedLastContactLag:
            logger.debug(f"Filtering for lastContactLag: {settings.allowedLastContactLag}")
            states = [state for state in states if state.last_contact > (filterTimestamp - settings.allowedLastContactLag)]
            
        if settings.originCountry:
            logger.debug(f"Filtering for registration country: {settings.originCountry}")
            states = [state for state in states if state.origin_country.lower().strip() == settings.originCountry.lower().strip()]
                
        if (settings.minVelocity) or (settings.maxVelocity):
            logger.debug(f"Filtering for velocity: minVelocity: {settings.minVelocity}, maxVelocity: {settings.maxVelocity}")
            states = self.filterStatesVelocity(states)
            
        if settings.trueTrackRange:
            logger.debug(f"Filtering for true track range: {settings.trueTrackRange}")
            states = self.filterStatesTrueTrackRange(states)
            
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
            states = self.filterStatesCategory(states)
            
        if settings.sensors:
            logger.debug(f"Filtering for sensors: {settings.sensors}")
            logger.warning(f"Untested, because the dev team doesn't have access to a paid openskyapi account")
            states = [state for state in states if (state.sensors) and any(sensor in settings.sensors for sensor in state.sensors)]
            
            
        return states        
           
    def filterStatesVelocity(self, states:list[StateVector]) -> list[StateVector]:
        """Helper function to filter states by velocity"""
        minVelocity = self.settings.minVelocity
        maxVelocity = self.settings.maxVelocity
        
        if (minVelocity is None) and (maxVelocity is None):
            return states
        
        filteredStates = []
        for state in states:
            
            if state.velocity is None:
                continue
                
            # apply minimum velocity filtering
            if (minVelocity is not None) and (state.velocity < minVelocity):
                # logger.debug(f"Filtered out callsign {state.callsign} because velocity too slow")
                continue
            
            # apply maximum velocity filtering
            if (maxVelocity is not None) and (maxVelocity > 0.0) and (state.velocity > maxVelocity):
                # logger.debug(f"Filtered out callsign {state.callsign} because velocity too fast")
                continue

            # logger.debug(f"Callsign {state.callsign} passed velocity filter: {state.velocity}")  
            filteredStates.append(state)
                
        return filteredStates

    def filterStatesTrueTrackRange(self, states:list[StateVector]) -> list[StateVector]:
        range = self.settings.trueTrackRange
        assert range is not None
        assert range[0] != range[1]

        filteredStates = []
        for state in states:
            if state.true_track is None:
                continue
            
            # Eg if range is [0, 90]
            if range[0] < range[1]:
                if (state.true_track >= range[0]) and (state.true_track <= range[1]):
                    filteredStates.append(state)

            # Eg if range is [350, 10], notice the 'or' conditional instead of 'and'
            elif range[0] > range[1]:
                if (state.true_track >= range[0]) or (state.true_track <= range[1]):
                    filteredStates.append(state) 
        
        return filteredStates
    
    def filterStatesCategory(self, states:list[StateVector]) -> list[StateVector]:
        if not self.settings.category:
            return states
        
        excludedCategories = []
        for cat in self.settings.category:
            if isinstance(cat, str) and (cat.startswith("!")):
                num = int(cat.lstrip("!"))
                excludedCategories.append(num)
        
        filteredStates = []
        for state in states:
            cat = state.category
            
            if excludedCategories and cat not in excludedCategories:
                filteredStates.append(state)
                            
            elif cat in self.settings.category:
                filteredStates.append(state)
        
        return filteredStates
    
    def applyAirportFilters(self, states:list[StateVector]) -> list[StateVector]:
        """Apply arrivalAirport and departureAirport filters, they require an api call since the data isn't part of StateVector."""
        
        logger.debug(f"Applying airport filters")
        
        if not hasattr(self, "fr24api"):
            self.fr24api = FlightRadar24API()
            
        airports:DataFrame = pd.read_csv("data/airports.csv")
        flights:list[Flight] = self.fr24api.get_flights(bounds=f"{self.bbox[1]},{self.bbox[0]},{self.bbox[2]},{self.bbox[3]}") # fr24api expects north, south, west, east 
        
        icao_from_iata = airports.dropna(subset=["iata"]).set_index("iata")["icao"]

        filteredStates = []
        for state in states:
            matchedFlight:Flight|None = next((f for f in flights if f.icao_24bit.lower().strip() == state.icao24.lower().strip()), None)
            
            if matchedFlight is None:
                continue

            # Flight stores its airport codes in IATA format but we need ICAO, convert using airports.csv
            if self.settings.departureAirport:
                print("hello")
                departure_iata:str = matchedFlight.origin_airport_iata
                try:
                    departure_icao:str = icao_from_iata[departure_iata]
                except:
                    continue
                
                if departure_icao.lower().strip() == self.settings.departureAirport.lower().strip():
                    filteredStates.append(state)

            if self.settings.arrivalAirport:                
                destination_iata:str = matchedFlight.destination_airport_iata
                try:
                    destination_icao:str = icao_from_iata[destination_iata]
                except:
                    logger.debug(f"Arrival airport: {destination_iata} not found, continuing to next flight.")
                    continue
                
                if destination_icao.lower().strip() == self.settings.arrivalAirport.lower().strip():
                    print("adding state to filtered states")
                    if state not in filteredStates:
                        filteredStates.append(state)

        return filteredStates

    def extractUntrackedStates(self, activeWindows:dict[icao24,MainWindow],  newStates:list[StateVector]) -> list[StateVector]:
        activeIcaos = activeWindows.keys()
        
        untrackedStates = []
        for state in newStates:
            if not state.icao24:
                continue
            
            if state.icao24 not in activeIcaos:
                untrackedStates.append(state)
        return untrackedStates