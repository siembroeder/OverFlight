

from PyQt6.QtGui import QPixmap, QMovie
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel, QWidget, QToolTip

from typing import TYPE_CHECKING        # to prevent circular dependency 
if TYPE_CHECKING:
    from Mover import Mover

        
# class MainWindow(QWidget): # QMainWindow
class MainWindow(QMainWindow): # QMainWindow

    def __init__(self, bbox:tuple, initPlaneCoords:tuple, icao24:str, callsign:str|None, mover: "Mover", showOnScreenName:str|None=None):
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
                if showOnScreenName==None: # set dimensions to first screen
                    self.availableGeometry = screen.availableGeometry()
                    self.Nxpixels, self.Nypixels = self.availableGeometry.width(), self.availableGeometry.height()
                    continue 
                    
                elif screen.name() == showOnScreenName:
                    self.availableGeometry = screen.availableGeometry()
                    self.Nxpixels, self.Nypixels = self.availableGeometry.width(), self.availableGeometry.height() 
        
        self.setToolTip(callsign)
        self.setWindowTitle(f"qtApp_{icao24}")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        # self.setStyleSheet("background: transparent;")

        # self.setMouseTracking(True)

        label = QLabel(self)
        # label.setStyleSheet("background: transparent; border: none;")
        # label.setMouseTracking(True)

        # pixmap = QPixmap("Assets/duck-left.gif")
        # label.setPixmap(pixmap)
        self.setCentralWidget(label)
        # self.resize(pixmap.width(), pixmap.height())

        movie = QMovie("Assets/duck-left.gif")
        label.setMovie(movie)
        movie.start()

        pixmap = QPixmap("Assets/duck-left.gif")
        self.resize(pixmap.width(), pixmap.height())

    # def mouseMoveEvent(self, event):
    #     QToolTip.showText(event.globalPosition().toPoint(), self.callsign, self)
    #     super().mouseMoveEvent(event)

    # def leaveEvent(self, event):
    #     QToolTip.hideText()
    #     super().leaveEvent(event)


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
        
        self.customMove(pixelx, pixely)  
        print(f"Moving {self.callsign} to {pixelx}, {pixely}")
    
    def customMove(self, x, y):
        self.mover.move(x, y, self)





def main():
    print("Not supported to run as standalone .py file.")


if __name__ == "__main__":
    main()
