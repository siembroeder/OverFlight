# aircraft_widget.py
import logging

logger = logging.getLogger(__name__)

from PySide6.QtGui import QMovie, QTransform
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QLabel

from paths import resource_path
from dead_reckoner import DeadReckoner
from aircraft_record import AircraftRecord
from utils.qt_utils import get_window_size, coords_to_pixels
from settings import app_settings, VisualsSettings, TrackingSettings


class AircraftWidget(QWidget):

    def __init__(self, parent: QWidget, aircraft_record: AircraftRecord):
        super().__init__(parent)
        self._parent = parent

        self.aircraft_record = aircraft_record
        self.reckoner = DeadReckoner(aircraft_record)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label = QLabel(self)

        self.image, self.image_scale_factor = aircraft_record.entry.get_visual_info()
        self._set_window_size()
        self._set_window_theme()
        self._build_tooltip()

        # TODO: memory leak here since callbacks are never removed from Settings.callbacks.
        app_settings.on_change("window_theme", lambda _: self._set_window_theme())
        app_settings.on_change("tooltip_fields", lambda _: self._build_tooltip())
        app_settings.on_change("window_size", lambda _: self._set_window_size())

        self._reposition()
        self.show()

    @property
    def state(self):
        return self.aircraft_record.state

    @property
    def entry(self):
        return self.aircraft_record.entry

    def _reposition(self) -> None:
        """Move this widget to match the reckoner's current lat/lon, centered."""
        if self.reckoner.latitude is None or self.reckoner.longitude is None:
            return

        pixel_x, pixel_y = coords_to_pixels(self.reckoner.latitude, self.reckoner.longitude, self._parent)
        pixel_x -= self.width() // 2
        pixel_y -= self.height() // 2
        self.move(pixel_x, pixel_y)

    def dead_reckon_increment(self) -> None:
        """Called on a timer between API updates."""
        if self.reckoner.step():
            self._reposition()

    def _build_tooltip(self) -> None:
        tracking_settings: TrackingSettings = app_settings.tracking
        lines = []
        for field in app_settings.visuals.tooltip_fields:
            value = None
            if hasattr(self.state, field):
                value = getattr(self.state, field)
            elif hasattr(self.entry, field):
                value = getattr(self.entry, field)
            elif hasattr(tracking_settings, field):
                value = getattr(tracking_settings, field)

            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
            if ("altitude" in field) and isinstance(value, (int, float)):
                value = round(value * 3.28084)  # to feet

            lines.append(f"{field}={value}")

        tooltip = "\n".join(lines)    
        self.setToolTip(tooltip) 

    def _set_window_theme(self):
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
        visuals: VisualsSettings = app_settings.visuals

        if visuals.window_theme == "aircraft":
            self.original_pixmap = self.image
            self.defaultPixmap = self.original_pixmap.scaled(
                self.label.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self._update_pixmap_heading()

        if visuals.window_theme == "duck":
            true_track = self.state.true_track
            if true_track is not None and 0.0 <= true_track <= 180.0:
                self.movie = QMovie(str(resource_path("assets", "duck-right.gif")))
            else:
                self.movie = QMovie(str(resource_path("assets", "duck-left.gif")))

            self.movie.setScaledSize(self.label.size())
            self.label.setMovie(self.movie)
            self.movie.start()

    def _set_window_size(self):
        """
        Sets the dimensions of the window and displayed image.
        Unique logic per theme.
        Valid sizes: 'miniature', 'small', 'medium', 'large', 'comicallyLarge'
        
        Default: 'small'
        """
        size: QSize = get_window_size(app_settings.visuals.window_size, app_settings.setup.display_name)

        # Some aircraft typecodes are scaled, eg larger for A380
        if self.image_scale_factor != 1.0:
            size = QSize(round(self.image_scale_factor * size.width()), round(self.image_scale_factor * size.height()))

        self.label.setFixedSize(size)
        self.setFixedSize(size)

        if app_settings.visuals.window_theme == "aircraft" and hasattr(self, "defaultPixmap"):
            self.defaultPixmap = self.original_pixmap.scaled(
                size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self._update_pixmap_heading()
        elif app_settings.visuals.window_theme == "duck" and hasattr(self, "movie"):
            self.movie.setScaledSize(size)

    def _update_pixmap_heading(self):
        if hasattr(self, "defaultPixmap") and self.state.true_track is not None:
            transform = QTransform().rotate(self.state.true_track)
            rotated = self.defaultPixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)

            size = self.label.size()
            x = (rotated.width() - size.width()) // 2
            y = (rotated.height() - size.height()) // 2
            self.pixmap = rotated.copy(x, y, size.width(), size.height())
            self.label.setPixmap(self.pixmap)

    def update_state(self, aircraft_record: AircraftRecord) -> None:
        """Called when fresh API data arrives for this aircraft."""
        previous_heading = self.state.true_track

        self.aircraft_record = aircraft_record
        self.reckoner.on_fresh_state(aircraft_record)
        self._build_tooltip()

        if app_settings.visuals.window_theme == "aircraft":
            self._update_pixmap_heading()

        if app_settings.visuals.window_theme == "duck" and self._heading_flipped(previous_heading):
            self._set_window_theme()

        self._reposition()

    def _heading_flipped(self, previous_heading) -> bool:
        """
        Whether the heading flipped from east to west or visa versa.
        
        :return: If heading flipped.
        :rtype: bool
        """
        current = self.state.true_track
        if previous_heading is None or current is None:
            return False
        return (previous_heading // 180) != (current // 180)
    