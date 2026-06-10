
from dataclasses import dataclass
from PySide6.QtGui import QPixmap

from opensky_api import StateVector
from utils.icao8643_utils import Icao8643Entry

@dataclass
class AircraftRecord():
    """Small dataclass storing an aircrafts live openskyapi StateVector and metadata from icao8643 database entry"""
    state:StateVector
    entry:Icao8643Entry

    def getVisualInfo(self) -> tuple[QPixmap, float]:
        entry = self.entry
        description = entry.aircraftDescription.lower()
        typecode = self.entry.typecode.upper()
        
        # Set defaults
        factor = 1.0
        image = QPixmap("assets/A321.png")

        # Filter specific typecodes
        if typecode.startswith("B74"):
            image = QPixmap("assets/B747.png")
            factor = 1.2
            
        if typecode.startswith("B73"):
            image = QPixmap("assets/B737.png")
            
        if typecode in ["a318", "a319", "a320", "a321"]:
            image = QPixmap("assets/A321.png")
            
        if typecode == "A388":
            image = QPixmap("assets/A380.png")
            factor = 1.4
            
        if typecode == "C172":
            image = QPixmap("assets/C172.png")
            factor = 0.5
            
        # Filter descriptions
        if description == "helicopter":
            image = QPixmap("assets/helicopter.png")
            factor = 0.7
            
        if description == "glider":
            image = QPixmap("assets/glider.png")
            factor = 0.6
        
        # Filter wtc
        if entry.wtc == "L":
            image = QPixmap("assets/C172.png")
            factor = 0.5
            
        if entry.wtc == "M":
            pass # default settings
        
        if entry.wtc == "H":
            image = QPixmap("assets/B777.png")
            factor = 1.1
        
        # Filter number of engines
        if entry.engineCount == 3:
            image = QPixmap("assets/md11.png")
        
        return (image, factor)

        
        