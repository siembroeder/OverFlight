
from dataclasses import dataclass
from PySide6.QtGui import QPixmap

from opensky_api import StateVector
from utils.Icao8643Utils import Icao8643Entry

@dataclass
class AircraftRecord():
    """Small dataclass storing an aircrafts live openskyapi StateVector and metadata from icao8643 database entry"""
    state:StateVector
    entry:Icao8643Entry

    def getVisualInfo(self) -> tuple[QPixmap, float]:
        description = self.entry.aircraftDescription.lower()
        typecode = self.entry.typecode.upper()
        factor = 1
        image = QPixmap("assets/singleIsleAircraft.png")

        if typecode.startswith("B74"):
            image = QPixmap("assets/747.png")
            factor = 1.2
            
        if typecode == "A388":
            image = QPixmap("assets/A380.png")
            factor = 1.4
            
        if typecode == "C172":
            image = QPixmap("assets/C172.png")
            factor = 0.5
            
        if description == "helicopter":
            image = QPixmap("assets/helicopter.png")
            factor = 0.5
        
        return (image, factor)

        
        