import json
import logging
logger = logging.getLogger(__name__)
from dataclasses import fields

from Settings import Settings
from opensky_api import StateVector
from StateFilter import StateFilter
from utils.QtUtils import windowIsOpen
# from utils.OpenSkyUtils import getAllTypeCodes
from CustomQtWindow import MainWindow, WindowConfig
from utils.Icao8643Utils import Icao8643Entry

type Icao24 = str
type Typecode = str

        
class WindowTracker():
    """
    Responsible for tracking which opensky states are being tracked, 
                for opening and closing windows when they enter/leave the bounding box
    """
    
    def __init__(self, settings:Settings):
        self.settings = settings
        self.windows:dict[Icao24, MainWindow] = {}
        self.filter = StateFilter(settings.tracking, settings.openSkyApi, settings.setup.maxWindows, settings.bboxAtLocation)
        
        for f in fields(settings.tracking): # if any field in settings.tracking changes, rebuild the filter completely
            settings.onChange(f.name, lambda _: self.rebuildFilter())
            
        # Register callback for settings that require WindowTracker method to execute
        settings.onChange("windowSize", lambda _: self.CloseAllWindows()) # Windows are rebuild on next api call with updated windowSize

        self.icao24ToTypecode:dict[str, str]          = Icao8643Entry.loadIcao24Typecodes()
        self.typecodeToEntry:dict[str, Icao8643Entry] = Icao8643Entry.loadTypecodes()

    def spawnWindow(self, windowConfig:WindowConfig) -> None:
        """Use spawns a window titled f\"OverFlightWindow_{state.icao24}\", also stores the  window in the windows dict with icao24 as key"""
        window = MainWindow(self.settings, windowConfig)
        window.mover.moveToLoc(window.latitude, window.longitude)
        window.show()  # triggers QMainWindow.showEvent() 
        self.windows[windowConfig.state.icao24] = window

    def updateWindows(self, newStates:list[StateVector], delete:bool = True) -> None:
        """Spawn, update, or close windows based on current aircraft states.
           The delete flag can be set to False to prevent windows from being closed"""
            
        # Delete windows that are no longer being tracked.
        newIcaos = [state.icao24 for state in newStates]
        if delete:
            for icao24 in list(self.windows.keys()):
                if icao24 not in newIcaos:
                    self.windows[icao24].close()
                    logger.debug(f"Stopped tracking {icao24}")
                    del self.windows[icao24] 
                    
        # Update existing windows and spawn new windows
        for state in newStates:
            icao24 = state.icao24
            if icao24 in self.windows:
                if windowIsOpen(icao24):
                    self.windows[icao24].updateState(state)
                else:
                    del self.windows[icao24]

            if icao24 not in self.windows and len(self.windows) < self.settings.setup.maxWindows:
                typecode = self.icao24ToTypecode.get(icao24, self.settings.visuals.fallbackTypecode)
                entry = self.typecodeToEntry.get(typecode) or Icao8643Entry.findByIcao24(icao24)
                self.spawnWindow(WindowConfig(state=state, entry=entry))

            # if icao24 not in self.windows and len(self.windows) < self.settings.setup.maxWindows:
            #     entry:Icao8643Entry = Icao8643Entry.findByIcao24(icao24, self.settings.visuals.fallbackTypecode)
            #     config = WindowConfig(state=state, entry=entry)
            #     self.spawnWindow(config)

        # spawningIcaos = [icao for icao in newIcaos if icao not in self.windows.keys()]
        # spawningTypecodes:dict[Icao24, Typecode] = getAllTypeCodes(spawningIcaos)
        # for state in newStates:
        #     icao24 = state.icao24
            
        #     if icao24 in self.windows:
        #         if windowIsOpen(icao24):
        #             self.windows[icao24].updateState(state)
        #         else:
        #             del self.windows[icao24] # delete to respawn
        #             spawningIcaos.append(icao24)
        #             spawningTypecodes = getAllTypeCodes(spawningIcaos)
                
        #     if icao24 not in self.windows and len(self.windows) < self.settings.setup.maxWindows:
        #         typecode = spawningTypecodes.get(icao24, self.settings.visuals.fallbackTypecode)
        #         entry:Icao8643Entry = Icao8643Entry.findEntry(typecode, self.settings.visuals.fallbackTypecode)
        #         self.spawnWindow(WindowConfig(state = state, entry = entry))
       
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
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in settings file: {e}")
            return False
        
        isUpdated = False
        if newRawSettings != self.settings.raw:
            try:
                newSettings = Settings.build()
                self.settings.applyUpdate(newSettings)
                isUpdated = True
            except (KeyError, TypeError, ValueError) as e:
                logger.error(f"Invalid settings values: {e}")
                return False
        
        return isUpdated
    
