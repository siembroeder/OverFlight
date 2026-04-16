
from opensky_api import OpenSkyApi, TokenManager, OpenSkyStates, OpenSkyApi, StateVector

from handlingOpenSkyStates import getBbox, fetchStatesInBbox
from managingWindows import renderAndUpdateWindows
from Mover import Mover





def main():

    api:OpenSkyApi = OpenSkyApi(token_manager=TokenManager.from_json_file("credentials.json"))


    # Set location, can be anything from jfk international airport to hilversum.
    locationName:str = "hilversum"
    
    # Define a small or large bboxsize, for dutch standards anyway.
    bboxAtLocation:tuple[float, float, float, float] = getBbox(locationName, BboxSize="small")            # print(f"{bboxAtLocation=})

    # Define the mover for the users operating system/session
    mover:Mover = Mover()

    # Fetch initial states
    statesAtLocationWTimestamp:OpenSkyStates|None = fetchStatesInBbox(api, bboxAtLocation)       # timestamp = statesAtLocation.time        # print(f"Planes in bbox:\n {statesAtLocationWTimestamp}")
    if statesAtLocationWTimestamp:
        statesAtLocation:list[StateVector] = statesAtLocationWTimestamp.states
    
        # Start the app
        app, windows = renderAndUpdateWindows(statesAtLocation, bboxAtLocation, api, mover, maxWindows=10)
    
    
    
        # other info:
        # typecodes:list = getTypeCodes(statesAtLocation)
        # tracks          = getTrueTracks(statesAtLocation)
        # classifications = printClassifications(typecodes)












































if __name__ == "__main__":
    main()
