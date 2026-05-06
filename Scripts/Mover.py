
import subprocess


from CustomQtWindow import MainWindow
from PlatformOs import getUserPlatform, getSessionType, getWindowManager



class Mover():
    def __init__(self):
        
        self.userPlatform = getUserPlatform()
        
        self.systemDependentMover = self.determineMover()
        
    def determineMover(self):
        if "windows" in self.userPlatform:
            return WindowsMover()
            
        elif "linux" in self.userPlatform:
            self.userSession  = getSessionType() 
            if self.userSession == "x11":
                return X11Mover()
            
            elif self.userSession == "wayland":     
                wm = getWindowManager().lower()

                if "hyprland" in wm:
                    return HyprlandMover()
                else:
                    raise NotImplementedError("Your wm is not supported.")     
                
            else:
                raise NotImplementedError("Your session is not supported.")  
                
        else:
            raise NotImplementedError("Your operating system is not supported")
             
    def move(self, x:int, y:int, window:MainWindow):
        return self.systemDependentMover.move(x, y, window)



    
class WindowsMover:
    def move(self, x:int, y:int, window:MainWindow):
        window.move(x, y)

class X11Mover:
    def move(self, x:int, y:int, window:MainWindow):
        window.move(x, y)

class HyprlandMover:
    def move(self, x:int, y:int, window:MainWindow):
        subprocess.run(['hyprctl', 'dispatch', 'movewindowpixel', f'exact {x} {y},title:{window.windowTitle()}'], capture_output=True) # ^(qtApp)$
        