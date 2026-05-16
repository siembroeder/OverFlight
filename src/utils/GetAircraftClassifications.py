"""
Write Aircraft Classification data from flugzeuginfo.net to .csv and .json file.
"""



import pandas as pd
import json
import os


if not os.path.isdir("AircraftData/"):
    os.mkdir("AircraftData/")



# Load data
url = "https://www.flugzeuginfo.net/table_accodes_en.php?"
tables = pd.read_html(url, encoding='ISO-8859-1')

aircraft_df = pd.DataFrame()
for table in tables:
    
    aircraft_df = pd.concat([aircraft_df, table])
    
    
# Write to .csv
aircraft_df.to_csv("AircraftData/AircraftClassifications.csv", header=True, index=False)


# Write to .json
aircraft_dict = {}
for index, row in aircraft_df.iterrows():
    icao_code = row["ICAO"]
    manufacturer = row["Manufacturer"]
    wake = row["Wake"]
    
    entry = {"Manufacturer": manufacturer,
             "wake": wake}
    
    aircraft_dict[icao_code] = entry

with open("AircraftData/AircraftClassifications.json", "w", encoding="utf-8") as f:
    json.dump(aircraft_dict, f, indent=4)
