
import subprocess

from platformOs import getPlatform, getSessionType, getWindowManager



class Mover():
    def __init__(self):
        
        self.userPlatform = getPlatform()
        self.userSession  = getSessionType() 
        
        self.specificMover = self.determineMover()
        
    def determineMover(self):
        if "windows" in self.userPlatform:
            return WindowsMover()
            
        elif "linux" in self.userPlatform:
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
        
        
    def move(self, x, y, windowTitle):
        return self.specificMover.move(x, y, windowTitle)



    
class WindowsMover:
    def move(self, x, y, windowTitle):
        # Qt move
        pass


class X11Mover:
    def move(self, x, y, windowTitle):
        # Qt move
        pass


class HyprlandMover:
    def move(self, x, y, windowTitle):
        subprocess.run(['hyprctl', 'dispatch', 'movewindowpixel', f'exact {x} {y},title:{windowTitle}'], capture_output=True) # ^(qtApp)$
        