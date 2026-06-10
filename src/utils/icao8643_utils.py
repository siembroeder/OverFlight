import csv
import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass

@dataclass
class Icao8643Entry():
    modelFullName:str
    wtc:str
    wtg:str
    typecode:str
    manufacturerCode:str
    aircraftDescription:str
    engineCount:int
    engineType:str
    
    @classmethod
    def loadIcao24ToTypecode(cls) -> dict[str, str]:
        """Load icao24 to typecode dict, 500k lines but two columns."""
        with open("data/icao24_typecode_aircraft.csv", encoding="utf-8") as f:
            reader = csv.reader(f)
            return dict(reader)

    @classmethod
    def loadTypecodesToIcao8643Entry(cls) -> dict[str, "Icao8643Entry"]:
        """Load typecode to Icao8643Entry dict from icao_8643.csv."""
        with open("data/icao_8643.csv", encoding="utf-8") as f:
            return {row["Designator"].strip().upper(): cls(modelFullName       = row["ModelFullName"],
                                                           wtc                 = row["WTC"],
                                                           wtg                 = row["WTG"],
                                                           typecode            = row["Designator"],
                                                           manufacturerCode    = row["ManufacturerCode"],
                                                           aircraftDescription = row["AircraftDescription"],
                                                           engineCount         = int(row["EngineCount"]),
                                                           engineType          = row["EngineType"])
                                                           for row in csv.DictReader(f)
                                                           }