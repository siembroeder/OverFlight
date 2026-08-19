from PySide6.QtWidgets import ( 
    QMainWindow, 
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout,
    QLabel,
    QSlider, 
    QLineEdit,
    QComboBox
)
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QIcon, QImage, QPixmap, QColor

from settings.settings import app_settings

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
        left_panel.setMinimumWidth(300)
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
        
        delay_widget = QWidget()
        delay_layout = QHBoxLayout(delay_widget)
        delay_title = QLabel("Delay on api-call")
        delay_layout.addWidget(delay_title, stretch=1)
        delay_slider = QSlider()
        delay_slider.setOrientation(Qt.Orientation.Horizontal)
        delay_slider.setMinimum(5)
        delay_slider.setMaximum(30)
        delay_slider.valueChanged.connect(self._on_delay_slider_changed)
        delay_layout.addWidget(delay_slider)
        settings_layout.addWidget(delay_widget)

        windows_widget = QWidget()
        windows_layout = QHBoxLayout(windows_widget)
        windows_title = QLabel("Maximum number of planes")
        windows_layout.addWidget(windows_title, stretch=1)
        windows_input = QLineEdit()
        windows_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        windows_input.setFixedWidth(50)
        windows_input.setText(str(app_settings.setup.max_windows))
        windows_layout.addWidget(windows_input)
        settings_layout.addWidget(windows_widget)

        theme_widget = QWidget()
        theme_layout = QHBoxLayout(theme_widget)
        theme_title = QLabel("Theme")
        theme_layout.addWidget(theme_title, stretch=1)
        theme_input = QComboBox()
        theme_input.addItems(["Airplane", "Duck"])
        theme_layout.addWidget(theme_input)
        settings_layout.addWidget(theme_widget)

        size_widget = QWidget()
        size_layout = QHBoxLayout(size_widget)
        size_title = QLabel("Size of icons")
        size_layout.addWidget(size_title, stretch=1)
        size_input = QLineEdit()
        size_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        size_input.setFixedWidth(50)
        size_input.setText(str(app_settings.visuals.window_size)) #TODO: change settings for this to be an int. 
        size_layout.addWidget(size_input)
        settings_layout.addWidget(size_widget)

        # Right side: map 
        label = QLabel(self)
        pixmap = QPixmap('assets\\Complete-World-Map_Original-Map.jpg')
        pixmap.setDevicePixelRatio(3)
        label.setPixmap(pixmap)
        layout.addWidget(label)

    @Slot(int)
    def _on_delay_slider_changed(self, new_value: int):
        pass # TODO update settings
