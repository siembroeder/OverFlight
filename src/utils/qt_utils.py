from PySide6.QtCore import QRect, QSize
from PySide6.QtWidgets import QApplication, QWidget


def get_screen_geometry(display_name:str|None) -> QRect:
    if display_name == "all":
        screen = QApplication.primaryScreen()
        
        if screen is None:
            raise ValueError("No primary screen found.")
        
        geom = screen.virtualGeometry()
        
    else:
        # set to first screen if not displayName, elif match to displayName, else None.
        screen = next((screen for screen in QApplication.screens() if (not display_name) or (screen.name() == display_name)), None) 
        
        if (screen is None) and (display_name is not None):
            raise NameError("display_name not found, check if you set it correctly")

        if screen is None:
            raise ValueError("No screen found. Set the display_name.")
        
        geom = screen.availableGeometry()

    return geom

def get_window_size(window_size:str|list, display_name:str|None) -> QSize:  
    default_sizes = {"miniature": 25,
                    "small": 50,
                    "medium": 100,
                    "large": 200,
                    "comicallyLarge": 500}

    nypixels = get_screen_geometry(display_name).height()
    factor = nypixels / 1080
    
    if isinstance(window_size, list):
        if len(window_size) != 2:
            raise IndexError("window_size should have exactly 2 items, or use one of the defaults: 'miniature', 'small', 'medium', 'large', 'comicallyLarge'.")

        if (window_size[0] <= 0) or (window_size[1] <= 0):
            raise ValueError("window_size should be a positive, non-zero integer.")

        return QSize(window_size[0], window_size[1])

    size = int(factor * default_sizes.get(window_size, default_sizes["small"]))
    return QSize(size, size)

def coords_to_pixels(lat: float, lon: float, parent: QWidget) -> tuple[int, int]:
    from settings import app_settings

    min_lat, max_lat, min_lon, max_lon = app_settings.bbox_at_location
    n_pixels_x, n_pixels_y = parent.width(), parent.height()

    pixel_x = int(((lon - min_lon) / (max_lon - min_lon)) * n_pixels_x)
    pixel_y = int(((lat - min_lat) / (max_lat - min_lat)) * n_pixels_y)
    pixel_y = n_pixels_y - pixel_y  # invert y axis

    return pixel_x, pixel_y
