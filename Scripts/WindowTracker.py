
from opensky_api import OpenSkyApi, StateVector, OpenSkyStates, FlightData, TokenManager

# Core Python imports
import time
import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, fields

# Custom imports
from Mover import Mover
from CustomQtWindow import MainWindow
from HandlingOpenSkyStates import fetchStatesInBbox, getBboxSize, getBboxOffset
from Utils.Helpers import windowIsOpen



@dataclass
class WindowTrackerConfig:
    # non-keyword arguments, required settings
    api:OpenSkyApi
    # location:str
    bboxAtLocation:tuple 
    
    # keyword arguments
    openskyCredentialsPath:str = "credentials.json"
    mover:Mover = Mover()
    apiCallDelay:float = 10
    bboxSize:str = ""
    latitudeOffset:float = 0.0
    longitudeOffset:float = 0.0
    maxWindows:int = 25
    displayName:str|None = None
    minVelocity:float = 0
    departureAirport:str = ""
    arrivalAirport:str = ""
    registrationCountry:str = ""
    callsign:str = ""
    airline:str = ""
    icao24:str = ""
    squawk:str = ""
    onGround:bool|None = None
    inAir:bool|None = None
    minBaroAltitude:float|None = None
    maxBaroAltitude:float|None = None
    minGeoAltitude:float|None = None
    maxGeoAltitude:float|None = None
    
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
            raise KeyError("Missing location in settings.")
        
        bboxAtLocation = cls.getBbox(location, settings)     
        filteredSettings = {key: value for key,value in settings.items() if key in validKeys}
        return cls(api, bboxAtLocation, **filteredSettings)

    @staticmethod
    def getBbox(location:str, settings:dict) -> tuple[float, float, float, float]:
        
        bboxSize  = settings.get("bboxSize")
        latOffset = settings.get("latitudeOffset")
        lonOffset = settings.get("longitudeOffset")

        hasBbox = bboxSize not in (None, "")
        hasLatOffset = latOffset is not None
        hasLonOffset = lonOffset is not None
        
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
        
        
class WindowTracker():
    def __init__(self, config:WindowTrackerConfig):
        self.config = config
        self.api            = config.api
        self.bboxAtLocation = config.bboxAtLocation
        self.mover          = config.mover
        self.maxWindows     = config.maxWindows
        self.displayName     = config.displayName
        
        self.windows:dict[str, MainWindow] = {}
        self.numApiCallsSkipped = 0.0
        self.newestApiUpdateTime = 0.0

    async def spawnWindow(self, state:StateVector) -> None:
        """Use spawns a window titled f\"qtApp_{state.icao24}\", also stores the  window in the windows dict with icao24 as key"""
        icao24 = state.icao24
        
        window = MainWindow(self.bboxAtLocation, state, self.mover, displayName = self.displayName)
        window.show()  # triggers QMainWindow.showEvent() 
        self.windows[icao24] = window
        # print(f"Now tracking {state.callsign}, {icao24=}")
        # await asyncio.sleep(0.2) #Delay between spawning windows

    async def updateWindows(self, newStates:list[StateVector]) -> None:
        """Spawn, update, or close windows based on current aircraft states."""
        newIcaos = {state.icao24 for state in newStates}

        for state in newStates:
            if state.icao24 in self.windows and windowIsOpen(state.icao24):
                self.windows[state.icao24].updateState(state)
            elif len(self.windows) < self.maxWindows:
                await self.spawnWindow(state)

        for icao24 in list(self.windows.keys()):
            if icao24 not in newIcaos:
                self.windows[icao24].close()
                print(f"Stopped tracking {icao24}")
                del self.windows[icao24]

    async def fetchLocationsLoop(self) -> None: 
            """keep track of icao24 codes, spawn one window per code in bbox, close window if aircraft flies out of bbox"""
            
            assert self.config.apiCallDelay >= 10.0, "Please select an apiCallDelay of at least 10 seconds."
            
            firstCall = True
            while True:
                if not firstCall:
                    await asyncio.sleep(self.config.apiCallDelay) # wait for at least 10 seconds so not ratelimited by OpenSkyApi
                firstCall = False
                
                newStates:OpenSkyStates|None = fetchStatesInBbox(self.api, self.bboxAtLocation)  
                
                if not newStates or not newStates.states:
                    print(f"New states are empty, continuing\n")
                    self.numApiCallsSkipped += 1
                    continue    # skip to next api call, else process exits.
                
                if newStates.time < self.newestApiUpdateTime: 
                    print(f"New states older than previous, continuing\n")
                    self.numApiCallsSkipped += 1
                    continue    # skip if new timestamp older than previous timestamp
                
                if newStates.time - self.newestApiUpdateTime <= 0.8*(self.numApiCallsSkipped + 1)*self.config.apiCallDelay: # TODO: this filter shouldn't apply to new aircraft appearing in bbox
                    print(f"New api call spacing too short, continuing\n")
                    self.numApiCallsSkipped += 1
                    continue    # skip if difference between timestamps is less than the elapsed real time
                
                self.newestApiUpdateTime = newStates.time
                self.numApiCallsSkipped  = 0.0  # reset
                
                print(f"\n\nNew states at {datetime.fromtimestamp(newStates.time)}\n")
                print(f"all new states: {[state.callsign for state in newStates.states]}")
                filteredNewStates = self.filterStates(newStates.states)
                await self.updateWindows(filteredNewStates)
                await asyncio.sleep(self.config.apiCallDelay) # wait for at least 10 seconds so not ratelimited by OpenSkyApi
  
    async def deadReckonLoop(self, dt:float=1.0) ->None:
        "Move windows in direction of true track with correct velocity every dt seconds"
        while True:
            t0 = time.monotonic()
            await asyncio.sleep(dt)
            dt = time.monotonic() - t0 # actual elapsed time
            for icao24, window in self.windows.items():
                if windowIsOpen(icao24):
                    window.deadReckonPosition(dt)
     
    def filterStates(self, states:list[StateVector]):
        states = self.applyLocalFilters(states)
        
        if self.config.departureAirport or self.config.arrivalAirport:
            states = self.applyApiFilters(states)
        
        return states    
         
    def applyLocalFilters(self, states:list[StateVector]):
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
        
    def filterStatesMinVelocity(self, states:list[StateVector], debugPrintFlag:bool = False):
        filteredStates = []
        for state in states:
            if state.velocity is not None:
                
                if not state.velocity >= self.config.minVelocity:
                        if debugPrintFlag: print(f"Filtered Callsign {state.callsign} because velocity too slow")
                else:
                    if debugPrintFlag: print(f"Callsign {state.callsign} passed velocity filter: {state.velocity}")
                    filteredStates.append(state)
                
        return filteredStates
        
    def applyApiFilters(self, states:list[StateVector]):
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
        
    async def runTracker(self) -> None:
        # spawn all windows for planes in bbox and matching filter criteria
        # filteredStates = self.filterStates(initialStates)
        # for state in filteredStates:
        #     await self.spawnWindow(state)
            
        # update the location of the windows / check for new/removed planes / check if windows were closed manually.        
        await asyncio.gather(self.fetchLocationsLoop(), self.deadReckonLoop())






    
