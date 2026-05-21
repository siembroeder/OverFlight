import os
import math
import time
import logging
logger = logging.getLogger(__name__)
import subprocess

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from CustomQtWindow import MainWindow
    
from utils.PlatformUtils import getUserPlatform, getSessionType, getWindowManager
from utils.TypeHints import Meters, Degrees, Radians, MetersPerSecond, Latitude, Longitude, asLatitude, asLongitude


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
        self.systemDependentMover = self.determineMover()
        
        # values used for deadreckoning 
        self.dlatStep = Latitude(0.0)
        self.dlonStep = Longitude(0.0)
      
    def determineMover(self):
        """
        Selects the sub-Mover class corresponding to the user's specs
        """
        userPlatform = getUserPlatform()
        
        if "windows" in userPlatform:
            return WindowsMover()
        
        elif "darwin" in userPlatform:
            return MacOSMover()
            
        elif "linux" in userPlatform:
            self.userSession  = getSessionType() 
            if self.userSession == "x11":
                return X11Mover()
            
            elif self.userSession == "wayland":     
                wm = getWindowManager().lower()

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
        return self.systemDependentMover.move(x, y, self.window)

    def coordsToPixels(self, lat:Latitude, lon:Longitude) -> tuple[int, int]:
        """ 
        Convert the coordinate (lat, lon) in the boundingbox to a location on the screen (pixelx, pixely)
        """
        
        minLat, maxLat, minLon, maxLon = self.window.settings.bboxAtLocation
        
        # normalize to 0-1 and multiply with number of available pixels
        pixelx = int(((lon - minLon) / (maxLon - minLon) ) * self.window.Nxpixels)
        pixely = int(((lat - minLat)  / (maxLat - minLat)   ) * self.window.Nypixels) # print(f"{[pixelx,pixely]=}")
        
        # invert y axis
        pixely = self.window.Nypixels - pixely    
        
        # offset to selected display
        pixelx += self.window.screenOrigin.x()
        pixely += self.window.screenOrigin.y()   
         
        return pixelx, pixely

    def moveToLoc(self, latitude:Latitude|None, longitude:Longitude|None) -> None:
        """Move self.window to coordinate (lat, lon) that's mapped to screen and center the image"""
        
        if (latitude is None) or (longitude is None):
            return
        
        pixelx, pixely = self.coordsToPixels(latitude, longitude)
    
        # Center image
        pixelx = int(pixelx - (self.window.width() / 2))
        pixely = int(pixely - (self.window.height()/ 2))
        
        self.move(pixelx, pixely)         # print(f"Moving {self.callsign} to {self.pixelx}, {self.pixely}")        

    def calculatePositionAtNextApiCall(self) -> tuple[Latitude, Longitude]:

        if (self.window.velocity is None) or (self.window.true_track is None):
            logger.warning("velocity or true_track (heading) not defined")
            return (Latitude(0.0), Longitude(0.0))
        
        if (self.window.latitude is None) or (self.window.longitude is None):
            logger.warning("Latitude or Longitude not defined")
            return (Latitude(0.0), Longitude(0.0))
        
        lat:Latitude = self.window.latitude 
        lon:Longitude = self.window.longitude
        
        velocity:MetersPerSecond = self.window.velocity
        distanceTraveledAtNextApiCall:Meters = Meters(velocity * self.window.settings.api.apiCallDelay)
        
        # Use flat earth approximation for converting from meters to degrees of lat/lon
        heading:Degrees = self.window.true_track
        headingRadians:Radians = Radians(math.radians(heading))
        dlatNextCall:Latitude = Latitude((distanceTraveledAtNextApiCall * math.cos(headingRadians)) / 111_320)
        dlonNextCall:Longitude = Longitude((distanceTraveledAtNextApiCall * math.sin(headingRadians)) / (111_320 * math.cos(math.radians(lat))))
        
        nextPosition= (Latitude(lat+dlatNextCall), Longitude(lon+dlonNextCall))
        return nextPosition
    
    def updateDeadReckonIncrements(self):
        
        if (self.window.latitude is None) or (self.window.longitude is None):
            return
        
        nextLat, nextLon = self.calculatePositionAtNextApiCall()
        
        # update deadreckoning increments
        self.dlatStep:Latitude = Latitude((nextLat - self.window.latitude) / self.steps)
        self.dlonStep:Longitude = Longitude((nextLon - self.window.longitude) / self.steps)
            
    def deadReckonIncrement(self):
        """
        Move self.window to next step in deadreckoning process
        """
                  
        if (self.window.true_track is None) or (self.window.velocity is None):
            return
    
        if time.monotonic() - self.window.lastApiUpdate < 0.75 * self.window.settings.visuals.updateInterval:
            return  # skip to prevent jittery updates
        
        if (self.window.latitude is None) or (self.window.longitude is None):
            return
  
        # increment lat and lon
        self.window.latitude = asLatitude(self.window.latitude + self.dlatStep)
        self.window.longitude= asLongitude(self.window.longitude + self.dlonStep)
           
        self.moveToLoc(self.window.latitude, self.window.longitude)


    @property
    def steps(self) -> float:
        """
        Number of steps of deadreckoning in between api calls. 
        Use @property decorator to set self.steps but let it always depend on current self.window.settings vars
        """
        return self.window.settings.api.apiCallDelay / self.window.settings.visuals.updateInterval





    
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

class MacOSMover:
    def move(self, x:int, y:int, window:"MainWindow"):
        window.move(x, y)