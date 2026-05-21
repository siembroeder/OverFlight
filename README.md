# OverFlight

Overflight is a desktop agent that displays nearby aircrafts through icons that mirror their flight paths on the screen. 

## Installation

Before running OverFlight, make sure you have `uv`, a package and project manager. Installation can be found at: https://docs.astral.sh/uv/getting-started/installation/. 

Clone the directory using `git clone https://github.com/siembroeder/OverFlight`

**Optional**:<br>
Create an account (free) at https://opensky-network.org/, go to 'Account' - 'API client' and click 'Create & Download Credential, and put the credentials.json into the OverFlight directory. <br>

>You can use OverFlight without an opensky account but creating an account gives more api credits (you can use OverFlight for longer) and api rate limiting drops from 10 to 5 seconds.

To start OverFlight, use the command `uv run src/main.py`. 

> **_On windows:_** For the icons to be transparent, the setting `transparency effects` under `Personalisation > Colours` must be turned off. 

## Prototype / Development

Current functionality:
- Configure in settings.yaml using below documentation.
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
- Sway (Provisional support only), add these to your sway config:
  - for_window [title="^OverFlightWindow_"] sticky enable


### Settings / Configuration
Use the settings.yaml file to set your preferences for the categories core, api, setup, visuals, and tracking. 

#### core

|name                  |type  |default           |description|
|----------------------|------|------------------|-----------|
|openskyCredentialsPath|string|".credentials.json"|Path to your opensky credentials .json file.|
|location              |string|"Schiphol"        |Any location in the world that geopy recognizes.|
|bboxSize              |string|"small"           |Preconfigured bounding box sizes, set to "local", "small", "medium", "large", "veryLarge", or "huge". May be omitted if both latitudeOffset and LongitudeOffset are used.|
|longitudeOffset, latitudeOffset|float,float|None,None|Can be used to set the width and height of the bounding box. Must both be a non-zero, positive float. Do not use if bboxSize is used.|

##### Configuring for Boundingbox / Area 
- Option 1: Set bboxSize from ["small", "medium", "large"]
- Option 2: Set BOTH longitudeOffset AND latitudeOffset to some non-zero float. The resulting bounding box has dimensions (2\*longitudeOffset x 2\*latitudeOffset)
- Invalid: Using bboxSize, latitudeOffset, and longitudeOffset.
- Invalid: Using only one of latitudeOffset, longitudeOffset.

#### api

| name         | type | default | description |
|--------------|------|---------|-------------|
|apiCallDelay  |float |5.0     | Spacing between consecutive calls to opensky_api.get_states(). Any value smaller than 5 seconds results in rate limiting.|

#### setup

| name       | type    | default | description |
|------------|---------|---------|-------------|
| maxWindows |int      |25       | Maximum number of aircraft windows on the screen.|
| displayName |string   |First entry in QApplication.screens() | Select the name of display on which to project the windows, eg "eDP-1", "HDMI-1-A", or "DP-1". If "all" use all displays. Depending on scaling of the displays, part of the bounding box may be "outside" the displays.|

