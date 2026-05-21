

import csv
from dataclasses import dataclass

@dataclass
class Icao8643Entry():
    modelFullName:str|None = None
    description:str|None = None
    wtc:str|None = None
    wtg:str|None = None
    manufacturerCode:str|None = None
    showInPart3Only:bool|None = None
    aircraftDescription:str|None = None
    engineCount:int|None = None
    engineType:str|None = None
    
def findIcao8643Entry(typecode:str) -> Icao8643Entry:
    typecode = typecode.strip().upper()
    with open("data/icao_8643.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            designator = row["Designator"].strip().upper()
            
            if typecode and (designator == typecode):
                return Icao8643Entry(
                    modelFullName=row["ModelFullName"],
                    description = row["Description"],
                    wtc = row["WTC"],
                    wtg = row["WTG"],
                    manufacturerCode= row["ManufacturerCode"],
                    showInPart3Only = bool(row["ShowInPart3Only"]),
                    aircraftDescription= row["AircraftDescription"],
                    engineCount= int(row["EngineCount"]),
                    engineType= row["EngineType"]
                )
                
    return Icao8643Entry()