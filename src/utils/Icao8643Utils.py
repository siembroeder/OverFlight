

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
    def findEntry(cls, typecode:str, fallbackTypecode:str = "C172") -> "Icao8643Entry":
        
        typecodeRow = None
        fallbackRow = None
        with open("data/icao24_lookup.csv", encoding="utf-8") as f:
        # with open("data/icao_8643.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                designator = row["typecode"].strip().upper()
                
                if designator == typecode:
                    typecodeRow = row
                    
                if designator == fallbackTypecode:
                    fallbackRow = row
                   
        returningRow = typecodeRow or fallbackRow
        assert returningRow is not None, f"Fallback typecode: {fallbackTypecode} is not found in our icao8643 data, set a different one in settings.yaml"
        
        return cls(modelFullName       = returningRow["model"],
                   wtc                 = returningRow["wtc"],
                   wtg                 = returningRow["wtg"],
                   typecode            = returningRow["typecode"],
                   manufacturerCode    = returningRow["manufacturer"],
                   aircraftDescription = returningRow["aircraft_description"],
                   engineCount         = int(returningRow["engine_count"]),
                   engineType          = returningRow["engine_type"]
                )

    @classmethod
    def findByIcao24(cls, icao24:str, fallbackTypecode:str = "C172") -> "Icao8643Entry":
        icao24 = icao24.strip().lower()
        with open("data/icao24_lookup.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["icao24"] == icao24:
                    return cls(
                        modelFullName       = row["model"],
                        wtc                 = row["wtc"],
                        wtg                 = row["wtg"],
                        typecode            = row["typecode"],
                        manufacturerCode    = row["manufacturer"],
                        aircraftDescription = row["aircraft_description"],
                        engineCount         = int(row["engine_count"]),
                        engineType          = row["engine_type"],
                    )

        # if icao24 not found (aircraft newer than 2025-08) use fallback typecode
        logger.debug(f"Icao24: {icao24} not found in lookup")
        return cls.findEntry(fallbackTypecode, fallbackTypecode)
    
    @classmethod
    def loadIcao24Typecodes(cls) -> dict[str, str]:
        """Load icao24 to typecode dict, 500k lines but two columns."""
        with open("data/icao24_typecode_aircraft.csv", encoding="utf-8") as f:
            return {row["icao24"]: row["typecode"] for row in csv.DictReader(f)}

    @classmethod
    def loadTypecodes(cls) -> dict[str, "Icao8643Entry"]:
        """Load typecode to Icao8643Entry dict from icao_8643.csv."""
        with open("data/icao_8643.csv", encoding="utf-8") as f:
            return {row["Designator"].strip().upper(): cls(
                        modelFullName       = row["ModelFullName"],
                        wtc                 = row["WTC"],
                        wtg                 = row["WTG"],
                        typecode            = row["Designator"],
                        manufacturerCode    = row["ManufacturerCode"],
                        aircraftDescription = row["AircraftDescription"],
                        engineCount         = int(row["EngineCount"]),
                        engineType          = row["EngineType"])
                    for row in csv.DictReader(f)
                    }