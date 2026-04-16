

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel

from typing import TYPE_CHECKING        # to prevent circular dependency 
if TYPE_CHECKING:
    from Mover import Mover




        
class MainWindow(QMainWindow):
    def __init__(self, bbox:tuple, initPlaneCoords:tuple, icao24:str, callsign:str|None, mover: "Mover", showOnScreenName:str="eDP-1"):
        super().__init__()
        
        self.mover = mover
        self.icao24 = icao24
        self.callsign = callsign
        self.initPlaneCoords = initPlaneCoords
        self.minLat, self.maxLat, self.minLong, self.maxLong = bbox
        
        screens = QApplication.screens()
        
        if showOnScreenName == 'all':
            self.primaryScreen = QApplication.primaryScreen()
            if self.primaryScreen is not None:
                self.virtual_geom = self.primaryScreen.virtualGeometry()
                self.Nxpixels = self.virtual_geom.getCoords()[2] + 1
                self.Nypixels = self.virtual_geom.getCoords()[3] + 1            #print(f"{self.virtual_geom=}")
        else:
            for screen in screens:
                if screen.name() == showOnScreenName:
                    self.availableGeometry = screen.availableGeometry()
                    self.Nxpixels, self.Nypixels = self.availableGeometry.width(), self.availableGeometry.height() 
        
        self.setToolTip(callsign)
        self.setWindowTitle(f"qtApp_{icao24}")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        label = QLabel(self)
        pixmap = QPixmap("Assets/duck-left.gif")
        label.setPixmap(pixmap)
        self.setCentralWidget(label)
        self.resize(pixmap.width(), pixmap.height())  
    
    def coordsToPixels(self, planeCoords:tuple) -> tuple[int, int]: 
        lon, lat = planeCoords

        # normalize to 0-1 and multiply with number of available pixels
        pixelx = int(((lon - self.minLong) / (self.maxLong - self.minLong) ) * self.Nxpixels)
        pixely = int(((lat - self.minLat)  / (self.maxLat - self.minLat)   ) * self.Nypixels) # print(f"{[pixelx,pixely]=}")
        
        # since on hyprland y axis inverted:
        pixely = self.Nypixels - pixely
        
        return pixelx, pixely
        
    def showEvent(self, a0) -> None: #a0 == event but qtwidgets complains
        """Fires when window is first shown"""
        super().showEvent(a0)             
        QTimer.singleShot(200, lambda:self.moveToPlaneLoc(self.initPlaneCoords))

    def moveToPlaneLoc(self, planeCoords:tuple) -> None:
        pixelx, pixely = self.coordsToPixels(planeCoords)
        pixelx = int(pixelx - (self.width() / 2))       # update such that image is rendered at the center rather than top left
        pixely = int(pixely - (self.height()/ 2))
        
        # self.moveOnHyprland(pixelx, pixely)  
        self.customMove(pixelx, pixely)  
        print(f"Moving {self.callsign} to {pixelx}, {pixely}")
    
    def customMove(self, x, y):
        self.mover.move(x, y, self)
    
    # def moveOnHyprland(self, x, y):
    #     subprocess.run(['hyprctl', 'dispatch', 'movewindowpixel', f'exact {x} {y},title:{self.windowTitle()}'], capture_output=True) # ^(qtApp)$







def main():
    print("Not supported to run as standalone .py file.")


if __name__ == "__main__":
    main()
