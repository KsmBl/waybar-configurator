"""Application bootstrap: sets up GTK3 and launches the main window."""

import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk  # noqa: E402

from waybar_configurator.app_window import AppWindow  # noqa: E402


class WaybarConfiguratorApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="de.synthelicz.WaybarConfigurator",
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
        )
        self._window = None
        self._open_path = None

    def do_open(self, files, n_files, hint):
        # Allow launching with a specific config file: waybar-configurator path/to/config.jsonc
        if files:
            self._open_path = files[0].get_path()
        self.activate()

    def do_activate(self):
        if self._window is None:
            self._window = AppWindow(self, initial_config_path=self._open_path)
        self._window.present()


def main(argv=None):
    app = WaybarConfiguratorApp()
    return app.run(argv if argv is not None else sys.argv)
