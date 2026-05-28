import time
import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass

from opensky_api import StateVector
from PySide6.QtGui import QMovie, QTransform
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import QMainWindow, QLabel

# Custom imports 
from Mover import Mover
from utils.Icao8643Utils import Icao8643Entry
from Settings import Settings, VisualsSettings, TrackingSettings
from utils.QtUtils import getWindowSize, getScreenGeometry, getTypecodeScaleFactor, getAircraftImage
from utils.TypeHints import Meters, Degrees, Seconds, MetersPerSecond, Latitude, Longitude, asLatitude, asLongitude

@dataclass
class WindowConfig():
    state:StateVector
    entry:Icao8643Entry


class MainWindow(QMainWindow): 
    """
    Qt Window representing an aircraft, named OverFlightWindow_{self.icao}.
    All visual logic lives here
    
    Properties:
    - All the fields in opensky_api.StateVector
    - settings:Settings, shared across windows
    - mover:Mover(), unique to each window. Is responsible for moving the window around, all coordinate logic lives there
    - self.lastApiUpdate:float. Timestamp of the last moment where new api data came in
    
    When new api data is fetched, MainWindow.updateState(state) is executed
    """
    icao24: str = ""
    callsign: str | None = None
    origin_country: str = ""
    time_position: Seconds | None = None
    last_contact: Seconds = Seconds(0)
    longitude: Longitude | None = None
    latitude: Latitude | None = None
    geo_altitude: Meters | None = None
    on_ground: bool = False
    velocity: MetersPerSecond | None = None
    true_track: Degrees | None = None
    vertical_rate: MetersPerSecond | None = None
    sensors: list[int] | None = None
    baro_altitude: Meters | None = None
    squawk: str | None = None
    spi: bool = False
    position_source: int = 0
    category: int = 0
    
    def __init__(self, settings:Settings, windowConfig:WindowConfig):
        super().__init__()
        
        self.settings = settings
        self.windowConfig = windowConfig
        
        # Extract state data, manually write self.lat/lon. All other lat/lon logic is handled by mover
        state = windowConfig.state
        self.applyState(state)
        self.latitude = asLatitude(state.latitude)
        self.longitude= asLongitude(state.longitude)
        self.lastApiUpdate = time.monotonic()        
        
        # Set basic Qt info
        self.setWindowTitle(f"OverFlightWindow_{state.icao24}")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        self.label = QLabel(self)
        self.setCentralWidget(self.label)
        
        # Set custom Qt info
        self.setWindowSize()
        self.setWindowTheme()
        self.buildTooltip()
        self.setScreenParams()
        
        self.mover:"Mover" = Mover(self)
        self.mover.updateDeadReckonIncrements()
        
        # Register callbacks for settings that require a MainWindow method to execute
        settings.onChange("windowTheme", lambda _: self.setWindowTheme())
        settings.onChange("tooltipFields", lambda _: self.buildTooltip())
        settings.onChange("bboxAtLocation", lambda _: self.mover.moveToLoc(self.latitude, self.longitude))
               
    def setScreenParams(self):
        """
        Set the widht, height and topLeft coordinates in pixels of the displayName from settings.setup
        If settings.setup.displayName == None, return the first screen from QApplication.screens()
        """
        displayName = self.settings.setup.displayName
        geom = getScreenGeometry(displayName)
        
        self.Nxpixels     = geom.width()
        self.Nypixels     = geom.height()
        self.screenOrigin = geom.topLeft()
         
    def buildTooltip(self) -> None:
        """
        Set the string that's shown when a mouse hovers over the window.
        Taken from self.settings.visuals.tooltipFields. 
        Valid fields are all those found in settings.tracking and StateVector
        
        Default = f'callsign = {self.callsign}'
        """
        trackingSettings:TrackingSettings = self.settings.tracking
        lines = []
        for field in self.settings.visuals.tooltipFields:
           # Check self and trackingSettings for field
            if hasattr(self, field):
                value = getattr(self, field)
            elif hasattr(trackingSettings, field):
                value = getattr(trackingSettings, field)
            else:
                continue

            if isinstance(value, str): # Clean string
                value = value.strip()
                
            if ("altitude" in field) and (isinstance(value, (int, float))):
                value = round(value * 3.28084) # convert to Feet

            lines.append(f"{field}={value}")

        tooltip = "\n".join(lines)    
        self.setToolTip(tooltip)   

    def setWindowTheme(self):
        """
        Sets the image that shown on the window. can be a still image like .jpg or .png (etc) or movie like .gif
        Currently supports two themes: 'aircraft' and 'duck'.
        
        'aircraft'
            .png image of a plane that's rotated to the current heading
            
        'duck'
            .gif of a walking duck.
            Can walk to the left or right depending on if the heading broadly points left or right.
            Not rotated yet because every frame of the .gif should be rotated as you go (more difficult than eg .png) 
        """
        visuals:VisualsSettings = self.settings.visuals
        
        # Stop movie if running when switching from theme duck to aircraft.
        # if hasattr(self, "movie") and (self.movie.state() == QMovie.MovieState.Running):
        #     self.movie.stop()

        if visuals.windowTheme == "aircraft":
            image = getAircraftImage(self.windowConfig.entry.typecode, self.windowConfig.entry)
                
            self.originalPixmap = image  # store original
            self.defaultPixmap = self.originalPixmap.scaled(self.label.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.updatePixmapHeading()
            
        if visuals.windowTheme == "duck":
            if self.true_track is not None:
                if (self.true_track >= 0.0) and (self.true_track <= 180.0): 
                    self.movie = QMovie("assets/duck-right.gif")
                else:
                    self.movie = QMovie("assets/duck-left.gif")
            else:
                self.movie = QMovie("assets/duck-left.gif")
                    
            self.movie.setScaledSize(self.label.size())
            self.label.setMovie(self.movie)
            self.movie.start()        

    def setWindowSize(self):
        """
        Sets the dimensions of the window and displayed image.
        Unique logic per theme.
        Valid sizes: 'miniature', 'small', 'medium', 'large', 'comicallyLarge'
        
        Default: 'small'
        """
        size:QSize = getWindowSize(self.settings.visuals.windowSize)
        scaleFactor = getTypecodeScaleFactor(self.windowConfig.entry.typecode)
        if scaleFactor != 1.0:
            size = QSize(round(scaleFactor * size.width()), round(scaleFactor * size.height()))

        self.label.setFixedSize(size)
        self.setFixedSize(size)
        
        # resize what is currently being displayed
        if (self.settings.visuals.windowTheme == "aircraft") and hasattr(self, "defaultPixmap"):
            self.defaultPixmap = self.originalPixmap.scaled(size,  # scale from original to preserve resolution
                                                            Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.updatePixmapHeading()

        elif (self.settings.visuals.windowTheme == "duck") and (hasattr(self, "movie")):
            self.movie.setScaledSize(size)
            
    def updatePixmapHeading(self):
        """
        Rotates the image in the direction of self.heading
        Can be used for any theme that uses a still image and maybe in the future also for movies.
        """
        if hasattr(self, "defaultPixmap") and (self.true_track is not None):
            transform = QTransform().rotate(self.true_track)
            rotated   = self.defaultPixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
            size = self.label.size()
            x = (rotated.width()  - size.width())  // 2
            y = (rotated.height() - size.height()) // 2
            self.pixmap = rotated.copy(x, y, size.width(), size.height())
            
            self.label.setPixmap(self.pixmap)
             
    def showEvent(self, a0) -> None: #a0 == event but qtwidgets complains
        """
        Fires when window is first shown
        Wait for 100ms for window to open / be recognized by compositer, then move to its respective location
        """
        super().showEvent(a0)    
        QTimer.singleShot(10, lambda:self.mover.moveToLoc(self.latitude, self.longitude)) # wait for window to spawn, then move. TODO: move first, then show.
    
    def applyState(self, state: StateVector) -> None:
        """Explicitly map StateVector (except lat/lon) to MainWindow with type conversions."""

        self.icao24             = state.icao24
        self.callsign           = state.callsign
        self.origin_country     = state.origin_country
        self.time_position      = Seconds(state.time_position) if state.time_position is not None else None
        self.last_contact       = Seconds(state.last_contact)
        self.geo_altitude       = Meters(state.geo_altitude) if state.geo_altitude is not None else None
        self.on_ground          = state.on_ground
        self.velocity           = MetersPerSecond(state.velocity) if state.velocity is not None else None
        self.true_track         = Degrees(state.true_track) if state.true_track is not None else None
        self.vertical_rate      = MetersPerSecond(state.vertical_rate) if state.vertical_rate is not None else None
        self.sensors            = state.sensors 
        self.baro_altitude      = Meters(state.baro_altitude) if state.baro_altitude is not None else None
        self.squawk             = state.squawk
        self.spi                = state.spi
        self.position_source    = state.position_source
        self.category           = state.category

    def updateState(self, state:StateVector) -> None:
        """Redefine window properties when new a state becomes available"""
       
        self.applyState(state)                        
        self.lastApiUpdate = time.monotonic()
        self.mover.updateDeadReckonIncrements()
        self.buildTooltip()
        
        if self.settings.visuals.windowTheme == "aircraft": # ducks use movie, don't rotate to heading
            self.updatePixmapHeading()
                 

    