from PySide6.QtWidgets import ( 
    QMainWindow, 
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout,
    QLabel,
    QSlider, 
    QLineEdit,
    QComboBox,
    QPushButton
)
from PySide6.QtCore import Slot, Signal, Qt
from PySide6.QtGui import QIcon, QImage, QPixmap, QColor

from settings.settings import app_settings, Settings

class SettingsWindow(QMainWindow):
    settings_changed = Signal()

    class TempSettings():
        delay: float
        max_windows: int
        theme: str 
        window_size: int

        def __init__(self):
            self.delay = app_settings.api.api_call_delay
            self.max_windows = app_settings.setup.max_windows
            self.theme = app_settings.visuals.window_theme
            # self.window_size = = app_settings.visuals.window_size 

        def has_changed(self):
            print(f"delay: {self.delay} vs {app_settings.api.api_call_delay}")
            print(f"delay: {self.max_windows} vs {app_settings.setup.max_windows}")
            print(f"delay: {self.theme} vs {app_settings.visuals.window_theme}")
            value = (not self.delay is app_settings.api.api_call_delay) or (not self.max_windows is app_settings.setup.max_windows) or (not self.theme is app_settings.visuals.window_theme)
            print(f"Return value: {value}")
            return value

    def __init__(self, icon_path : str):
        super().__init__()
        icon = QIcon(icon_path)
        self.setWindowTitle("OverFlight settings")
        self.setWindowIcon(icon)
        self.temp_settings = self.TempSettings()
        self._setup_ui()
        self.settings_changed.connect(self._on_settings_changed)


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
        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setMinimum(5)
        self.delay_slider.setMaximum(30)
        self.delay_slider.setValue(app_settings.api.api_call_delay)
        self.delay_slider.setMinimumWidth(100)
        self.delay_slider.valueChanged.connect(self._on_delay_slider_changed)
        self.delay_slider.sliderReleased.connect(self._on_delay_changed)
        delay_layout.addWidget(self.delay_slider)
        self.delay_value = QLabel(str(self.delay_slider.value()))
        self.delay_value.setFixedWidth(20)
        delay_layout.addWidget(self.delay_value)
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

        self.save_button = QPushButton()
        self._on_settings_changed()
        settings_layout.addWidget(self.save_button)

        # Right side: map 
        label = QLabel(self)
        pixmap = QPixmap('assets\\Complete-World-Map_Original-Map.jpg')
        pixmap.setDevicePixelRatio(3)
        label.setPixmap(pixmap)
        layout.addWidget(label)

    @Slot(int)
    def _on_delay_slider_changed(self, new_value: int):
        self.delay_value.setText(str(new_value))

    @Slot()
    def _on_delay_changed(self):
        self.temp_settings.delay = self.delay_slider.value()
        self.settings_changed.emit()

    @Slot()
    def _on_settings_changed(self):
        if self.temp_settings.has_changed():
            self.save_button.setText("Save settings")
            self.save_button.setFlat(True)
        else:
            self.save_button.setText("Settings already saved")
            self.save_button.setFlat(False)
