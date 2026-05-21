
import logging
logger = logging.getLogger(__name__)
from dataclasses import fields

import yaml
from opensky_api import StateVector
from StateFilter import StateFilter
from CustomQtWindow import MainWindow
from utils.QtUtils import windowIsOpen
from Settings import Settings

type icao24 = str

        
class WindowTracker():
    """
    Responsible for tracking which opensky states are being tracked, 
                for opening and closing windows when they enter/leave the bounding box
    """
    
    def __init__(self, settings:Settings):
        self.settings = settings
        self.windows:dict[icao24, MainWindow] = {}
        self.filter = StateFilter(settings.tracking, settings.openSkyApi, settings.setup.maxWindows, settings.bboxAtLocation)
        
        for f in fields(settings.tracking): # if any field in settings.tracking changes, rebuild the filter completely
            settings.onChange(f.name, lambda _: self.rebuildFilter())
            
        # Register callback for settings that require WindowTracker method to execute
        settings.onChange("windowSize", lambda _: self.CloseAllWindows()) # Windows are rebuild on next api call with updated windowSize

    def spawnWindow(self, state:StateVector) -> None:
        """Use spawns a window titled f\"OverFlightWindow_{state.icao24}\", also stores the  window in the windows dict with icao24 as key"""
        icao24 = state.icao24
        
        window = MainWindow(state, self.settings)
        window.mover.moveToLoc(window.latitude, window.longitude)
        window.show()  # triggers QMainWindow.showEvent() 
        self.windows[icao24] = window                       # print(f"Now tracking {state.callsign}, {icao24=}")

    def updateWindows(self, newStates:list[StateVector], delete:bool = True) -> None:
        """Spawn, update, or close windows based on current aircraft states.
           The delete flag can be set to False to prevent windows from being closed"""
                
        newIcaos = {state.icao24 for state in newStates}

        # Update existing windows and spawn new windows
        for state in newStates:
            if state.icao24 in self.windows and windowIsOpen(state.icao24):
                self.windows[state.icao24].updateState(state)
            elif len(self.windows) < self.settings.setup.maxWindows:
                self.spawnWindow(state)
                
        # Delete windows that are no longer being tracked. 
        if delete:
            for icao24 in list(self.windows.keys()):
                if icao24 not in newIcaos:
                    self.windows[icao24].close()
                    logger.debug(f"Stopped tracking {icao24}")
                    del self.windows[icao24] 
                    
    def deadReckonWindows(self):
        """Execute dead reckon increment for every open window currently being tracked"""
        for icao24, window in list(self.windows.items()):
            if windowIsOpen(icao24):
                window.mover.deadReckonIncrement()
                
    def rebuildFilter(self):
        self.filter = StateFilter(self.settings.tracking, self.settings.openSkyApi, self.settings.setup.maxWindows, self.settings.bboxAtLocation)

    def CloseAllWindows(self):
        for window in self.windows.values():
            window.close()
        self.windows.clear()        
                
    def checkNewSettings(self) -> bool:
        try:
            newRawSettings = Settings.loadSettings()
        except yaml.YAMLError as e:
            logger.error(f"Invalid yaml settings file: {e}")
            return False
        
        if newRawSettings != self.settings.raw:
            newSettings = Settings.build()
            if newSettings:
                self.settings.applyUpdate(newSettings)
                return True
        
        return False
    
