import csv
import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass

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