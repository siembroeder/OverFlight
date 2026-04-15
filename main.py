
from opensky_api import OpenSkyApi, TokenManager, OpenSkyStates, OpenSkyApi, StateVector

import sys
import json
import signal
import requests
from requests.models import Response
import subprocess
from datetime import datetime

from geopy.location import Location
from geopy.geocoders import Nominatim

import asyncio
from qasync import QEventLoop

from customQtWindow import MainWindow
from PyQt6.QtWidgets import QApplication



# coordinate/aircraft metadata functions
def getBbox(locationName:str, BboxSize:str) -> tuple[float, float, float, float]:

    geolocator:Nominatim = Nominatim(user_agent="appname")
    location:Location    = geolocator.geocode(locationName)
    
    if location:
        latitude = location.latitude
        longitude= location.longitude
        print(f"{location}\'s coordinates are: {location.latitude}, {location.longitude}")
    else:
        raise NameError("No bbox found.")
     

    BboxSizes:dict[str, dict] = {"small": {"latitudeOffset": 0.15, "longitudeOffset": 0.25},
                                 "large": {"latitudeOffset": 0.3,  "longitudeOffset": 0.5}}

    latitudeOffset:dict  =  BboxSizes[BboxSize]["latitudeOffset"]
    longitudeOffset:dict = BboxSizes[BboxSize]["longitudeOffset"]

    minLat:float  = latitude - latitudeOffset
    maxLat:float  = latitude + latitudeOffset
    minLong:float = longitude- longitudeOffset
    maxLong:float = longitude+ longitudeOffset
    
    return (minLat, maxLat, minLong, maxLong)

def fetchStatesInBbox(api:OpenSkyApi, bbox:tuple) -> OpenSkyStates|None:
    states:OpenSkyStates|None = api.get_states(bbox = bbox)
    return states

def getAircraftMeta(icao24: str, username: str, password: str) -> dict:
    url:str = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao24}"
    response:Response = requests.get(url, auth=(username, password))
    
    if response.status_code == 200:
        return response.json()
    return {}

def getTypeCodes(states:list[StateVector], printCodes:bool = False) -> list[str]:
    typecodes:list = []
    for state in states:
        meta:dict = getAircraftMeta(state.icao24, "", "") # The empty strings are the username and password for the api call ... ?!
        
        # print(f"{meta=}")
        
        typecode = meta.get("typecode")
        typecodes.append(typecode)

        if printCodes:
            print(state.callsign, typecode, meta.get("model"))

    return typecodes

def printClassifications(typecodes:list[str], printClassifications = False) -> None:
    
    with open("AircraftData/AircraftClassifications.json") as file:
        
        aircraftClassifications = json.load(file)

        if printClassifications: print("\nClassifications:")
        for typecode in typecodes:
            try:
                classification = aircraftClassifications[typecode]
                wake = classification["wake"]
                if printClassifications: print(f"Type \'{typecode}\' found, classification: {wake}")
            except:
                if printClassifications: print(f"Type \'{typecode}\' not found, continuing")
                pass

def getTrueTracks(states:list[StateVector]) -> list[float]:
    tracks:list = []
    for state in states:
        tracks.append(state.true_track) # True_track, can be null.
    return tracks
   
   



# window functions   
async def spawnWindow(state:StateVector, bboxAtLocation:tuple, windows:dict, screenName:str="eDP-1") -> None:
    """Use spawns a window titled f\"qtApp_{icao24}\" using hyprctl and qt, also stores the new window in the windows dict with icao24 as key"""
    icao24 = state.icao24
    subprocess.run(['hyprctl', 'keyword', 'windowrule', f'match:title qtApp_{icao24}, monitor {screenName}, float on'], capture_output=True)
    window = MainWindow(bboxAtLocation, (state.longitude, state.latitude), icao24, state.callsign, showOnScreenName = screenName)
    window.show()  # triggers showEvent 
    windows[icao24] = window
    await asyncio.sleep(0.5)

