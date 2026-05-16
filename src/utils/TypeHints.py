
from typing import NewType


# Custom types
Meters = NewType("Meters", float)
Degrees = NewType("Degrees", float)
Radians = NewType("Radians", float)
Seconds = NewType("Seconds", float)
MetersPerSecond = NewType("MetersPerSecond", float)

Latitude = NewType("Latitude", float)
Longitude = NewType("Longitude", float)



# Helper functions
def asLatitude(value: float | None) -> Latitude | None:
    return Latitude(value) if value is not None else None

def asLongitude(value: float | None) -> Longitude | None:
    return Longitude(value) if value is not None else None

