
* [X] ~~*Move location and bbox settings from main.py to settings file.*~~ [2026-05-01]
* [X] ~~*Include logic for either bboxSize OR latitude/longitudeOffset settings.*~~ [2026-05-01]
* [X] ~~*Rename screenName to displayName*~~ [2026-05-01]
* [X] ~~*Ducks walking left/right depending on heading.*~~ [2026-05-01]
* [X] ~~*Type hinting of windows:dict[str,MainWindow] should become dict[icao24, Mainwindow]*~~ [2026-05-06]
* [X] ~~*Fix image resizing. Also check if centering image works correctly.*~~ [2026-05-06]
* [X] ~~*Fix screenName setting*~~ [2026-05-07]
* [ ] Rotate image depending on heading
    * [X] ~~*Initial heading*~~ [2026-05-07] 
    * [ ] Update heading
* [ ] Split WindowTracker class into multiple classes
    * [X] ~~*Filter to separate class*~~ [2026-05-03]
    * [ ] What to do with fetching/deadreckoning loop?
* [ ] Make small, medium, large bbox sizes
    * [X] ~~*All three exist*~~ [2026-05-03]
    * [ ] Verify that the sizes make sense compared to 16:9 ratio.
* [ ] When skipping api call for short spacing, extract aircraft not already being tracked
    * [X] ~~*Built*~~ [2026-05-04]
    * [ ] Test
* [ ] Use some way to smoothen transition to incoming new api states. eg kallman filter or deadreckoning strechting

        When new api call comes in, calculate position of where the window would be for next call, move there with required heading/velocity. 
        If no new call and position reached, then take latest heading/velocity and deadreckon from there.
        When new call, again calculate position it would be after apiCallDelay seconds, move there. etc 
* [ ] Include plane/helicopter images and select based on type
* [ ] Add other windowmanagers / desktop environments, eg sway or kwin
* [ ] Move window first while not visible, then show
* [ ] Remove window borders completely on windows
* [ ] Fix arrival airport filters.
* [ ] Add more info to tooltip and toggle it in settings.