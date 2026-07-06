import csv
import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass

from PySide6.QtGui import QPixmap


@dataclass
class Icao8643Entry():
    model_full_name:str
    wtc:str
    wtg:str
    typecode:str
    manufacturer_code:str
    aircraft_description:str
    engine_count:int
    engine_type:str
    
    @classmethod
    def load_icao24_to_typecode(cls) -> dict[str, str]:
        """Load icao24 to typecode dict, 500k lines but two columns."""
        with open("data/icao24_typecode_aircraft.csv", encoding="utf-8") as f:
            reader = csv.reader(f)
            return dict(reader)

    @classmethod
    def load_typecodes_to_icao8643_entry(cls) -> dict[str, "Icao8643Entry"]:
        """Load typecode to Icao8643Entry dict from icao_8643.csv."""
        with open("data/icao_8643.csv", encoding="utf-8") as f:
            return {row["Designator"].strip().upper(): cls(model_full_name       = row["ModelFullName"],
                                                           wtc                 = row["WTC"],
                                                           wtg                 = row["WTG"],
                                                           typecode            = row["Designator"],
                                                           manufacturer_code    = row["ManufacturerCode"],
                                                           aircraft_description = row["AircraftDescription"],
                                                           engine_count         = int(row["EngineCount"]),
                                                           engine_type          = row["EngineType"])
                                                           for row in csv.DictReader(f)
                                                           }
    
    def get_visual_info(self) -> tuple[QPixmap, float]:
        description = self.aircraft_description.lower()
        typecode = self.typecode.upper()
        
        # Set defaults
        factor = 1.0
        image = QPixmap("assets/A321.png")

        # Filter wtc
        if self.wtc == "L":
            image = QPixmap("assets/C172.png")
            factor = 0.5
            
        if self.wtc == "M":
            pass # default settings
        
        if self.wtc == "H":
            image = QPixmap("assets/B777.png")
            factor = 1.1
            
        # Filter number of engines
        if self.engine_count == 3:
            image = QPixmap("assets/md11.png")

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
        if self.wtc == "L":
            image = QPixmap("assets/C172.png")
            factor = 0.5
            
        if self.wtc == "M":
            pass # default settings
        
        if self.wtc == "H":
            image = QPixmap("assets/B777.png")
            factor = 1.1
        
        # Filter number of engines
        if self.engine_count == 3:
            image = QPixmap("assets/md11.png")
        
        return (image, factor)
