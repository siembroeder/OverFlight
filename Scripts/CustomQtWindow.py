from opensky_api import StateVector

# Core Python imports
import math
import time

# PyQt imports
from PyQt6.QtGui import QPixmap, QMovie
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel, QWidget, QToolTip

# Custom imports
from typing import TYPE_CHECKING        # to prevent circular dependency 
if TYPE_CHECKING:
    from Mover import Mover
   

class MainWindow(QMainWindow): 
    def __init__(self, bbox:tuple, state:StateVector, mover: "Mover", displayName:str|None=None):
        super().__init__()
        

        
        self.mover = mover
        self.state = state
        self.icao24 = state.icao24
        self.callsign = state.callsign
        self.velocity = state.velocity  # m/s
        self.heading  = state.true_track
        self.lastApiUpdate = time.monotonic()
        if state.longitude is None or state.latitude is None:
            return
        self.longitude, self.latitude = (state.longitude, state.latitude)
        self.minLat, self.maxLat, self.minLong, self.maxLong = bbox
        
        screens = QApplication.screens()
        if displayName == 'all': 
            self.primaryScreen = QApplication.primaryScreen()
            if self.primaryScreen is not None:
                self.virtual_geom = self.primaryScreen.virtualGeometry()
                self.Nxpixels = self.virtual_geom.getCoords()[2] + 1
                self.Nypixels = self.virtual_geom.getCoords()[3] + 1            #print(f"{self.virtual_geom=}")
        else:
            for screen in screens:
                if not displayName: # set dimensions to first screen
                    self.availableGeometry = screen.availableGeometry()
                    self.Nxpixels, self.Nypixels = self.availableGeometry.width(), self.availableGeometry.height()
                    break 
                elif screen.name() == displayName:
                    self.availableGeometry = screen.availableGeometry()
                    self.Nxpixels, self.Nypixels = self.availableGeometry.width(), self.availableGeometry.height() 
        
        self.setToolTip(self.callsign)
        self.setWindowTitle(f"qtApp_{self.icao24}")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        label = QLabel(self)
        self.setCentralWidget(label)

        # pixmap = QPixmap("Assets/duck-left.gif")
        # label.setPixmap(pixmap)
        # self.resize(pixmap.width(), pixmap.height())

        if self.heading:
            if self.heading >= 0.0 and self.heading <= 180.0: 
                movie = QMovie("Assets/duck-right.gif")
            else:
                movie = QMovie("Assets/duck-left.gif")
        else:
            movie = QMovie("Assets/duck-left.gif")
                            
    
        label.setMovie(movie)
        movie.start()

        pixmap = QPixmap("Assets/duck-left.gif")
        self.resize(pixmap.width(), pixmap.height())

    def updateState(self, state: StateVector) -> None:
        """Redefine window properties when new a state becomes available"""
        self.icao24 = state.icao24
        self.callsign = state.callsign
        self.velocity = state.velocity
        self.heading = state.true_track
        if state.longitude is None or state.latitude is None:
            return
        self.longitude = state.longitude
        self.latitude = state.latitude
        
        stateTimestamp = state.time_position
        if stateTimestamp is not None:
            staleness = time.time() - stateTimestamp # difference real time and api data
            self.deadReckonPosition(dt=staleness)
            
        self.lastApiUpdate = time.monotonic()
        
        # self.moveToPlaneLoc(self.longitude, self.latitude)

    def coordsToPixels(self, lon, lat) -> tuple[int, int]: 
        # normalize to 0-1 and multiply with number of available pixels
        pixelx = int(((lon - self.minLong) / (self.maxLong - self.minLong) ) * self.Nxpixels)
        pixely = int(((lat - self.minLat)  / (self.maxLat - self.minLat)   ) * self.Nypixels) # print(f"{[pixelx,pixely]=}")
        
        # since on hyprland y axis inverted:
        pixely = self.Nypixels - pixely        
        return pixelx, pixely
        
    def showEvent(self, a0) -> None: #a0 == event but qtwidgets complains
        """Fires when window is first shown"""
        super().showEvent(a0)             
        QTimer.singleShot(150, lambda:self.moveToPlaneLoc(self.longitude, self.latitude)) # wait for window to spawn, then move. TODO: move first, then show.

    def centerImage(self):
        self.pixelx = int(self.pixelx - (self.width() / 2))       # update such that image is rendered at the center rather than top left
        self.pixely = int(self.pixely - (self.height()/ 2))

    def moveToPlaneLoc(self, longitude:float, latitude:float) -> None:
        self.pixelx, self.pixely = self.coordsToPixels(longitude, latitude)
        
        self.centerImage()
        self.customMove(self.pixelx, self.pixely)  
        # print(f"Moving {self.callsign} to {self.pixelx}, {self.pixely}")
    
    def customMove(self, x, y):
        self.mover.move(x, y, self)

    def deadReckonPosition(self, dt:float) -> None:
        
        if not self.heading or not self.velocity:
            return
    
        if time.monotonic() - self.lastApiUpdate < 0.75 * dt:
            return  # skip to prevent jittery updates
        
        distanceTraveled = self.velocity*dt
        headingRadians = math.radians(self.heading)
        
        # Use flat earth approximation for converting from meters to degrees of lat/lon
        dlat = (distanceTraveled * math.cos(headingRadians)) / 111_320
        dlon = (distanceTraveled * math.sin(headingRadians)) / (111_320 * math.cos(math.radians(self.latitude)))        # print(f"{dlat,dlon=}")

        self.latitude += dlat
        self.longitude += dlon
        
        self.moveToPlaneLoc(self.longitude, self.latitude)      # print(f"Deadreckon at {datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")}")





def main():
    print("Not supported to run as standalone .py file.")

if __name__ == "__main__":
    main()
