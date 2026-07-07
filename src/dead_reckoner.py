import math
import time

from settings import app_settings
from utils.aircraft_record import AircraftRecord
from utils.type_hints import *


class DeadReckoner:

    def __init__(self, aircraft_record: AircraftRecord):
        state = aircraft_record.state
        self.latitude: Latitude | None = asLatitude(state.latitude) if state.latitude is not None else None
        self.longitude: Longitude | None = asLongitude(state.longitude) if state.longitude is not None else None
        self.velocity = state.velocity
        self.true_track = state.true_track

        self.last_api_update = time.monotonic()
        self.d_step_lat: Latitude = Latitude(0.0)
        self.d_step_lon: Longitude = Longitude(0.0)
        self.recompute_step()

    def on_fresh_state(self, aircraft_record: AircraftRecord) -> None:
        """Call new state is received."""
        state = aircraft_record.state
        if state.latitude is not None:
            self.latitude = asLatitude(state.latitude)
        if state.longitude is not None:
            self.longitude = asLongitude(state.longitude)
        self.velocity = state.velocity
        self.true_track = state.true_track

        self.last_api_update = time.monotonic()
        self.recompute_step()

    def predicted_position_at_next_api_call(self) -> tuple[Latitude, Longitude]:
        """
        Calculates the next position of the aircraft if it continues its path.

        :return: The predicted position at the next api call.
        :rtype: tuple[Latitude, Longitude]
        """
        if self.velocity is None or self.true_track is None or self.latitude is None or self.longitude is None:
            return (self.latitude or Latitude(0.0), self.longitude or Longitude(0.0))

        distance: Meters = Meters(self.velocity * app_settings.api.api_call_delay)
        heading_rad: Radians = Radians(math.radians(self.true_track))

        d_lat = Latitude((distance * math.cos(heading_rad)) / 111_320)
        d_lon = Longitude((distance * math.sin(heading_rad)) / (111_320 * math.cos(math.radians(self.latitude))))

        return (Latitude(self.latitude + d_lat), Longitude(self.longitude + d_lon))

    def recompute_step(self) -> None:
        """Recalculate the per-tick lat/lon delta used by `step()`."""
        if self.latitude is None or self.longitude is None:
            return

        next_lat, next_lon = self.predicted_position_at_next_api_call()
        self.d_step_lat = Latitude((next_lat - self.latitude) / self.steps)
        self.d_step_lon = Longitude((next_lon - self.longitude) / self.steps)

    def step(self) -> bool:
        """
        Advance position by one dead-reckoning tick. 
        Returns True if position (probably) changed, False if skipped.

        :return: Whether the position changed.
        :rtype: bool
        """
        if self.true_track is None or self.velocity is None or self.latitude is None or self.longitude is None:
            return False

        if time.monotonic() - self.last_api_update < 0.75 * app_settings.visuals.update_interval:
            return False  # skip to prevent jittery updates

        self.latitude = asLatitude(self.latitude + self.d_step_lat)
        self.longitude = asLongitude(self.longitude + self.d_step_lon)
        return True

    @property
    def steps(self) -> float:
        """
        Number of dead-reckoning ticks between api calls, derived live from current settings.
        
        :return: Number of dead-reckoning ticks between api calls.
        :rtype: float
        """
        return app_settings.api.api_call_delay / app_settings.visuals.update_interval