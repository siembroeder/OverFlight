
# PyQt imports
from PyQt6.QtWidgets import QApplication



def windowIsOpen(icao24:str) -> bool:
    title = f"qtApp_{icao24}"
    return any(w.windowTitle() == title and w.isVisible() for w in QApplication.topLevelWidgets())

