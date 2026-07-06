from dataclasses import dataclass

from opensky_api import StateVector

from utils.icao8643_utils import Icao8643Entry


@dataclass
class AircraftRecord():
    """Small dataclass storing an aircrafts live openskyapi StateVector and metadata from icao8643 database entry"""
    state:StateVector
    entry:Icao8643Entry     
        