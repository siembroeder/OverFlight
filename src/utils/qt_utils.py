from PySide6.QtCore import QRect, QSize
from PySide6.QtWidgets import QApplication

def window_is_open(icao24:str) -> bool:
    title = f"OverFlightWindow_{icao24}"
    return any((w.windowTitle() == title) and w.isVisible() for w in QApplication.topLevelWidgets())

def get_screen_geometry(display_name:str|None) -> QRect:
    if display_name == "all":
        screen = QApplication.primaryScreen()
        
        if screen is None:
            raise ValueError("No primary screen found.")
        
        geom = screen.virtualGeometry()
        
    else:
        # set to first screen if not displayName, elif match to displayName, else None.
        screen = next((screen for screen in QApplication.screens() if (not display_name) or (screen.name() == display_name)), None) 
        
        if screen is None:
            raise ValueError("No screen found. Set the displayName.")
        
        geom = screen.availableGeometry()

    return geom

def get_window_size(window_size:str|list) -> QSize:
    default_sizes = {"miniature": QSize(25, 25),
                    "small":     QSize(50, 50),
                    "medium":    QSize(100, 100),
                    "large":     QSize(200, 200),
                    "comicallyLarge": QSize(500, 500)}
    
    if isinstance(window_size, list):
        if len(window_size) == 2:
            return QSize(window_size[0], window_size[1])
        raise IndexError("imageSize should have exactly 2 items")
    
    if window_size not in default_sizes.keys():
        window_size = "small"

    return default_sizes[window_size] 
