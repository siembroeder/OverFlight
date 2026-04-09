# OverFlight

Overflight is a desktop agent that displays nearby aircrafts through icons that mirror their flight paths on the screen. 



## Prototype / Development
Not ready for use.
Current functionality:
- choose a location eg "Alkmaar", bounding box eg "small", monitor eg "eDP-1", and maximum amount of windows allowed eg "3".
- spawns a duck at the corrent location relative to the chosen bounding box and screen.
- move the window/duck when a new api call comes in.
- close the window when the aircraft moves out of the bounding box.
- creates a new window if a new aircraft moves into the bounding box and the max number of windows isn't reached.
- runs indefinitely.



Only Hyprland is supported for now, add these to your hyprland.conf file:
- windowrule = float on, match:title ^qtApp_.*
- windowrule = no_blur on, match:title ^qtApp_.*
- windowrule = border_size 0, match:title ^qtApp_.*
- windowrule = no_shadow on, match:title ^qtApp_.*
















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
