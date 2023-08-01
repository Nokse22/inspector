# window.py
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

from gi.repository import Adw
from gi.repository import Gtk
import gi, os, subprocess, threading, time, json, re

#@Gtk.Template(resource_path='/org/gnome/Example/window.ui')
class CommandTestWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'CommandTestWindow'

    #text_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.hb = Adw.HeaderBar(css_classes=["flat"])
        self.set_titlebar(self.hb)

        self.set_default_size(1000, 700)

        a = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        view_stack = Adw.ViewStack(vexpand=True)
        a.append(view_stack)

        self.disks_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrolled_window = Gtk.ScrolledWindow()
        clamp = Adw.Clamp(margin_start=10, margin_end=10)
        clamp.set_child(self.disks_content)
        scrolled_window.set_child(clamp)
        view_stack.add_titled_with_icon(scrolled_window,"disk","Disk", "drive-harddisk-symbolic")

        self.memory_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrolled_window = Gtk.ScrolledWindow()
        clamp = Adw.Clamp(margin_start=10, margin_end=10)
        clamp.set_child(self.memory_content)
        scrolled_window.set_child(clamp)
        view_stack.add_titled_with_icon(scrolled_window,"mem","Memory", "drive-harddisk-solidstate-symbolic")

        self.pci_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrolled_window = Gtk.ScrolledWindow()
        clamp = Adw.Clamp(margin_start=10, margin_end=10)
        clamp.set_child(self.pci_content)
        scrolled_window.set_child(clamp)
        view_stack.add_titled_with_icon(scrolled_window,"pci","PCI", "drive-optical-symbolic")

        self.usb_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_bottom=100)
        scrolled_window = Gtk.ScrolledWindow()
        clamp = Adw.Clamp(margin_start=10, margin_end=10)
        clamp.set_child(self.usb_content)
        scrolled_window.set_child(clamp)
        view_stack.add_titled_with_icon(scrolled_window,"usb","Usb", "drive-harddisk-usb-symbolic")

        self.network_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_bottom=100)
        scrolled_window = Gtk.ScrolledWindow()
        clamp = Adw.Clamp(margin_start=10, margin_end=10)
        clamp.set_child(self.network_content)
        scrolled_window.set_child(clamp)
        view_stack.add_titled_with_icon(scrolled_window,"network","Network", "network-transmit-receive-symbolic")

        self.d=Adw.ViewSwitcherTitle()
        self.d.set_stack(view_stack)
        self.d.set_title("Inspector")
        self.hb.set_title_widget(self.d)

        self.c = Adw.ViewSwitcherBar()
        self.c.set_stack(view_stack)
        self.c.set_reveal(True)
        a.append(self.c)

        self.f()

        self.set_child(a)
        self.d.connect("notify::title-visible",self.f)

        out = self.execute_terminal_command("lsblk -J")
        data = json.loads(out)
        for device in data["blockdevices"]:
            text = f"Name: {device['name']}, Size: {device['size']}"
            group = Adw.PreferencesGroup(title=text, margin_bottom=20)
            self.disks_content.append(group)
            if "children" in device:
                for partition in device["children"]:
                    box = Gtk.Box(homogeneous=True, hexpand=True)
                    #box.append(Gtk.Label(label=))
                    box.append(Gtk.Label(label=partition['size'], wrap=True))
                    box.append(Gtk.Label(label=partition['mountpoints'], wrap=True))
                    row = Adw.ActionRow(title=partition['name'])
                    row.add_suffix(box)
                    group.add(row)

        out = self.execute_terminal_command("lsmem -J")
        data = json.loads(out)
        group2 = Adw.PreferencesGroup(title="Ranges", margin_bottom=20)
        self.memory_content.append(group2)
        total = 0
        for device in data["memory"]:
            total += float(device['size'].replace('G', ''))
            text = "range " + device['block']
            box = Gtk.Box(homogeneous=True, hexpand=True)
            box.append(Gtk.Label(label=device['size'], wrap=True))
            box.append(Gtk.Label(label=device['block'], wrap=True))
            row = Adw.ActionRow(title="Memory", subtitle=device['range'])
            row.add_suffix(box)
            group2.add(row)
        group2 = Adw.PreferencesGroup(title="Total", margin_bottom=20)
        self.memory_content.append(group2)
        text = "range " + device['block']
        label = Gtk.Label(label=str(total)+"G", wrap=True)
        row = Adw.ActionRow(title="Total")
        row.add_suffix(label)
        group2.add(row)

        out = self.execute_terminal_command("lspci")
        out = out.splitlines()
        text = "range "
        pattern = r'(\S+)\s(.*?):\s(.*)'
        for line in out:
            match = re.match(pattern, line)
            if match:
                first_part = match.group(1)
                second_part = match.group(2)
                third_part = match.group(3)

                group2 = Adw.PreferencesGroup(title=first_part, margin_bottom=20)
                self.pci_content.append(group2)

                action_row = Adw.ActionRow(title="What is")
                action_row.add_suffix(Gtk.Label(label=second_part))
                group2.add(action_row)

                action_row = Adw.ActionRow(title="Name")
                action_row.add_suffix(Gtk.Label(label=third_part, wrap=True, xalign=1))
                group2.add(action_row)


        out = self.execute_terminal_command("lsusb")
        out = out.splitlines()
        text = "Usb"
        for line in out:
            result = []
            parts = line.split(' ')
            bus_device = ' '.join(parts[:4])
            identifier = ' '.join(parts[4:6])
            vendor_product = ' '.join(parts[6:])
            result.append(bus_device)
            result.append(identifier)
            result.append(vendor_product)

            group2 = Adw.PreferencesGroup(title=result[0], margin_bottom=20)
            self.usb_content.append(group2)


            name, value = result[1].split(' ', 1)
            print(value)
            action_row = Adw.ActionRow(title=name)
            action_row.add_suffix(Gtk.Label(label=value, xalign=1))
            group2.add(action_row)


            action_row = Adw.ActionRow(title="Name")
            action_row.add_suffix(Gtk.Label(label=result[2], wrap=True,hexpand=True, xalign=1))
            group2.add(action_row)

        out = self.execute_terminal_command("ip -j address")
        data = json.loads(out)
        for line in data:
            group2 = Adw.PreferencesGroup(title=line['ifname'], margin_bottom=20)
            self.network_content.append(group2)
            for key, value in line.items():
                if isinstance(value, list) and len(value) > 1:
                    for element in value:
                        if isinstance(element, dict):
                            expander_row = Adw.ExpanderRow(title=key)
                            group2.add(expander_row)
                            for key2, value2 in element.items():
                                row = Adw.ActionRow(title=key2)
                                expander_row.add_row(row)
                                box = Gtk.Box(homogeneous=True, hexpand=True)
                                box.append(Gtk.Label(label=value2, xalign=1, wrap=True))
                                row.add_suffix(box)
                        else:
                            pass
                else:
                    box = Gtk.Box(homogeneous=True, hexpand=True)
                    box.append(Gtk.Label(label=value, xalign=1, wrap=True))
                    # box.append(Gtk.Label(label=""))
                    row = Adw.ActionRow(title=key)
                    row.add_suffix(box)
                    group2.add(row)


    def f(self,*data):
        if self.d.get_title_visible():
            self.c.set_reveal(True)
        else:
            self.c.set_reveal(False)

    def execute_terminal_command(self, command):
        console_permissions = ""
        console_permissions = "flatpak-spawn --host"
        txt = console_permissions + " " + command
        process = subprocess.Popen(txt, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=True)
        #outputs = []

        try:
            stdout, stderr = process.communicate()

            # outputs.append((True, stdout.decode()))
            out = stdout.decode()
        except Exception as e:
            pass

        return out #outputs[0]

