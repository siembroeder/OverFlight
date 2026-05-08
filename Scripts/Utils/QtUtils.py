
from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication



def windowIsOpen(icao24:str) -> bool:
    title = f"qtApp_{icao24}"
    return any(w.windowTitle() == title and w.isVisible() for w in QApplication.topLevelWidgets())


def getScreenGeometry(displayName:str|None) -> QRect:
    if displayName == "all":
        screen = QApplication.primaryScreen()
        
        if screen is None:
            raise ValueError("No primary screen found.")
        
        geom = screen.virtualGeometry()
        
    else:
        # set to first screen if not displayName, elif match to displayName, else None.
        screen = next((screen for screen in QApplication.screens() if not displayName or screen.name() == displayName), None) 
        
        if screen is None:
            raise ValueError("No screen found. Set the displayName.")
        
        geom = screen.availableGeometry()

    return geom