def windowIsOpen(icao24:str) -> bool:
    title = f"qtApp_{icao24}"
    # return any(w.windowTitle() == title for w in QApplication.topLevelWidgets())
    return any(w.windowTitle() == title and w.isVisible() for w in QApplication.topLevelWidgets())

async def fetchAndUpdateLocationsLoop(api:OpenSkyApi, bboxAtLocation:tuple, windows:dict, maxWindows:int, screenName:str="eDP-1") -> None: 
    """keep track of icao24 codes, spawn one window per code in bbox, close window if aircraft flies out of bbox"""
    while True:
        await asyncio.sleep(10) # wait for 10 seconds so not ratelimited by OpenSkyApi
        
        newStates = fetchStatesInBbox(api, bboxAtLocation)        
        if not newStates or not newStates.states:
            continue # skip to next api call, else process exits.
        
        print(f"\nNew states at {datetime.fromtimestamp(newStates.time).strftime("%Y-%m-%d %H:%M:%S")}")
        newIcaos = {state.icao24 for state in newStates.states}
        
        for state in newStates.states:
            if state.icao24 in windows:
                if windowIsOpen(state.icao24):
                    windows[state.icao24].moveToPlaneLoc((state.longitude, state.latitude))
                else:
                    await spawnWindow(state, bboxAtLocation, windows, screenName)

            elif len(windows) < maxWindows: # if allowed spawn another window
                await spawnWindow(state, bboxAtLocation, windows, screenName=screenName) 
                
        # Remove planes that have moved out of the bbox
        for icao24 in list(windows.keys()):
            if icao24 not in newIcaos:
                windows[icao24].close()
                del windows[icao24]
    
def renderAndUpdateStates(states:list[StateVector], bboxAtLocation:tuple, api:OpenSkyApi, maxWindows:int=3, screenName:str="eDP-1"):
    """ spawn the windows asynchronously, wait for 10 seconds before api call, update locations asynchronously."""
    app:QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    loop:QEventLoop  = QEventLoop(app)
    asyncio.set_event_loop(loop)
    loop.add_signal_handler(signal.SIGINT, QApplication.quit) # quit with CTRL+C from terminal

    windows:dict[str, MainWindow] = {}
       
       
       
    async def runApp():
        # spawn all windows for planes in bbox
        for index, state in enumerate(states[:maxWindows], start=1):
            await spawnWindow(state, bboxAtLocation, windows, screenName)
            
        # update te location of the windows / check for new/removed planes / check if windows were closed manually.
        await fetchAndUpdateLocationsLoop(api, bboxAtLocation, windows, maxWindows, screenName)   
    
    
    # Ensure the program doesn't exit when all windows are closed:
    app.aboutToQuit.connect(loop.stop)
    with loop:
        asyncio.ensure_future(runApp())
        loop.run_forever()
    
    
                 
    return app, windows # keep reference to prevent them from being garbage collected
    









def main():

    api:OpenSkyApi = OpenSkyApi(token_manager=TokenManager.from_json_file("credentials.json"))


    # Set location, can be anything from jfk international airport to hilversum.
    locationName:str = "hilversum"
    
    # Define a small or large bboxsize, for dutch standards anyway.
    bboxAtLocation:tuple[float, float, float, float] = getBbox(locationName, BboxSize="small")            # print(f"{bboxAtLocation=})


    # Fetch initial states
    statesAtLocationWTimestamp:OpenSkyStates|None = fetchStatesInBbox(api, bboxAtLocation)       # timestamp = statesAtLocation.time        # print(f"Planes in bbox:\n {statesAtLocationWTimestamp}")
    if statesAtLocationWTimestamp:
        statesAtLocation:list[StateVector] = statesAtLocationWTimestamp.states
    
        # Start the app
        app, windows = renderAndUpdateStates(statesAtLocation, bboxAtLocation, api, maxWindows=10)
    
    
    
        # other info:
        # typecodes:list = getTypeCodes(statesAtLocation)
        # tracks          = getTrueTracks(statesAtLocation)
        # classifications = printClassifications(typecodes)







if __name__ == "__main__":
    main()
