
"""AI generated script to get ICAO 8643 database in a .csv file"""

import requests
import csv

def download_icao_8643(output_file="data/icao_8643.csv"):
    url = "https://doc8643.icao.int/External/AircraftTypes"
    headers = {
        "Origin": "https://www.icao.int",
        "Referer": "https://www.icao.int/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    print("Fetching ICAO Doc 8643 data...")
    resp = requests.post(url, headers=headers, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    print(f"Got {len(data)} records.")

    if not data:
        print("No data returned.")
        return

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    print(f"Saved to {output_file}")

if __name__ == "__main__":
    download_icao_8643()