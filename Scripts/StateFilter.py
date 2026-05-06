
from opensky_api import StateVector, FlightData, OpenSkyApi

# Core imports
import time

# Custom imports
from CustomQtWindow import MainWindow
from WindowTrackerConfig import WindowTrackerConfig

type icao24 = str

class StateFilter():
    def __init__(self, config:WindowTrackerConfig, api:OpenSkyApi):
        self.config = config
        self.api = api
    
    def filterStates(self, states:list[StateVector]) -> list[StateVector]:
        states = self.applyLocalFilters(states)
        
        if self.config.departureAirport or self.config.arrivalAirport:
            states = self.applyApiFilters(states)
        
        return states    
         
    def applyLocalFilters(self, states:list[StateVector]) -> list[StateVector]:
        if self.config.minVelocity:
            print(f"Filtering for minVelocity: {self.config.minVelocity}")
            states = self.filterStatesMinVelocity(states, debugPrintFlag=True)
            
        if self.config.registrationCountry:
            print(f"Filtering for registration country: {self.config.registrationCountry}")
            filteredStates = []
            
            for state in states:
                if not state.origin_country:
                    continue
                
                if state.origin_country.lower().strip() == self.config.registrationCountry.lower().strip():
                    filteredStates.append(state)
                    
            states = filteredStates
        
        if self.config.callsign:
            print(f"Filtering for callsign {self.config.callsign}")
            states = [state for state in states if state.callsign and state.callsign.strip() == self.config.callsign]
            
        if self.config.airline:
            print(f"Filtering for airline: {self.config.airline}")
            states = [state for state in states if state.callsign is not None and state.callsign.lower().startswith(self.config.airline.lower())]
            
        if self.config.icao24:
            print(f"Filtering for icao24: {self.config.icao24}")
            states = [state for state in states if state.icao24.lower() == self.config.icao24.lower()]
        
        if self.config.squawk:
            print(f"Filtering for squawk: {self.config.squawk}")
            states = [state for state in states if state.squawk and state.squawk.lower().strip() == self.config.squawk.lower().strip()]
        
        if self.config.onGround == 1:
            print(f"Filtering for aircraft on the ground")
            states = [state for state in states if state.on_ground]
            
        if self.config.inAir == 1:
            print(f"Filtering for aircraft in the air")
            states = [state for state in states if not state.on_ground]
        
        if self.config.minBaroAltitude:
            print(f"Filtering for minBaroAltitude: {self.config.minBaroAltitude}")
            for state in states:
                if state.baro_altitude:
                    print(state.baro_altitude * 3.28084, state.callsign)
            
            states = [state for state in states if state.baro_altitude and state.baro_altitude*3.28084 >= self.config.minBaroAltitude] # convert from meters to feet
        
        if self.config.maxBaroAltitude:
            print(f"Filtering for maxBaroAltitude: {self.config.maxBaroAltitude}")
            states = [state for state in states if state.baro_altitude and state.baro_altitude*3.28084 <= self.config.maxBaroAltitude] # convert from meters to feet   
                 
        if self.config.minGeoAltitude:
            print(f"Filtering for minGeoAltitude: {self.config.minGeoAltitude}")
            states = [state for state in states if state.geo_altitude and state.geo_altitude*3.28084 >= self.config.minGeoAltitude] # convert from meters to feet

        if self.config.maxGeoAltitude:
            print(f"Filtering for maxGeoAltitude: {self.config.maxGeoAltitude}")
            states = [state for state in states if state.geo_altitude and state.geo_altitude*3.28084 <= self.config.maxGeoAltitude] # convert from meters to feet

        if self.config.maxWindows and len(states) >= self.config.maxWindows:
            print(f"Restricting number of windows to: {self.config.maxWindows}")
            states = states[:self.config.maxWindows]
        
        return states        
        
    def filterStatesMinVelocity(self, states:list[StateVector], debugPrintFlag:bool = False) -> list[StateVector]:
        filteredStates = []
        for state in states:
            if state.velocity is not None and self.config.minVelocity is not None:
                
                if not state.velocity >= self.config.minVelocity:
                        if debugPrintFlag: print(f"Filtered Callsign {state.callsign} because velocity too slow")
                else:
                    if debugPrintFlag: print(f"Callsign {state.callsign} passed velocity filter: {state.velocity}")
                    filteredStates.append(state)
                
        return filteredStates
        
    def applyApiFilters(self, states:list[StateVector]) -> list[StateVector]:
        print(f"Applying API filters")
        filteredStates = []
        t1 = int(time.time())
        t0 = t1 - 1*3600 # fetch flights in past x hours
            
        recentFlights:list[FlightData]|None = self.api.get_flights_from_interval(t0, t1)
        if not recentFlights:
            return states # failed request, don't apply filters
        
        icaos = [state.icao24 for state in states if state.icao24]
        stateMap = {state.icao24:state for state in states}
        
        for flight in recentFlights:
            state = stateMap.get(flight.icao24)
            
            if not state:
                continue # flight not in states
            
            estDepAirport = flight.estDepartureAirport
            estArrAirport = flight.estArrivalAirport
            
            if estDepAirport == self.config.departureAirport:
                    filteredStates.append(state)
                    
            if estArrAirport == self.config.arrivalAirport:
                if not state in filteredStates: # prevent dupes
                    filteredStates.append(state)
            
        states = filteredStates  
        return states        

    def extractUntrackedStates(self, activeWindows:dict[icao24,MainWindow],  newStates:list[StateVector]) -> list[StateVector]:
        activeIcaos = activeWindows.keys()
        
        untrackedStates = []
        for state in newStates:
            if not state.icao24:
                continue
            
            if state.icao24 not in activeIcaos:
                untrackedStates.append(state)
        
        return untrackedStates