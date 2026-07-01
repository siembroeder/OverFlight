import yaml
import logging
logger = logging.getLogger(__name__)
from dataclasses import fields

from settings import Settings
from state_filter import StateFilter
from custom_qt_window import MainWindow
from utils.qt_utils import window_is_open
from utils.aircraft_record import AircraftRecord

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
            
        # Register callback for settings that require WindowTracker method to execute
        settings.on_change("window_size", lambda _: self.close_all_windows()) # Windows are rebuild on next api call with updated windowSize
        settings.on_change("location", lambda _: self.close_all_windows())
        settings.on_change("bbox_size", lambda _: self.close_all_windows())

    def spawn_window(self, aircraft:AircraftRecord) -> None:
        """Use spawns a window titled f\"OverFlightWindow_{state.icao24}\", also stores the  window in the windows dict with icao24 as key"""
        window = MainWindow(self.settings, aircraft)
        window.mover.move_to_loc(window.latitude, window.longitude)
        window.show()  # triggers QMainWindow.showEvent() 
        self.windows[aircraft.state.icao24] = window

    def update_windows(self, new_aircraft:list[AircraftRecord], delete:bool = True) -> None:
    # def updateWindows(self, newStates:list[StateVector], delete:bool = True) -> None:
        """Spawn, update, or close windows based on current aircraft states.
           The delete flag can be set to False to prevent windows from being closed""" 
            
        # Delete windows that are no longer being tracked.
        new_icaos = [ac.state.icao24 for ac in new_aircraft]
        # newIcaos = [state.icao24 for state in newAircraft]
        if delete:
            for icao24 in list(self.windows.keys()):
                if icao24 not in new_icaos:
                    self.windows[icao24].close()
                    logger.debug(f"Stopped tracking {icao24}")
                    del self.windows[icao24] 
                    
        # Update existing windows and spawn new windows
        for ac in new_aircraft:
            state = ac.state
            icao24 = state.icao24
            if icao24 in self.windows:
                if window_is_open(icao24):
                    self.windows[icao24].update_state(state)
                else:
                    del self.windows[icao24]

            if icao24 not in self.windows and len(self.windows) < self.settings.setup.max_windows:
                self.spawn_window(ac)
                # typecode = self.icao24ToTypecode.get(icao24, self.settings.visuals.fallbackTypecode)
                # entry = self.typecodeToEntry.get(typecode) or Icao8643Entry.findByIcao24(icao24)
                # self.spawnWindow(AircraftRecord(state=state, entry=entry))
       
    def dead_reckon_windows(self):
        """Execute dead reckon increment for every open window currently being tracked"""
        for icao24, window in list(self.windows.items()):
            if window_is_open(icao24):
                window.mover.dead_reckon_increment()

    def close_all_windows(self):
        for window in self.windows.values():
            window.close()
        self.windows.clear()        
                
    def check_new_settings(self) -> bool:
        try:
            new_raw_settings = Settings.load_settings()
        except yaml.YAMLError as e:
            logger.error(f"Invalid yaml settings file: {e}")
            return False
        
        if new_raw_settings != self.settings.raw:
            new_settings = Settings.build()
            if new_settings:
                self.settings.apply_update(new_settings)
                return True
        
        return False
    
