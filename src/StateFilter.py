
from opensky_api import StateVector, OpenSkyApi

# Core imports
import time
import logging
logger = logging.getLogger(__name__)
from typing import TYPE_CHECKING
    
# Custom imports
from CustomQtWindow import MainWindow
if TYPE_CHECKING:
    from Settings import TrackingSettings

type icao24 = str
class StateFilter():
    """
    Filters OpenSky aircraft state vectors using opensky_api and local configuration settings.
    """
    def __init__(self, settings:"TrackingSettings", api:OpenSkyApi, maxWindows:int):
        """Initialize filter with tracking configuration, OpenSky API client, and maximum number of windows (default=25)"""
        
        self.settings:TrackingSettings = settings
        self.api:OpenSkyApi = api
        self.maxWindows = maxWindows
    
    def filterStates(self, states:list[StateVector]) -> list[StateVector]:
        
        states = self.applyLocalFilters(states)
        
        if self.settings.departureAirport or self.settings.arrivalAirport:
            states = self.applyApiFilters(states)
        
        assert self.maxWindows > 0.0, "maxWindows should be larger than 0"
        if len(states) >= self.maxWindows: # must be last filter
            logger.debug(f"Restricting number of windows to: {self.maxWindows}")
            states = states[:self.maxWindows]

        return states    
         
    def applyLocalFilters(self, states:list[StateVector]) -> list[StateVector]:
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
                
        if (settings.minVelocity is not None) or (settings.maxVelocity is not None):
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
        
        if settings.minBaroAltitude is not None:
            logger.debug(f"Filtering for minBaroAltitude: {settings.minBaroAltitude}")            
            states = [state for state in states if (state.baro_altitude is not None) and (state.baro_altitude*3.28084 >= settings.minBaroAltitude)] # convert from meters to feet
        
        if (settings.maxBaroAltitude is not None) and (settings.maxBaroAltitude > 0.0):
            logger.debug(f"Filtering for maxBaroAltitude: {settings.maxBaroAltitude}")
            states = [state for state in states if (state.baro_altitude is not None) and (state.baro_altitude*3.28084 <= settings.maxBaroAltitude)] # convert from meters to feet   
                 
        if settings.minGeoAltitude is not None:
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
    
    def applyApiFilters(self, states:list[StateVector]) -> list[StateVector]:
        """Apply the filters the require another call to the api like departureAirport as this data is not part of StateVector."""
        
        logger.debug(f"Applying API filters")
        filteredStates = []
        t1 = int(time.time())
        t0 = t1 - 24*3600 # fetch flights in past 24 hours
        stateMap = {state.icao24:state for state in states}
        matchedIcaos = set()
         
        if self.settings.departureAirport:
            departures = self.api.get_departures_by_airport(self.settings.departureAirport, t0, t1)
            if departures is None:
                logger.debug("Departure airport request failed — skipping departure filter")
            else:
                matchedIcaos.update(flight.icao24 for flight in departures if flight.icao24 in stateMap)

        if self.settings.arrivalAirport:
            logger.warning(f"arrivalAirport filtering is broken")
        
        if not matchedIcaos:
            logger.debug("No matching flights found for configured airports")
            return []

        filteredStates = [stateMap[icao] for icao in matchedIcaos]
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
        
        
        
        
        
        
        
        
        
    # # Leftover code for trying to make the arrival airport filter work:   
    
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

    # def getRouteCallsign(self, callsign:str) -> tuple[str, str]|None:
    #     r = requests.get(f"https://api.adsbdb.com/v0/callsign/{callsign.strip()}")
        
    #     if r.status_code != 200:
    #         return None
    #     # print(r.json())
    #     data = r.json().get("response", {}).get("flightroute")
    #     if not data:
    #         return None
        
    #     return (data["origin"]["icao_code"], data["destination"]["icao_code"])