#### visuals
| name       | type    | default | description |
|------------|---------|---------|-------------|
| windowTheme|string   |aircraft |Sets the image. Options: "aircraft", "duck". If "aircraft", the windows contain a .png of an aircraft that rotates depending on the heading. If "duck", the windows contain a .gif of a duck walking to the left or right depening on the heading.|
| windowSize |string or list   | "small" |Set the size of the window. Options: "miniature", "small", "medium", "large", "comicallyLarge", [width, height]. Width and height must be integers|
|updateInterval|float  |1.0      |Time in seconds between moving windows around. Must be positive and non-zero.|
|tooltipFields|list     |["callsign"]        |List of fields shown when hovering over a window. May be any field from the tracking conditions or any field from [opensky_api.StateVector](https://openskynetwork.github.io/opensky-api/python.html#opensky_api.StateVector).|

#### tracking
Aircraft are filtered based on these conditions.

| name                  | type    | default | description |
|-----------------------|---------|---------|-------------|
| icao24                |string   |None     |Eg "485F82", case insensitive.|
| callsign              |string   |None     |Eg "KLM641", case insensitive.|
| airline               |string   |None     |Filter the callsign for airline designator, eg "KLM" or "DLH".|
| allowedTimePositionLag|float    |None     |Filter for aircraft with time position timestamp (Unix time) greater than timestamp at filtering minus allowedLastContactLag.|
| allowedLastContactLag |float    |None     |Filter for aircraft with last contact timestamp (Unix time) greater than timestamp at filtering minus allowedLastContactLag.|
| squawk                |string   |None     |Eg "1000" or "7700".|
| inAir                 |int      |None     |Set to 1 to only show aircraft in the air. Shouldn't be set together with onGround.|
| onGround              |int      |None     |Set to 1 to only show aircraft on the ground. Shouldn't be set together with inAir.|
| minVelocity           |float    |None     |Filter for aircraft with a velocity higher than minVelocity in m/s.|
| maxVelocity           |float    |None     |Filter for aircraft with a velocity lower than maxVelocity in m/s.|
| trueTrackRange        |list     |None     |Filter for aircraft with a true_track (heading) that's included in the range. Setting [0,90] shows only aircraft flying northeast. Set [350, 10] for aircraft only going north.|
| minVerticalRate       |float    |None     |Filter for aircraft with a vertical rate higher than minVerticalRate in m/s.|
| maxVerticalRate       |float    |None     |Filter for aircraft with a vertical rate lower than maxVerticalRate in m/s.|
| minGeoAltitude        |float    |None     |Eg 30000, units in feet.|
| maxGeoAltitude        |float    |None     |Eg 30000, units in feet.|
| minBaroAltitude       |float    |None     |Eg 30000, units in feet.|
| maxBaroAltitude       |float    |None     |Eg 30000, units in feet.|
| spi                   |int      |None     |Set to 1 to only show aircraft with the special purpose indicator flag set to True, eg when squawking ident.|
| positionSource        |list[int]|[0,1,2,3]|Origin of this state's position: <br>0 = ADS-B, <br>1 = ASTERIX, <br>2 = MLAT, <br>3 = FLARM.|
| category              |list[int]|[0-20]    |Aircraft category (nearly always 0), set to eg [4, 6] to only show Large and Heavy. To exclude certain categories set to ["!0", "!1"], in this case all entries should be strings starting with "!". <br>0 = No information at all, <br>1 = No ADS-B Emitter Category Information, <br>2 = Light (< 5500 lbs), <br>3 = Small (15500 to 75000 lbs), <br>4 = Large (75000 to 300000 lbs), <br>5 = High Vortex Large (aircraft such as B-757), <br>6 = Heavy (> 300000 lbs), <br>7 = High Performance (> 5g acceleration and 400 kts), <br>8 = Rotorcraft, <br>9 = Glider / sailplane, <br>10 = Lighter-than-air, <br>11 = Parachutist / Skydiver, <br>12 = Ultralight / hang-glider / paraglider, <br>13 = Reserved, <br>14 = Unmanned Aerial Vehicle, <br>15 = Space / Trans-atmospheric vehicle, <br>16 = Surface Vehicle – Emergency Vehicle, <br>17 = Surface Vehicle – Service Vehicle, <br>18 = Point Obstacle (includes tethered balloons), <br>19 = Cluster Obstacle, <br>20 = Line Obstacle.|
| arrivalAirport        |string      |None     |Airport ICAO code, eg "EHAM", case insensitive.|
| departureAirport      |string      |None     |Airport ICAO code, eg "EHAM", case insensitive.|
| originCountry         |string      |None     |Eg "Kingdom of the Netherlands.|
| sensors               |list[int]   |None     |Must be a list of integers representing the serial numbers of sensors.<br>This filter is only accessible to users with a paid openskyapi account, for free users the vehicle's sensors are always None.    |


#### visuals
| name       | type    | default | description |
|------------|---------|---------|-------------|
| windowTheme|string   |aircraft |Sets the image. Options: "aircraft", "duck". If "aircraft", the windows contain a .png of an aircraft that rotates depending on the heading. If "duck", the windows contain a .gif of a duck walking to the left or right depening on the heading.|
| windowSize |string or list   | "small" |Set the size of the window. Options: "miniature", "small", "medium", "large", "comicallyLarge", [width, height]. Width and height must be integers|
|updateInterval|float  |1.0      |Time in seconds between moving windows around. Must be positive and non-zero.|
|tooltipFields|list     |["callsign"]        |List of fields shown when hovering over a window. May be any field from the tracking conditions or any field from [opensky_api.StateVector](https://openskynetwork.github.io/opensky-api/python.html#opensky_api.StateVector).|
|fallbackTypecode|string|C172    |When data/icao24_typecode_aircraft and opensky api can't find the typecode associated with a certain icao24, use this typecode instead.|

#### Example settings file:
<pre> ```yaml 
core:
  openskyCredentialsPath: credentials.json
  location: Amsterdam
  bboxSize: medium

api:
  apiCallDelay: 5.0

setup:
  maxWindows: 25

visuals:
  windowTheme: duck
  windowSize: small
  tooltipFields: [callsign, true_track]

tracking:
  inAir: 1
  departureAirport: EHAM
``` </pre>

><details>
><summary>Complete settings template</summary>
><pre>```yaml
>core:
>    openskyCredentialsPath:
>    location:
>    bboxSize:
>
>api:
>    apiCallDelay:
>
>setup:
>    maxWindows:
>    displayName:
>
>visuals:
>    windowTheme:
>    windowSize:
>    updateInterval:
>    tooltipFields:
>
>tracking:
>    icao24:
>    callsign:
>    airline:
>    squawk:
>    inAir:
>    onGround:
>    arrivalAirport:
>    departureAirport:
>    minVelocity:
>    maxVelocity:
>    minGeoAltitude:
>    maxGeoAltitude:
>    minBaroAltitude:
>    maxBaroAltitude:
>    minVerticalRate:
>    maxVerticalRate:
>    trueTrackRange:
>    spi:
>    sensors:
>    category:
>    originCountry:
>    allowedLastContactLag:
>    allowedTimePositionLag: ```
></pre>
></details>

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
See [`pyproject.toml`](pyproject.toml)

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
