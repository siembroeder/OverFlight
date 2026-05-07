
from opensky_api import StateVector

# Custom imports
from StateFilter import StateFilter
from CustomQtWindow import MainWindow
from WindowTrackerConfig import WindowTrackerConfig
from Utils.Helpers import windowIsOpen

type icao24 = str
        
class WindowTracker():
    def __init__(self, config:WindowTrackerConfig):
        self.config = config
        
        self.api            = config.api
        self.bboxAtLocation = config.bboxAtLocation
        
        self.maxWindows     = config.setup.maxWindows
        self.apiCallDelay   = config.apiConfig.apiCallDelay
        
        self.filter = StateFilter(config.tracking, self.api, config.setup.maxWindows)
        
        self.windows:dict[icao24, MainWindow] = {}
        self.numApiCallsSkipped = 0.0
        self.newestStateTimestamp = 0.0

    def spawnWindow(self, state:StateVector) -> None:
        """Use spawns a window titled f\"qtApp_{state.icao24}\", also stores the  window in the windows dict with icao24 as key"""
        icao24 = state.icao24
        
        window = MainWindow(state, self.config)
        window.show()  # triggers QMainWindow.showEvent() 
        self.windows[icao24] = window                       # print(f"Now tracking {state.callsign}, {icao24=}")

    def updateWindows(self, newStates:list[StateVector], delete:bool = True) -> None:
        """Spawn, update, or close windows based on current aircraft states."""
        newIcaos = {state.icao24 for state in newStates}

        for state in newStates:
            if state.icao24 in self.windows and windowIsOpen(state.icao24):
                self.windows[state.icao24].updateState(state)
            elif len(self.windows) < self.maxWindows:
                self.spawnWindow(state)

        if delete:
            for icao24 in list(self.windows.keys()):
                if icao24 not in newIcaos:
                    self.windows[icao24].close()
                    print(f"Stopped tracking {icao24}")
                    del self.windows[icao24]
                          
    def deadReckonWindows(self, dt:float):
        for icao24, window in list(self.windows.items()):
            if windowIsOpen(icao24):
                window.deadReckonPosition(dt)


