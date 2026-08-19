from PySide6.QtWidgets import ( 
    QMainWindow, 
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout,
    QLabel,
)
from PySide6.QtGui import QIcon, QImage, QPixmap, QColor

class SettingsWindow(QMainWindow):
    def __init__(self, icon_path : str):
        super().__init__()
        icon = QIcon(icon_path)
        self.setWindowTitle("OverFlight settings")
        self.setWindowIcon(icon)
        self._setup_ui()

    def _setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Left side: time left and setters
        left_panel = QWidget()
        layout.addWidget(left_panel)
        left_layout = QVBoxLayout(left_panel)

        # Time left box
        time_left_widget = QWidget()
        time_left_widget.setStyleSheet("background-color: gray;")
        left_layout.addWidget(time_left_widget)
        time_left_layout = QVBoxLayout(time_left_widget)
        time_left_title = QLabel("Time left using current settings")
        time_left_layout.addWidget(time_left_title)
        time_left_content = QLabel("x minutes etc")
        time_left_layout.addWidget(time_left_content)

        # Settings
        settings_widget = QWidget()
        left_layout.addWidget(settings_widget)
        settings_layout = QVBoxLayout(settings_widget)
        
        delay_widget = QLabel("delay")
        settings_layout.addWidget(delay_widget)
        windows_widget = QLabel("max_windows")
        settings_layout.addWidget(windows_widget)
        theme_widget = QLabel("theme")
        settings_layout.addWidget(theme_widget)
        size_widget = QLabel("size")
        settings_layout.addWidget(size_widget)

        # Right side: map 
        label = QLabel(self)
        pixmap = QPixmap('assets\\Complete-World-Map_Original-Map.jpg')
        pixmap.setDevicePixelRatio(3)
        label.setPixmap(pixmap)
        layout.addWidget(label)

    