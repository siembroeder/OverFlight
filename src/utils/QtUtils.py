
from PySide6.QtCore import QRect, QSize
from PySide6.QtWidgets import QApplication



def windowIsOpen(icao24:str) -> bool:
    title = f"OverFlightWindow_{icao24}"
    return any((w.windowTitle() == title) and w.isVisible() for w in QApplication.topLevelWidgets())


def getScreenGeometry(displayName:str|None) -> QRect:
    if displayName == "all":
        screen = QApplication.primaryScreen()
        
        if screen is None:
            raise ValueError("No primary screen found.")
        
        geom = screen.virtualGeometry()
        
    else:
        # set to first screen if not displayName, elif match to displayName, else None.
        screen = next((screen for screen in QApplication.screens() if (not displayName) or (screen.name() == displayName)), None) 
        
        if screen is None:
            raise ValueError("No screen found. Set the displayName.")
        
        geom = screen.availableGeometry()

    return geom


def getWindowSize(windowSize:str|list) -> QSize:
    defaultSizes = {"miniature": QSize(25, 25),
                    "small":     QSize(50, 50),
                    "medium":    QSize(100, 100),
                    "large":     QSize(200, 200),
                    "comicallyLarge": QSize(500, 500)}
    
    if isinstance(windowSize, list):
        if len(windowSize) == 2:
            return QSize(windowSize[0], windowSize[1])
        raise IndexError("imageSize should have exactly 2 items")
    
    if windowSize not in defaultSizes.keys():
        windowSize = "small"

    return defaultSizes[windowSize] 


def getTypecodeScaleFactor(typecode:str) -> float:
    typecode = typecode.upper()
    
    if typecode.startswith("B74"):
        return 1.3
    elif typecode == "C172":
        return 0.5
    
    return 1.0

        
