# OverFlight

Overflight is a desktop agent that displays nearby aircrafts through icons that mirror their flight paths on the screen. 



## Prototype / Development

Current functionality:
- Configure in Settings/settings.json using below documentation.
- spawns windows representing live aircraft at their current location relative to the chosen boundingbox and screen.
- in between api calls, use deadreckoning to update window position for more a interactive experience
- When a new api call comes in, deadreckon to predicted next api location.
- close the window when the aircraft moves out of the bounding box or no longer passes filters
- create a new window if a new aircraft moves into the boundingbox and the max number of windows isn't reached.
- Settings can be changed at runtime
- runs indefinitely.


### Supported Sessions:

- Hyprland, add these to your hyprland.conf file:
  - windowrule = float on, match:title ^OverFlightWindow_.*
  - windowrule = no_blur on, match:title ^OverFlightWindow_.*
  - windowrule = border_size 0, match:title ^OverFlightWindow_.*
  - windowrule = no_shadow on, match:title ^OverFlightWindow_.*
  - windowrule = no_initial_focus on, match:title ^OverFlightWindow_.*
  - windowrule = pin on, match:title ^OverFlightWindow_.*
    - Hyprland 0.55 (lua) support is coming.

- Windows
- X11 like xfce
- Sway


### Settings / Configuration
Use the settings.json file in Settings/ to set your preferences for the categories core, api, setup, tracking, and visuals. 

#### core

|name                  |type  |default           |description|
|----------------------|------|------------------|-----------|
|openskyCredentialsPath|string|"credentials.json"|Path to your opensky credentials .json file.|
|location              |string|"Schiphol"        |Any location in the world that geopy recognizes.|
|bboxSize              |string|"small"           |Preconfigured bounding box sizes, set to "small", "medium", or "large". May be omitted if both latitudeOffset and LongitudeOffset are used.|
|longitudeOffset, latitudeOffset|float,float|None,None|Can be used to set the width and height of the bounding box. Must both be a non-zero, positive float. Do not use if bboxSize is used.|

##### Configuring for Boundingbox / Area 
- Option 1: Set bboxSize from ["small", "medium", "large"]
- Option 2: Set BOTH longitudeOffset AND latitudeOffset to some non-zero float. The resulting bounding box has dimensions (2\*longitudeOffset x 2\*latitudeOffset)
- Invalid: Using bboxSize, latitudeOffset, and longitudeOffset.
- Invalid: Using only one of latitudeOffset, longitudeOffset.

#### api

| name         | type | default | description |
|--------------|------|---------|-------------|
|apiCallDelay  |float |10.0     | Spacing between consecutive calls to opensky_api.get_states(). Any value smaller than 10.0 results in rate limiting for free OpenSky users.|

#### setup

| name       | type    | default | description |
|------------|---------|---------|-------------|
| maxWindows |int      |25       | Maximum number of aircraft windows on the screen.|
| displayName |string   |First entry in QApplication.screens() | Select the name of display on which to project the windows, eg "eDP-1", "HDMI-1-A", or "DP-1". If "all" use all displays. Depending on scaling of the displays, part of the bounding box may be "outside" the displays.|

#### tracking
Aircraft are filtered based on these conditions.

| name                  | type       | default | description |
|-----------------------|------------|---------|-------------|
| minVelocity           |float       |None     |Display only aircraft with a velocity higher than minVelocity in m/s.|
| callsign              |string      |None     |Eg "KLM641", case insensitive.|
| airline               |string      |None     |Filter the three letters in the callsign, eg "KLM" or "DLH".|
| icao24                |string      |None     |Eg "485F82", case insensitive.|
| squawk                |string      |None     |Eg "1000" or "7700".|
| inAir                 |int         |None     |Set to 1 to only show aircraft in the air.|
| onGround              |int         |None     |Set to 1 to only show aircraft on the ground.|
| minGeoAltitude        |float       |None     |Eg 30000, units in feet.|
| maxGeoAltitude        |float       |None     |Eg 30000, units in feet.|
| minBaroAltitude       |float       |None     |Eg 30000, units in feet.|
| maxBaroAltitude       |float       |None     |Eg 30000, units in feet.|
| arrivalAirport        |string      |None     |Broken: No reliable way to get this info. Eg "EHAM", case insensitive.|
| departureAirport      |string      |None     |Eg "EHAM", case insensitive. Might be slow as it calls to the api for every aircraft.|
| registrationCountry   |string      |None     |Eg "Kingdom of the Netherlands.|


#### visuals
| name       | type    | default | description |
|------------|---------|---------|-------------|
| windowTheme|string   |aircraft |Sets the image. Options: "aircraft", "duck". If "aircraft", the windows contain a .png of an aircraft that rotates depending on the heading. If "duck", the windows contain a .gif of a duck walking to the left or right depening on the heading.|
| windowSize |string or list   | "small" |Set the size of the window. Options: "miniature", "small", "medium", "large", "comicallyLarge", [width, height]. Width and height must be integers|
|updateInterval|float  |1.0      |Time in seconds between moving windows around. Must be positive and non-zero.|
|tooltipFields|list     |["callsign"]        |List of fields shown when hovering over a window. May be any field from the tracking conditions or any field from [opensky_api.StateVector](https://openskynetwork.github.io/opensky-api/python.html#opensky_api.StateVector).|

#### Example settings file:
<pre> ```json 
{ 
    "core": {"openskyCredentialsPath": "credentials.json",
             "location": "Amsterdam",
             "bboxSize": "medium"},
    "api": { "apiCallDelay": 10.0 },
    "setup": { "maxWindows": 25, 
               "displayName": "eDP-1" },
    "tracking": {"inAir": 1,
                 "departureAirport": "EHAM"},
    "visuals": {"windowTheme": "duck",
                "windowSize": "small",
                "tooltipFields": ["callsign", "true_track", "baro_altitude"]}
} 
``` </pre>

#### Runtime settings updating
There are three different tiers of settings:
- Tier 1, these are cheap and easy to change:
    
  - Tracking settings
  - maxWindow
  - apiCallDelay
  - updateInterval
  - tooltipFields

- Tier 2, visual settings that might require all windows to close and reopen on the next api call:

    - windowTheme
    - windowSize

- Tier 3, settings that require restarting OverFlight:

    - openskyCredentialsPath
    - displayName
    
    for now anyway, the goal is to implement runtime changing of these too
  
    


## Dependencies
- OpenSkyApi
- pyQt6
- geopy
- qasync
- qasyncio
- wmctrl, if on linux





## Contributors

This is a project by:

[Loes Baart de la Faille](https://github.com/loesbdlf)  
[Siem Broeder](https://github.com/siembroeder)  
[Steef Broeder](https://github.com/Steef-Broeder)  

## Sources

This project will use data from the OpenSky Network for the purpose of non-profit education:

*Bringing up OpenSky: A large-scale ADS-B sensor network for research  
Matthias Schäfer, Martin Strohmeier, Vincent Lenders, Ivan Martinovic, Matthias Wilhelm  
ACM/IEEE International Conference on Information Processing in Sensor Networks, April 2014*
