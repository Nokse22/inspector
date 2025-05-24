# main.py
#
# Copyright 2023 Nokse
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys

from gi.repository import Gio, Adw
from .window import InspectorWindow


class CommandTestApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.nokse22.inspector',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action, ['F1'])

        self.create_action('reload', self.on_reload_action, ['<primary>r'])

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        self.win = self.props.active_window
        if not self.win:
            self.win = InspectorWindow(application=self)
        self.win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
                                application_name=_("Inspector"),
                                application_icon='io.github.nokse22.inspector',
                                developer_name='Nokse',
                                developers=["Nokse22 https://github.com/Nokse22","David Stephenson https://github.com/David-Stephenson", "soumyaDghosh https://github.com/soumyaDghosh", "Epig-is-a-llama https://github.com/Epig-is-a-llama"],
                                issue_url='https://github.com/Nokse22/inspector/issues',
                                website='https://github.com/Nokse22/inspector',
                                version='0.3.0',
                                copyright='© 2023 Nokse')
        # Translator credits. Replace "translator-credits" with your name/username, and optionally an email or URL. 
        # One name per line, please do not remove previous names.
        about.set_translator_credits(_("translator-credits"))
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print('app.preferences action activated')

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def on_reload_action(self, *args):
        self.win.reload_current()


def main(version):
    """The application's entry point."""
    app = CommandTestApplication()
    return app.run(sys.argv)
