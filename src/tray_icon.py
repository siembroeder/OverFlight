import os
import sys
import webbrowser

from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from main_window import MainWindow, SPAWN_DELAY

class TrayIcon(QSystemTrayIcon):
    def __init__(self, app:QApplication, window:MainWindow, icon_path: str, parent=None):
        super().__init__(QIcon(icon_path), parent)
        self.app = app
        self.window = window
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

    def _show_terminal(self):
        # TODO: Implement
        pass
