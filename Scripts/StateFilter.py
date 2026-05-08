
from opensky_api import StateVector, OpenSkyApi

# Core imports
import time
import logging
import requests

# Custom imports
from CustomQtWindow import MainWindow
from WindowTrackerConfig import TrackingConfig

type icao24 = str
logger = logging.getLogger(__name__)
class StateFilter():
    def __init__(self, trackingConfig:TrackingConfig, api:OpenSkyApi, maxWindows:int):
        self.config = trackingConfig
        self.api = api
        self.maxWindows = maxWindows
    
    def filterStates(self, states:list[StateVector]) -> list[StateVector]:
        
        if self.config.departureAirport or self.config.arrivalAirport:
            states = self.applyApiFilters(states)
        
        states = self.applyLocalFilters(states)
        
        return states    
         
    def applyLocalFilters(self, states:list[StateVector]) -> list[StateVector]:
        if self.config.minVelocity:
            logger.debug(f"Filtering for minVelocity: {self.config.minVelocity}")
            states = self.filterStatesMinVelocity(states)
            
        if self.config.registrationCountry:
            logger.debug(f"Filtering for registration country: {self.config.registrationCountry}")
            filteredStates = []
            
            for state in states:
                if not state.origin_country:
                    continue
                
                if state.origin_country.lower().strip() == self.config.registrationCountry.lower().strip():
                    filteredStates.append(state)
                    
            states = filteredStates
        
        if self.config.callsign:
            logger.debug(f"Filtering for callsign {self.config.callsign}")
            states = [state for state in states if state.callsign and state.callsign.strip() == self.config.callsign]
            
        if self.config.airline:
            logger.debug(f"Filtering for airline: {self.config.airline}")
            states = [state for state in states if state.callsign is not None and state.callsign.lower().startswith(self.config.airline.lower())]
            
        if self.config.icao24:
            logger.debug(f"Filtering for icao24: {self.config.icao24}")
            states = [state for state in states if state.icao24.lower() == self.config.icao24.lower()]
        
        if self.config.squawk:
            logger.debug(f"Filtering for squawk: {self.config.squawk}")
            states = [state for state in states if state.squawk and state.squawk.lower().strip() == self.config.squawk.lower().strip()]
        
        if self.config.onGround == 1:
            logger.debug(f"Filtering for aircraft on the ground")
            states = [state for state in states if state.on_ground]
            
        if self.config.inAir == 1:
            logger.debug(f"Filtering for aircraft in the air")
            states = [state for state in states if not state.on_ground]
        
        if self.config.minBaroAltitude:
            logger.debug(f"Filtering for minBaroAltitude: {self.config.minBaroAltitude}")            
            states = [state for state in states if state.baro_altitude and state.baro_altitude*3.28084 >= self.config.minBaroAltitude] # convert from meters to feet
        
        if self.config.maxBaroAltitude:
            logger.debug(f"Filtering for maxBaroAltitude: {self.config.maxBaroAltitude}")
            states = [state for state in states if state.baro_altitude and state.baro_altitude*3.28084 <= self.config.maxBaroAltitude] # convert from meters to feet   
                 
        if self.config.minGeoAltitude:
            logger.debug(f"Filtering for minGeoAltitude: {self.config.minGeoAltitude}")
            states = [state for state in states if state.geo_altitude and state.geo_altitude*3.28084 >= self.config.minGeoAltitude] # convert from meters to feet

        if self.config.maxGeoAltitude:
            logger.debug(f"Filtering for maxGeoAltitude: {self.config.maxGeoAltitude}")
            states = [state for state in states if state.geo_altitude and state.geo_altitude*3.28084 <= self.config.maxGeoAltitude] # convert from meters to feet

        if len(states) >= self.maxWindows: # must be last filter
            logger.debug(f"Restricting number of windows to: {self.maxWindows}")
            states = states[:self.maxWindows]
        
        return states        
        
    def filterStatesMinVelocity(self, states:list[StateVector]) -> list[StateVector]:
        filteredStates = []
        for state in states:
            if state.velocity is not None and self.config.minVelocity is not None:
                
                if not state.velocity >= self.config.minVelocity:
                    logger.debug(f"Filtered Callsign {state.callsign} because velocity too slow")
                else:
                    logger.debug(f"Callsign {state.callsign} passed velocity filter: {state.velocity}")
                        
                    filteredStates.append(state)
                
        return filteredStates
            
    # def applyApiFilters(self, states:list[StateVector]) -> list[StateVector]:
    #     print(f"Applying API filters")
    #     filteredStates = []
    #     stateMap = {state.icao24:state for state in states}
    #     matchedIcaos = set()
            
    #     print(self.config.departureAirport, self.config.arrivalAirport)
    #     if self.config.departureAirport or self.config.arrivalAirport:
    #         for state in states:
    #             if state.callsign is None:
    #                 continue
                
    #             callsign = state.callsign.strip()
    #             route = self.getRouteCallsign(callsign)

    #             if route is None:
    #                 continue
                
    #             if route[0] == self.config.departureAirport or route[1] == self.config.arrivalAirport:
    #                 print(callsign, state.icao24, route)
    #                 matchedIcaos.add(state.icao24)
        
    #     if not matchedIcaos:
    #         return []

    #     filteredStates = [stateMap[icao] for icao in matchedIcaos]
    #     return filteredStates    
    
    def applyApiFilters(self, states:list[StateVector]) -> list[StateVector]:
        logger.info(f"Applying API filters")
        filteredStates = []
        t1 = int(time.time())
        t0 = t1 - 24*3600 # fetch flights in past 24 hours
        stateMap = {state.icao24:state for state in states}
        matchedIcaos = set()
         
        if self.config.departureAirport:
            departures = self.api.get_departures_by_airport(self.config.departureAirport, t0, t1)
            if departures is None:
                logger.info("Departure airport request failed — skipping departure filter")
            else:
                matchedIcaos.update(flight.icao24 for flight in departures if flight.icao24 in stateMap)

        if self.config.arrivalAirport:
            logger.warning(f"arrivalAirport filtering is broken")

        # if self.config.arrivalAirport:
        #     for icao24 in stateMap:
        #         if icao24 in matchedIcaos:
        #             continue  # already matched, skip the API call
                
        #         flights = self.api.get_flights_by_aircraft(icao24, t0, t1)
        #         if not flights:
        #             continue
        #         # Most recent flight is last in the list
        #         current_flight = flights[-1]
        #         if current_flight.estArrivalAirport == self.config.arrivalAirport:
        #             matchedIcaos.add(icao24)
        
        if not matchedIcaos:
            logger.info("No matching flights found for configured airports")
            return []

        filteredStates = [stateMap[icao] for icao in matchedIcaos]
        return filteredStates

    # def getRouteCallsign(self, callsign:str) -> tuple[str, str]|None:
    #     r = requests.get(f"https://api.adsbdb.com/v0/callsign/{callsign.strip()}")
        
    #     if r.status_code != 200:
    #         return None
    #     # print(r.json())
    #     data = r.json().get("response", {}).get("flightroute")
    #     if not data:
    #         return None
        
    #     return (data["origin"]["icao_code"], data["destination"]["icao_code"])

    def extractUntrackedStates(self, activeWindows:dict[icao24,MainWindow],  newStates:list[StateVector]) -> list[StateVector]:
        activeIcaos = activeWindows.keys()
        
        untrackedStates = []
        for state in newStates:
            if not state.icao24:
                continue
            
            if state.icao24 not in activeIcaos:
                untrackedStates.append(state)
        
        return untrackedStates