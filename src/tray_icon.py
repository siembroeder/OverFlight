import os
import sys
import platform
import webbrowser
import subprocess

from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from paths import get_settings_path
from main_window import MainWindow, SPAWN_DELAY
from settings.settings_window import SettingsWindow

class TrayIcon(QSystemTrayIcon):
    def __init__(self, app:QApplication, window:MainWindow, settings_window:SettingsWindow, icon_path: str, parent=None):
        super().__init__(QIcon(icon_path), parent)
        self.app = app
        self.window = window
        self.settings_window = settings_window
        self.setToolTip("OverFlight") # TODO: add the version 

        menu = QMenu()

        info_action = QAction("Info", self)
        info_action.triggered.connect(self._open_repository)
        menu.addAction(info_action)

        debug_action = QAction("Debug", self)
        debug_action.triggered.connect(self._show_terminal)
        menu.addAction(debug_action)

        restart_action = QAction("Restart", self)
        restart_action.triggered.connect(self._restart)
        menu.addAction(restart_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)

        open_settings_action = QAction("Open settings", self)
        open_settings_action.triggered.connect(self._open_settings)
        menu.addAction(open_settings_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        # left click / double click toggles the window
        if reason is QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_window()

    def _toggle_window(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            self._show_window()

    def _show_window(self):
        self.window._show_mainwindow(delay=SPAWN_DELAY)

    def _open_repository(self):
        webbrowser.open("https://github.com/siembroeder/OverFlight")

    def _restart(self):
        self.app.quit()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _open_settings(self, ):
        self.settings_window.show()

        # path = get_settings_path()
        # system = platform.system()
    
        # if system == "Windows" and hasattr(os, "startfile"):
        #     os.startfile(path)
        # elif system == "Linux":
        #     subprocess.run(["xdg-open", path])
        # else:
        #     raise NotImplementedError("Opening the settings file from the trayicon isn't supported for your operating system.")

    def _show_terminal(self):
        # TODO: Implement
        pass
