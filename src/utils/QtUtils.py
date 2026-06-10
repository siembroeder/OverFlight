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

def getWindowSize(windowSize:str|list, nypixels:int) -> QSize:

    defaultSizes = {"miniature": 25,
                    "small": 50,
                    "medium": 100,
                    "large": 200,
                    "comicallyLarge": 500}
    
    factor = nypixels / 1080
    
    if isinstance(windowSize, list):
        if len(windowSize) != 2:
            raise IndexError("windowSize should have exactly 2 items, or use one of the defaults: 'miniature', 'small', 'medium', 'large', 'comicallyLarge'.")
        
        if (windowSize[0] <= 0) or (windowSize[1] <= 0):
            raise ValueError("windowSize should be a positive, non-zero integer.")
        
        return QSize(windowSize[0], windowSize[1])
    
    size = int(factor * defaultSizes.get(windowSize, defaultSizes["small"]))
    return QSize(size, size)
    
