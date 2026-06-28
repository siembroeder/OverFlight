import time
import logging
logger = logging.getLogger(__name__)

from opensky_api import StateVector
from PySide6.QtGui import QMovie, QTransform
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import QMainWindow, QLabel

# Custom imports 
from mover import Mover
from utils.aircraft_record import AircraftRecord
from utils.qt_utils import get_window_size, getScreenGeometry
from settings import Settings, VisualsSettings, TrackingSettings
from utils.type_hints import Meters, Degrees, Seconds, MetersPerSecond, Latitude, Longitude, asLatitude, asLongitude

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
    squawk: str | None = None
    callsign: str | None = None
    origin_country: str = ""
    latitude: Latitude | None = None
    longitude: Longitude | None = None
    last_contact: Seconds = Seconds(0)
    time_position: Seconds | None = None
    velocity: MetersPerSecond | None = None
    on_ground: bool = False
    true_track: Degrees | None = None
    vertical_rate: MetersPerSecond | None = None
    geo_altitude: Meters | None = None
    baro_altitude: Meters | None = None
    spi: bool = False
    sensors: list[int] | None = None
    category: int = 0
    position_source: int = 0
    
    
    def __init__(self, settings:Settings, aircraft:AircraftRecord):
        super().__init__()
        
        self.settings = settings
        self.aircraft = aircraft
        
        # Extract state data, manually write self.lat/lon. All other lat/lon logic is handled by mover
        state = aircraft.state
        self.apply_state(state)
        self.latitude = asLatitude(state.latitude)
        self.longitude= asLongitude(state.longitude)
        self.last_api_update = time.monotonic()        
        
        # Set basic Qt info
        self.setWindowTitle(f"OverFlightWindow_{state.icao24}")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        self.label = QLabel(self)
        self.setCentralWidget(self.label)
        
        # Set custom Qt info
        self.image, self.image_scale_factor = aircraft.getVisualInfo()
        self.set_window_size()
        self.set_window_theme()
        self.build_tooltip()
        self.set_screen_params()
        
        self.mover:"Mover" = Mover(self)
        self.mover.update_dead_reckon_increments()
        
        # Register callbacks for settings that require a MainWindow method to execute
        settings.on_change("window_theme", lambda _: self.set_window_theme())
        settings.on_change("tooltip_fields", lambda _: self.build_tooltip())
        settings.on_change("bbox_at_location", lambda _: self.mover.move_to_loc(self.latitude, self.longitude))
               
    def set_screen_params(self):
        """
        Set the width, height and topLeft coordinates in pixels of the displayName from settings.setup
        If settings.setup.displayName == None, return the first screen from QApplication.screens()
        """
        display_name = self.settings.setup.display_name
        geom = getScreenGeometry(display_name)
        
        self.n_pixels_x     = geom.width()
        self.n_pixels_y     = geom.height()
        self.screen_origin = geom.topLeft()
         
    def build_tooltip(self) -> None:
        """
        Set the string that's shown when a mouse hovers over the window.
        Taken from self.settings.visuals.tooltipFields. 
        Valid fields are all those found in settings.tracking and StateVector
        
        Default = f'callsign = {self.callsign}'
        """
        tracking_settings:TrackingSettings = self.settings.tracking
        lines = []
        for field in self.settings.visuals.tooltip_fields:
            value = None
            # Check self, entry, trackingSettings for field (order matters)
            if hasattr(self, field):
                value = getattr(self, field)
            elif hasattr(self.aircraft.entry, field):
                value = getattr(self.aircraft.entry, field)
            elif hasattr(tracking_settings, field):
                value = getattr(tracking_settings, field)
            
            if value is None:
                continue # if field isn't found, don't show it in the tooltip
            
            if isinstance(value, str): # Clean string
                value = value.strip()
                
            if ("altitude" in field) and (isinstance(value, (int, float))):
                value = round(value * 3.28084) # convert to Feet

            lines.append(f"{field}={value}")

        tooltip = "\n".join(lines)    
        self.setToolTip(tooltip)   

    def set_window_theme(self):
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
        
        if visuals.window_theme == "aircraft":                
            self.original_pixmap = self.image  # store original
            self.default_pixmap = self.original_pixmap.scaled(self.label.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.update_pixmap_heading()
            
        if visuals.window_theme == "duck":
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

    def set_window_size(self):
        """
        Sets the dimensions of the window and displayed image.
        Unique logic per theme.
        Valid sizes: 'miniature', 'small', 'medium', 'large', 'comicallyLarge'
        
        Default: 'small'
        """
        size:QSize = get_window_size(self.settings.visuals.window_size)
        if self.image_scale_factor != 1.0:
            size = QSize(round(self.image_scale_factor * size.width()), round(self.image_scale_factor * size.height()))

        self.label.setFixedSize(size)
        self.setFixedSize(size)
        
        # resize what is currently being displayed
        if (self.settings.visuals.window_theme == "aircraft") and hasattr(self, "defaultPixmap"):
            self.default_pixmap = self.original_pixmap.scaled(size,  # scale from original to preserve resolution
                                                            Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.update_pixmap_heading()

        elif (self.settings.visuals.window_theme == "duck") and (hasattr(self, "movie")):
            self.movie.setScaledSize(size)
            
    def update_pixmap_heading(self):
        """
        Rotates the image in the direction of self.heading
        Can be used for any theme that uses a still image and maybe in the future also for movies.
        """
        if hasattr(self, "defaultPixmap") and (self.true_track is not None):
            transform = QTransform().rotate(self.true_track)
            rotated   = self.default_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
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
        QTimer.singleShot(10, lambda:self.mover.move_to_loc(self.latitude, self.longitude)) # wait for window to spawn, then move. TODO: move first, then show.
    
    def apply_state(self, state: StateVector) -> None:
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

    def heading_flipped(self, previous_heading:Degrees|None) -> bool:
        if previous_heading is None:
            return False
            
        current_heading  = self.true_track
        
        if previous_heading is None or current_heading is None:
            return False
        
        return (previous_heading // 180) != (current_heading // 180)        

    def update_state(self, state:StateVector) -> None:
        """Redefine window properties when new a state becomes available"""
        previous_heading = self.true_track
        
        # update window with new state
        self.apply_state(state)                        
        self.last_api_update = time.monotonic()
        
        self.mover.update_dead_reckon_increments()
        self.build_tooltip() # Some values like heading or altitude (might) change every api call
        
        if self.settings.visuals.window_theme == "aircraft": # ducks use movie, don't rotate to heading
            self.update_pixmap_heading()
                 
        if (self.settings.visuals.window_theme == "duck") and self.heading_flipped(previous_heading): # for aircraft changing directions, update duck direction accordingly
            self.set_window_theme()