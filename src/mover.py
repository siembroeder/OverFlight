import os
import math
import time
import logging
logger = logging.getLogger(__name__)
import subprocess

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from custom_qt_window import MainWindow
    
from utils.platform_utils import get_user_platform, get_session_type, get_window_manager
from utils.type_hints import Meters, Degrees, Radians, MetersPerSecond, Latitude, Longitude, asLatitude, asLongitude


class Mover():
    """
    Responsible for moving a single MainWindow around.
    Keeps track of window.latitude/longitude and of how to move the window in between api calls (dead reckoning).
    
    Reads the user's platform and session, eg Linux and Hyprland and selects the correct .move function eg HyprlandMover.move()
    
    
    The goal is to move to the predicted location of the window at the next api call. 
    If the next call doesn't come in for some reason (eg bad data) continue in direction it was already going
    """
        
    def __init__(self, window:"MainWindow"):
        self.window = window
        self.system_dependent_mover = self.determine_mover()
        
        # values used for deadreckoning 
        self.d_step_lat = Latitude(0.0)
        self.d_step_lon = Longitude(0.0)
      
    def determine_mover(self):
        """
        Selects the sub-Mover class corresponding to the user's specs
        """
        user_platform = get_user_platform()
        
        if "windows" in user_platform:
            return WindowsMover()
            
        elif "linux" in user_platform:
            self.user_session  = get_session_type() 
            if self.user_session == "x11":
                return X11Mover()
            
            elif self.user_session == "wayland":     
                wm = get_window_manager().lower()

                if "hyprland" in wm:
                    return HyprlandMover()
                if "wlroots" in wm:
                    desktop = os.environ.get("XDG_CURRENT_DESKTOP")
                    if (desktop is not None) and "sway" in desktop:
                        return SwayMover()
                    else:
                        raise NotImplementedError("Your wm is not supported.")     
                else:
                    raise NotImplementedError("Your wm is not supported.")     
                
            else:
                raise NotImplementedError("Your session is not supported.")  
                
        else:
            raise NotImplementedError("Your operating system is not supported")
                        
    def move(self, x:int, y:int):
        return self.system_dependent_mover.move(x, y, self.window)

    def coords_to_pixels(self, lat:Latitude, lon:Longitude) -> tuple[int, int]:
        """ 
        Convert the coordinate (lat, lon) in the boundingbox to a location on the screen (pixelx, pixely)
        """
        
        min_lat, max_lat, min_lon, max_lon = self.window.settings.bbox_at_location
        
        # normalize to 0-1 and multiply with number of available pixels
        pixel_x = int(((lon - min_lon) / (max_lon - min_lon) ) * self.window.Nxpixels)
        pixel_y = int(((lat - min_lat)  / (max_lat - min_lat)   ) * self.window.Nypixels) # print(f"{[pixelx,pixely]=}")
        
        # invert y axis
        pixel_y = self.window.Nypixels - pixel_y    
        
        # offset to selected display
        pixel_x += self.window.screenOrigin.x()
        pixel_y += self.window.screenOrigin.y()   
         
        return pixel_x, pixel_y

    def move_to_loc(self, latitude:Latitude|None, longitude:Longitude|None) -> None:
        """Move self.window to coordinate (lat, lon) that's mapped to screen and center the image"""
        
        if (latitude is None) or (longitude is None):
            return
        
        pixel_x, pixel_y = self.coords_to_pixels(latitude, longitude)
    
        # Center image
        pixel_x = int(pixel_x - (self.window.width() / 2))
        pixel_y = int(pixel_y - (self.window.height()/ 2))
        
        self.move(pixel_x, pixel_y)

    def calculate_position_at_next_api_call(self) -> tuple[Latitude, Longitude]:

        if (self.window.velocity is None) or (self.window.true_track is None):
            logger.warning("velocity or true_track (heading) not defined.")
            return (Latitude(0.0), Longitude(0.0))
        
        if (self.window.latitude is None) or (self.window.longitude is None):
            logger.warning("latitude or longitude not defined.")
            return (Latitude(0.0), Longitude(0.0))
        
        lat:Latitude = self.window.latitude 
        lon:Longitude = self.window.longitude
        
        velocity:MetersPerSecond = self.window.velocity
        distance_traveled_at_next_api_call:Meters = Meters(velocity * self.window.settings.api.api_call_delay)
        
        # Use flat earth approximation for converting from meters to degrees of lat/lon
        heading:Degrees = self.window.true_track
        heading_radians:Radians = Radians(math.radians(heading))
        d_lat_next_call:Latitude = Latitude((distance_traveled_at_next_api_call * math.cos(heading_radians)) / 111_320)
        d_lon_next_call:Longitude = Longitude((distance_traveled_at_next_api_call * math.sin(heading_radians)) / (111_320 * math.cos(math.radians(lat))))
        
        next_position = (Latitude(lat+d_lat_next_call), Longitude(lon+d_lon_next_call))
        return next_position
    
    def update_dead_reckon_increments(self):
        
        if (self.window.latitude is None) or (self.window.longitude is None):
            return
        
        next_lat, next_lon = self.calculate_position_at_next_api_call()
        
        # update deadreckoning increments
        self.d_step_lat:Latitude = Latitude((next_lat - self.window.latitude) / self.steps)
        self.d_step_lon:Longitude = Longitude((next_lon - self.window.longitude) / self.steps)
            
    def dead_reckon_increment(self):
        """
        Move self.window to next step in deadreckoning process
        """
                  
        if (self.window.true_track is None) or (self.window.velocity is None):
            return
    
        if time.monotonic() - self.window.lastApiUpdate < 0.75 * self.window.settings.visuals.update_interval:
            return  # skip to prevent jittery updates
        
        if (self.window.latitude is None) or (self.window.longitude is None):
            return
  
        # increment lat and lon
        self.window.latitude = asLatitude(self.window.latitude + self.d_step_lat)
        self.window.longitude= asLongitude(self.window.longitude + self.d_step_lon)
           
        self.move_to_loc(self.window.latitude, self.window.longitude)


    @property
    def steps(self) -> float:
        """
        Number of steps of deadreckoning in between api calls. 
        Use @property decorator to set self.steps but let it always depend on current self.window.settings vars
        """
        return self.window.settings.api.api_call_delay / self.window.settings.visuals.update_interval





    
class WindowsMover:
    def move(self, x:int, y:int, window:"MainWindow"):
        window.move(x, y)

class X11Mover:
    def move(self, x:int, y:int, window:"MainWindow"):
        window.move(x, y)

class HyprlandMover:
    def move(self, x:int, y:int, window:"MainWindow"):
        # # Hyprland version 0.55:
        # subprocess.run(["hyprctl", "dispatch", "hl.dsp.window.move",
        #                 f"{{ x = {x}, y = {y}, window = 'title:{window.windowTitle()}' }}"],
        #                 capture_output=True)

        # Old hyprlang version, as of hyprland 0.55 moved to lua instead.
        subprocess.run(['hyprctl', 'dispatch', 'movewindowpixel', f'exact {x} {y},title:{window.windowTitle()}'], capture_output=True) # ^(qtApp)$
        
class SwayMover:
    def move(self, x:int, y:int, window:"MainWindow"):
        subprocess.run(['swaymsg', f'[title="^{window.windowTitle()}$"] move absolute position {x} {y}'], capture_output=True)