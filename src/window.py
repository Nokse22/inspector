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

class CommandTestWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'CommandTestWindow'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_default_size(1000, 700)
        self.set_title("Inspector")

        self.disks_content = Adw.PreferencesPage(title="Disk", icon_name="drive-harddisk-symbolic")
        self.add(self.disks_content)

        self.memory_content = Adw.PreferencesPage(title="Memory", icon_name="drive-harddisk-solidstate-symbolic")
        self.add(self.memory_content)

        self.pci_content = Adw.PreferencesPage(title="PCI", icon_name="drive-optical-symbolic")
        self.add(self.pci_content)

        self.usb_content = Adw.PreferencesPage(title="Usb", icon_name="drive-harddisk-usb-symbolic")
        self.add(self.usb_content)

        self.network_content = Adw.PreferencesPage(title="Network", icon_name="network-transmit-receive-symbolic")
        self.add(self.network_content)

        self.hardware_content = Adw.PreferencesPage(title="Hardware", icon_name="video-display-symbolic")
        self.add(self.hardware_content)

        # self.d.connect("notify::title-visible",self.f)

        out = self.execute_terminal_command("lsblk -J")
        data = json.loads(out)
        for device in data["blockdevices"]:
            text = f"Name: {device['name']}, Size: {device['size']}"
            group = Adw.PreferencesGroup(title=device['name'])
            self.disks_content.add(group)

            row = Adw.ActionRow(title="Total size")
            row.add_suffix(Gtk.Label(label=device['size'], wrap=True))
            group.add(row)

            group = Adw.PreferencesGroup()
            self.disks_content.add(group)

            if "children" in device:
                for partition in device["children"]:
                    row = Adw.ActionRow(title=partition['name'], subtitle=partition['mountpoints'][0])
                    row.add_suffix(Gtk.Label(label=partition['size'], wrap=True, xalign=1))
                    group.add(row)

        out = self.execute_terminal_command("lshw -json -c storage")  # "ip -j address")
        data = json.loads(out)
        for line in data:
            group2 = Adw.PreferencesGroup(title=line['description'], margin_top=20) #
            self.disks_content.add(group2)
            for key, value in line.items():
                if isinstance(value, dict):
                    expander_row = Adw.ExpanderRow(title=key)
                    group2.add(expander_row)
                    for key2, value2 in value.items():
                        row = Adw.ActionRow(title=key2)
                        expander_row.add_row(row)
                        box = Gtk.Box(homogeneous=True, hexpand=True)
                        box.append(Gtk.Label(label=value2, xalign=1, wrap=True))
                        row.add_suffix(box)
                elif key not in ["id", "class", "description"]:
                    row = Adw.ActionRow(title=key)
                    row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True))
                    group2.add(row)


        out = self.execute_terminal_command("lsmem -J")
        data = json.loads(out)
        group2 = Adw.PreferencesGroup(title="Ranges")
        self.memory_content.add(group2)
        total = 0
        for device in data["memory"]:
            total += float(re.sub('\D', '', device['size']))
            text = "range " + device['block']
            box = Gtk.Box(homogeneous=True, hexpand=True, width_request=150)
            box.append(Gtk.Label(label=device['size'], wrap=True, xalign=1))
            box.append(Gtk.Label(label=device['block'], wrap=True, xalign=1))
            row = Adw.ActionRow(title="Memory", subtitle=device['range'])
            row.add_suffix(box)
            group2.add(row)
        group2 = Adw.PreferencesGroup()
        self.memory_content.add(group2)
        text = "range " + device['block']
        label = Gtk.Label(label=str(total)+"G", wrap=True)
        row = Adw.ActionRow(title="Total")
        row.add_suffix(label)
        group2.add(row)

        out = self.execute_terminal_command("lspci")
        out = out.splitlines()
        text = "range "
        pattern = r'(\S+)\s(.*?):\s(.*)'
        group2 = Adw.PreferencesGroup(title="PCIs", margin_bottom=20)
        self.pci_content.add(group2)
        for line in out:
            match = re.match(pattern, line)
            if match:
                first_part = match.group(1)
                second_part = match.group(2)
                third_part = match.group(3)

                action_row = Adw.ActionRow(title=third_part, subtitle=second_part)
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
            self.usb_content.add(group2)

            name, value = result[1].split(' ', 1)
            action_row = Adw.ActionRow(title=name)
            action_row.add_suffix(Gtk.Label(label=value, xalign=1))
            group2.add(action_row)

            action_row = Adw.ActionRow(title="Name")
            action_row.add_suffix(Gtk.Label(label=result[2], wrap=True,hexpand=True, xalign=1))
            group2.add(action_row)

        out = self.execute_terminal_command("lshw -json -c network")  # "ip -j address")
        data = json.loads(out)
        for line in data:
            group2 = Adw.PreferencesGroup(title=line['description'], margin_bottom=20) #
            self.network_content.add(group2)
            for key, value in line.items():
                if isinstance(value, dict):
                    expander_row = Adw.ExpanderRow(title=key)
                    group2.add(expander_row)
                    for key2, value2 in value.items():
                        row = Adw.ActionRow(title=key2)
                        expander_row.add_row(row)
                        box = Gtk.Box(homogeneous=True, hexpand=True)
                        box.append(Gtk.Label(label=value2, xalign=1, wrap=True))
                        row.add_suffix(box)
                elif key not in ["ifname","ifindex", "addr_info", "id", "class", "description"]:
                    row = Adw.ActionRow(title=key)
                    row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True))
                    group2.add(row)

        out = self.execute_terminal_command("lshw -json -c cpu")  # "ip -j address")
        data = json.loads(out)
        for line in data:
            group2 = Adw.PreferencesGroup(title="CPU", margin_top=20) #
            self.hardware_content.add(group2)
            for key, value in line.items():
                if isinstance(value, dict):
                    expander_row = Adw.ExpanderRow(title=key)
                    group2.add(expander_row)
                    for key2, value2 in value.items():
                        row = Adw.ActionRow(title=key2)
                        expander_row.add_row(row)
                        box = Gtk.Box(homogeneous=True, hexpand=True)
                        box.append(Gtk.Label(label=value2, xalign=1, wrap=True))
                        row.add_suffix(box)
                elif key not in ["id", "class", "description"]:
                    row = Adw.ActionRow(title=key)
                    row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True))
                    group2.add(row)

        out = self.execute_terminal_command("lshw -json -c display")  # "ip -j address")
        data = json.loads(out)
        for line in data:
            group2 = Adw.PreferencesGroup(title="Display", margin_top=20) #
            self.hardware_content.add(group2)
            for key, value in line.items():
                if isinstance(value, dict):
                    expander_row = Adw.ExpanderRow(title=key)
                    group2.add(expander_row)
                    for key2, value2 in value.items():
                        row = Adw.ActionRow(title=key2)
                        expander_row.add_row(row)
                        box = Gtk.Box(homogeneous=True, hexpand=True)
                        box.append(Gtk.Label(label=value2, xalign=1, wrap=True))
                        row.add_suffix(box)
                elif key not in ["id", "class", "description"]:
                    row = Adw.ActionRow(title=key)
                    row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True))
                    group2.add(row)

        out = self.execute_terminal_command("lshw -json -c input")  # "ip -j address")
        data = json.loads(out)
        for line in data:
            group2 = Adw.PreferencesGroup(title=line['id'], margin_top=20) #
            self.hardware_content.add(group2)
            for key, value in line.items():
                if isinstance(value, dict):
                    expander_row = Adw.ExpanderRow(title=key)
                    group2.add(expander_row)
                    for key2, value2 in value.items():
                        row = Adw.ActionRow(title=key2)
                        expander_row.add_row(row)
                        box = Gtk.Box(homogeneous=True, hexpand=True)
                        box.append(Gtk.Label(label=value2, xalign=1, wrap=True))
                        row.add_suffix(box)
                elif isinstance(value, list):
                    expander_row = Adw.ExpanderRow(title=key)
                    group2.add(expander_row)
                    for val in value:
                        row = Adw.ActionRow(title=val)
                        expander_row.add_row(row)
                        row.add_suffix(Gtk.Label(label="", xalign=1, wrap=True))
                elif key not in ["id"]:
                    row = Adw.ActionRow(title=key)
                    row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True))
                    group2.add(row)

        out = self.execute_terminal_command("lshw -json -c bus")  # "ip -j address")
        data = json.loads(out)
        for line in data:
            group2 = Adw.PreferencesGroup(title=line['description'], margin_top=20) #
            self.hardware_content.add(group2)
            for key, value in line.items():
                if isinstance(value, dict):
                    expander_row = Adw.ExpanderRow(title=key)
                    group2.add(expander_row)
                    for key2, value2 in value.items():
                        row = Adw.ActionRow(title=key2)
                        expander_row.add_row(row)
                        box = Gtk.Box(homogeneous=True, hexpand=True)
                        box.append(Gtk.Label(label=value2, xalign=1, wrap=True))
                        row.add_suffix(box)
                elif isinstance(value, list):
                    expander_row = Adw.ExpanderRow(title=key)
                    group2.add(expander_row)
                    for val in value:
                        row = Adw.ActionRow(title=val)
                        expander_row.add_row(row)
                        row.add_suffix(Gtk.Label(label="", xalign=1, wrap=True))
                elif key not in ["id"]:
                    row = Adw.ActionRow(title=key)
                    row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True))
                    group2.add(row)


        out = self.execute_terminal_command("lshw -json -c system")
        data = json.loads(out)
        for line in data:
            group2 = Adw.PreferencesGroup(title="System", margin_top=20) #
            self.hardware_content.add(group2)
            for key, value in line.items():
                if isinstance(value, dict):
                    expander_row = Adw.ExpanderRow(title=key)
                    group2.add(expander_row)
                    for key2, value2 in value.items():
                        row = Adw.ActionRow(title=key2)
                        expander_row.add_row(row)
                        box = Gtk.Box(homogeneous=True, hexpand=True)
                        box.append(Gtk.Label(label=value2, xalign=1, wrap=True))
                        row.add_suffix(box)
                elif isinstance(value, list):
                    expander_row = Adw.ExpanderRow(title=key)
                    group2.add(expander_row)
                    for val in value:
                        row = Adw.ActionRow(title=val)
                        expander_row.add_row(row)
                        row.add_suffix(Gtk.Label(label="", xalign=1, wrap=True))
                elif key not in [""]:
                    row = Adw.ActionRow(title=key)
                    row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True))
                    group2.add(row)

    def execute_terminal_command(self, command):
        console_permissions = "flatpak-spawn --host"
        txt = console_permissions + " " + command
        process = subprocess.Popen(txt, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=True)
        try:
            stdout, stderr = process.communicate()
            out = stdout.decode()
        except Exception as e:
            pass
        return out

