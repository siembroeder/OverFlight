from opensky_api import StateVector

# Core Python imports
import math
import time

# PyQt imports
from PyQt6.QtGui import QPixmap, QMovie, QTransform
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel

# Custom imports 
from Mover import Mover
from WindowTrackerConfig import WindowTrackerConfig, VisualsConfig
   

class MainWindow(QMainWindow): 
    def __init__(self, state:StateVector, config:WindowTrackerConfig):
        super().__init__()
        
        # Extract state data
        self.state = state
        self.icao24 = state.icao24
        self.callsign = state.callsign
        self.velocity = state.velocity  # m/s
        self.heading  = state.true_track
        self.lastApiUpdate = time.monotonic()
        if state.longitude is None or state.latitude is None:
            return
        self.longitude, self.latitude = (state.longitude, state.latitude)
        
        # Extract config data
        self.mover:"Mover" = config.mover
        self.minLat, self.maxLat, self.minLong, self.maxLong = config.bboxAtLocation
        
        # Select display
        screens = QApplication.screens()
        displayName = config.setup.displayName
        self.targetScreen = None
        
        if displayName == "all":
            self.targetScreen = QApplication.primaryScreen()
            if self.targetScreen is not None:
                self.virtual_geom = self.targetScreen.virtualGeometry()
                self.Nxpixels = self.virtual_geom.width()
                self.Nypixels = self.virtual_geom.height()
                self.screenOrigin = self.virtual_geom.topLeft()
        else:
            for screen in screens:
                if not displayName: # Use first screen
                    self.targetScreen = screen
                    break
                elif screen.name() == displayName:
                    self.targetScreen = screen
                    break
                
            if self.targetScreen is None:
                raise ValueError("No screen found. Set the displayName.")
                
            geom              = self.targetScreen.availableGeometry()
            self.Nxpixels     = geom.width()
            self.Nypixels     = geom.height()
            self.screenOrigin = geom.topLeft()
        
        # if displayName == 'all': 
        #     self.primaryScreen = QApplication.primaryScreen()
        #     if self.primaryScreen is not None:
        #         self.virtual_geom = self.primaryScreen.virtualGeometry()
        #         self.Nxpixels = self.virtual_geom.getCoords()[2] + 1
        #         self.Nypixels = self.virtual_geom.getCoords()[3] + 1            #print(f"{self.virtual_geom=}")
        # else:
        #     for screen in screens:
        #         if not displayName: # set dimensions to first screen
        #             self.availableGeometry = screen.availableGeometry()
        #             self.Nxpixels, self.Nypixels = self.availableGeometry.width(), self.availableGeometry.height()
        #             break 
        #         elif screen.name() == displayName:
        #             self.availableGeometry = screen.availableGeometry()
        #             self.Nxpixels, self.Nypixels = self.availableGeometry.width(), self.availableGeometry.height() 
        
        self.setToolTip(self.callsign)
        self.setWindowTitle(f"qtApp_{self.icao24}")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        label = QLabel(self)
        self.setCentralWidget(label)
        self.setVisuals(config.visuals, label)
                

    def setVisuals(self, visuals:VisualsConfig, label:QLabel):
        size = self.getImageSize(visuals.imageSize)

        if visuals.windowTheme == "aircraft":
            pixmap = QPixmap("Assets/singleIsleAircraft.png")
            if self.heading is not None:
                transform = QTransform().rotate(self.heading)
                pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
            pixmap = pixmap.scaled(size,Qt.AspectRatioMode.IgnoreAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)

            label.setFixedSize(size)
            self.setFixedSize(size)
            
        if visuals.windowTheme == "duck":
            if self.heading is not None:
                if self.heading >= 0.0 and self.heading <= 180.0: 
                    self.movie = QMovie("Assets/duck-right.gif")
                else:
                    self.movie = QMovie("Assets/duck-left.gif")
            else:
                self.movie = QMovie("Assets/duck-left.gif")
                        
            self.setFixedSize(size)
            label.setFixedSize(size)

            self.movie.setScaledSize(size)
            label.setMovie(self.movie)
            self.movie.start()        

    def getImageSize(self, imageSize:str|list) -> QSize:
        defaultSizes = {"miniature": QSize(25, 25),
                        "small":     QSize(50, 50),
                        "medium":    QSize(100, 100),
                        "large":     QSize(200, 200),
                        "comicallyLarge": QSize(500, 500)}
        
        if isinstance(imageSize, list):
            if len(imageSize) == 2:
                return QSize(imageSize[0], imageSize[1])
            raise IndexError("imageSize should have exactly 2 items")
        
        if imageSize not in defaultSizes.keys():
            imageSize = "small"
    
        return defaultSizes[imageSize] 
    
    def updateState(self, state:StateVector) -> None:
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

    def coordsToPixels(self, lon:float, lat:float) -> tuple[int, int]: 
        # normalize to 0-1 and multiply with number of available pixels
        pixelx = int(((lon - self.minLong) / (self.maxLong - self.minLong) ) * self.Nxpixels)
        pixely = int(((lat - self.minLat)  / (self.maxLat - self.minLat)   ) * self.Nypixels) # print(f"{[pixelx,pixely]=}")
        
        # invert y axis
        pixely = self.Nypixels - pixely    
        
        # offset to selected display
        pixelx += self.screenOrigin.x()
        pixely += self.screenOrigin.y()   
         
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
    
    def customMove(self, x:int, y:int):
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
