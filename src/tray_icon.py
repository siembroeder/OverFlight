import webbrowser

from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


class TrayIcon(QSystemTrayIcon):
    def __init__(self, app:QApplication, window, icon_path: str, parent=None):
        super().__init__(QIcon(icon_path), parent)
        self.window = window
        self.setToolTip("OverFlight") # TODO: add the version 

        menu = QMenu()

        info_action = QAction("Info", self)
        info_action.triggered.connect(self._open_repository)
        menu.addAction(info_action)

        debug_action = QAction("Debug", self)
        debug_action.triggered.connect(self._show_terminal)
        menu.addAction(debug_action)

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
        self.window.show()

    def _open_repository(self):
        webbrowser.open("https://github.com/siembroeder/OverFlight")

    def _show_terminal(self):
        # TODO: Implement
        pass
