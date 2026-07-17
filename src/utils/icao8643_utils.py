import csv
import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass

from PySide6.QtGui import QPixmap

from paths import resource_path

AIRCRAFT_DIR = resource_path("assets", "aircraft")

DEFAULT_VISUALS = ("A321.png", 1.0)

WTC_VISUALS = {
    "L": ("C172.png", 0.5),
    "M": DEFAULT_VISUALS,
    "H": ("B777.png", 1.2)
}

ENGINE_COUNT_VISUALS = {
    "3": ("md11.png", 1.0)
}

TYPECODE_VISUALS = {
    "A388": ("A380.png", 1.4),
    "C172": ("C172.png", 0.5),
    "A318": ("A321.png", 1.0),
    "A319": ("A321.png", 1.0),
    "A320": ("A321.png", 1.0),
    "A321": ("A321.png", 1.0),
}

TYPECODE_PREFIX_VISUALS = {
    "B74": ("B747.png", 1.2),
    "B73": ("B737.png", 1.0)
}

DESCRIPTION_VISUALS = {
    "glider": ("glider.png", 0.6),
    "helicopter": ("helicopter.png", 0.7)
}


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
        path = resource_path("data", "icao24_typecode_aircraft.csv")
        with open(path, encoding="utf-8") as f:
        # with open("data/icao24_typecode_aircraft.csv", encoding="utf-8") as f:
            reader = csv.reader(f)
            return dict(reader)

    @classmethod
    def load_typecodes_to_icao8643_entry(cls) -> dict[str, "Icao8643Entry"]:
        """Load typecode to Icao8643Entry dict from icao_8643.csv."""
        path = resource_path("data", "icao_8643.csv")
        with open(path, encoding="utf-8") as f:
        # with open("data/icao_8643.csv", encoding="utf-8") as f:
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
        """
        Order matters: later checks overwrite earlier checks
        """
        description = self.aircraft_description.lower()
        typecode = self.typecode.upper()
        
        file, factor = DEFAULT_VISUALS

        if self.wtc in WTC_VISUALS:
            file, factor = WTC_VISUALS[self.wtc]

        if self.engine_count in ENGINE_COUNT_VISUALS:
            file, factor = ENGINE_COUNT_VISUALS[self.engine_count]

        if description in DESCRIPTION_VISUALS:
            file, factor = DESCRIPTION_VISUALS[description]

        for prefix, visual in TYPECODE_PREFIX_VISUALS.items():
            if typecode.startswith(prefix):
                file, factor = visual

        if typecode in TYPECODE_VISUALS:
            file, factor = TYPECODE_VISUALS[typecode]

        image = QPixmap(AIRCRAFT_DIR / file)
        return image, factor


        # # Set defaults
        # factor = 1.0
        # image = QPixmap("assets/aircraft/A321.png")

        # # Filter wtc
        # if self.wtc == "L":
        #     image = QPixmap("assets/aircraft/C172.png")
        #     factor = 0.5
            
        # if self.wtc == "M":
        #     pass # default settings
        
        # if self.wtc == "H":
        #     image = QPixmap("assets/aircraft/B777.png")
        #     factor = 1.1
            
        # # Filter number of engines
        # if self.engine_count == 3:
        #     image = QPixmap("assets/aircraft/md11.png")

        # # Filter specific typecodes
        # if typecode.startswith("B74"):
        #     image = QPixmap("assets/aircraft/B747.png")
        #     factor = 1.2
            
        # if typecode.startswith("B73"):
        #     image = QPixmap("assets/aircraft/B737.png")
            
        # if typecode in ["a318", "a319", "a320", "a321"]:
        #     image = QPixmap("assets/aircraft/A321.png")
            
        # if typecode == "A388":
        #     image = QPixmap("assets/aircraft/A380.png")
        #     factor = 1.4
            
        # if typecode == "C172":
        #     image = QPixmap("assets/aircraft/C172.png")
        #     factor = 0.5
            
        # # Filter descriptions
        # if description == "helicopter":
        #     image = QPixmap("assets/aircraft/helicopter.png")
        #     factor = 0.7
            
        # if description == "glider":
        #     image = QPixmap("assets/aircraft/glider.png")
        #     factor = 0.6
                
        # return (image, factor)
