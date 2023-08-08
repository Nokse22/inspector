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
from gi.repository import Gio
import gi, os, subprocess, threading, time, json, re

class CommandTestWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'CommandTestWindow'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = Gio.Settings.new('io.github.nokse22.inspector')

        # self.set_default_size(600, 820)
        self.settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)

        self.set_title("Inspector")
        self.set_modal(False)
        # hd = self.get_content().get_child().get_visible_child().get_last_child().get_last_child().get_last_child().get_last_child().get_prev_sibling().get_child().get_child().get_first_child()

        hd = self.get_content().get_child().get_visible_child().get_first_child() #.get_child().get_child().get_last_child().get_prev_sibling().get_child().get_child().get_first_child()
        # print(hd)

        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        menu.append(_("Reload"), "app.reload")
        menu.append(_("Keyboard shortcuts"), "win.show-help-overlay")
        menu.append(_("About"), "app.about")

        menu_button.set_menu_model(menu)

        #hd.pack_start(menu_button)
        about_button = Gtk.Button(icon_name="help-about-symbolic", valign=3, action_name='app.about')
        hd.pack_start(about_button)

        self.usb_content = Adw.PreferencesPage(title="Usb", icon_name="media-removable-symbolic")
        self.usb_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.usb_content)

        self.disks_content = Adw.PreferencesPage(title="Disk", icon_name="drive-harddisk-symbolic")
        self.disks_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.disks_content)

        self.memory_content = Adw.PreferencesPage(title="Memory", icon_name="drive-harddisk-solidstate-symbolic")
        self.memory_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.memory_content)

        self.pci_content = Adw.PreferencesPage(title="PCI", icon_name="drive-optical-symbolic")
        self.pci_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.pci_content)

        self.network_content = Adw.PreferencesPage(title="Network", icon_name="network-transmit-receive-symbolic")
        self.network_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.network_content)

        self.hardware_content = Adw.PreferencesPage(title="CPU", icon_name="system-run-symbolic")
        self.hardware_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.hardware_content)

        self.system_content = Adw.PreferencesPage(title="System", icon_name="preferences-desktop-display-symbolic")
        self.system_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.system_content)

        self.disk_page_children = []
        self.memory_page_children = []
        self.pci_page_children = []
        self.usb_page_children = []
        self.network_page_children = []
        self.hardware_page_children = []
        self.system_page_children = []

        self.update_disk_page()
        self.update_memory_page()
        self.update_pci_page()
        self.update_usb_page()
        self.update_network_page()
        self.update_hardware_page()
        self.update_system_page()

    def execute_terminal_command(self, command):
        if 'SNAP' not in os.environ:
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

    def empty_command_page(self, command):
        group = Adw.PreferencesGroup()
        empty_command_status_page = Adw.StatusPage(title="The command is not supported",
                icon_name="computer-fail-symbolic", hexpand=True, vexpand=True,
                description="The command " + command + " returned empty. \n Try running it on your terminal, it should prompt you to install the package on your system.")
        group.add(empty_command_status_page)
        return group

    def update_system_page(self, btn=None):
        for child in self.system_page_children:
            self.system_content.remove(child)
        self.system_page_children = []
        out = self.execute_terminal_command("uname -a")
        if out == "":
            page = self.empty_command_page("uname")
            self.system_content.add(page)
            self.system_page_children.append(page)
            return
        group = Adw.PreferencesGroup(title="System", description="command: uname")
        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
        refresh_button.connect("clicked", self.update_system_page)
        group.set_header_suffix(refresh_button)
        self.system_content.add(group)
        self.system_page_children.append(group)

        out = self.execute_terminal_command("uname -s")
        row = Adw.ActionRow(title="Kernel Name")
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -n")
        row = Adw.ActionRow(title="Network Node Hostname")
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -r")
        row = Adw.ActionRow(title="Kernel Release")
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -v")
        row = Adw.ActionRow(title="Kernel Version")
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -m")
        row = Adw.ActionRow(title="Machine Hardware Name")
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -p")
        row = Adw.ActionRow(title="Processor Type")
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -i")
        row = Adw.ActionRow(title="hardware platform")
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -o")
        row = Adw.ActionRow(title="Operating System")
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        # cat /etc/os-release

        group = Adw.PreferencesGroup(title="Distro", description="command: cat /etc/os-release")
        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
        refresh_button.connect("clicked", self.update_system_page)
        group.set_header_suffix(refresh_button)
        self.system_content.add(group)
        self.system_page_children.append(group)

        out = self.execute_terminal_command("cat /etc/os-release")
        out = out.splitlines()

        for line in out:
            key, value = line.split('=')
            key = key.replace('_', ' ').title()
            row = Adw.ActionRow(title=key)
            if "Url" in key:
                link = Gtk.LinkButton(uri=value.replace('"', ''), label=value.replace('"', ''), hexpand=True)
                label = link.get_child()
                label.set_wrap(True)
                label.set_xalign(1)
                label.set_justify(1)
                row.add_suffix(link)
            else:
                row.add_suffix(Gtk.Label(label=value.replace('"', ''), wrap=True, hexpand=True, xalign=1, justify=1))
            group.add(row)



    def update_disk_page(self, btn=None):
        for child in self.disk_page_children:
            self.disks_content.remove(child)
        self.disk_page_children = []
        out = self.execute_terminal_command("lsblk -J")
        if out == "":
            page = self.empty_command_page("lsblk")
            self.disks_content.add(page)
            self.disk_page_children.append(page)
        else:
            data = json.loads(out)
            for device in data["blockdevices"]:
                text = f"Name: {device['name']}, Size: {device['size']}"
                group = Adw.PreferencesGroup(title=device['name'], description="command: lsblk")
                refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
                refresh_button.connect("clicked", self.update_disk_page)
                group.set_header_suffix(refresh_button)
                self.disks_content.add(group)
                self.disk_page_children.append(group)
                row = Adw.ActionRow(title="Total size")
                row.add_suffix(Gtk.Label(label=device['size'], wrap=True))
                group.add(row)
                if "children" in device:
                    group = Adw.PreferencesGroup()
                    self.disks_content.add(group)
                    self.disk_page_children.append(group)
                    for partition in device["children"]:
                        row = Adw.ActionRow(title=partition['name'], subtitle=partition['mountpoints'][0])
                        row.add_suffix(Gtk.Label(label=partition['size'], wrap=True, xalign=1))
                        group.add(row)

            # out = self.execute_terminal_command("lshw -json -c storage")
            # if out != "":
            #     data = json.loads(out)
            #     for line in data:
            #         group2 = Adw.PreferencesGroup(title=line['description'], description="command: lshw -c storage")
            #         refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
            #         refresh_button.connect("clicked", self.update_disk_page)
            #         group2.set_header_suffix(refresh_button)
            #         self.disks_content.add(group2)
            #         self.disk_page_children.append(group2)
            #         for key, value in line.items():
            #             if isinstance(value, dict):
            #                 expander_row = Adw.ExpanderRow(title=key)
            #                 group2.add(expander_row)
            #                 for key2, value2 in value.items():
            #                     row = Adw.ActionRow(title=key2[0].upper() + key2[1:])
            #                     expander_row.add_row(row)
            #                     box = Gtk.Box(homogeneous=True, hexpand=True)
            #                     box.append(Gtk.Label(label=value2, xalign=1, wrap=True, justify=1))
            #                     row.add_suffix(box)
            #             elif key not in ["id", "class", "description"]:
            #                 row = Adw.ActionRow(title=key[0].upper() + key[1:])
            #                 row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True, justify=1))
            #                 group2.add(row)

    def update_memory_page(self, btn=None):
        for child in self.memory_page_children:
            self.memory_content.remove(child)
        self.memory_page_children = []
        out = self.execute_terminal_command("lsmem -J")
        if out == "":
            page = self.empty_command_page("lsmem")
            self.memory_content.add(page)
            self.memory_page_children.append(page)
        else:
            data = json.loads(out)
            group2 = Adw.PreferencesGroup(title="Ranges", description="command: lsmem")
            refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
            refresh_button.connect("clicked", self.update_memory_page)
            group2.set_header_suffix(refresh_button)
            self.memory_content.add(group2)
            self.memory_page_children.append(group2)
            # total = 0
            for device in data["memory"]:
                # total += float(re.sub('\D', '', device['size']))
                text = "range " + device['block']
                box = Gtk.Box(homogeneous=True, hexpand=True, width_request=150)
                box.append(Gtk.Label(label=device['size'], wrap=True, xalign=1))
                box.append(Gtk.Label(label=device['block'], wrap=True, xalign=1))
                row = Adw.ActionRow(title="Memory", subtitle=device['range'])
                row.add_suffix(box)
                group2.add(row)
            text = "range " + device['block']

            # out = self.execute_terminal_command("lshw -json -c memory")
            # if out != "":
            #     data = json.loads(out)
            #     for line in data:
            #         group2 = Adw.PreferencesGroup(title=line['description'], description="command: lshw -c memory") #
            #         refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
            #         refresh_button.connect("clicked", self.update_memory_page)
            #         group2.set_header_suffix(refresh_button)
            #         self.memory_content.add(group2)
            #         self.memory_page_children.append(group2)
            #         for key, value in line.items():
            #             if isinstance(value, dict):
            #                 expander_row = Adw.ExpanderRow(title=key)
            #                 group2.add(expander_row)
            #                 for key2, value2 in value.items():
            #                     row = Adw.ActionRow(title=key2[0].upper() + key2[1:])
            #                     expander_row.add_row(row)
            #                     box = Gtk.Box(homogeneous=True, hexpand=True)
            #                     box.append(Gtk.Label(label=value2, xalign=1, wrap=True, justify=1))
            #                     row.add_suffix(box)
            #             elif key == "size":
            #                 row = Adw.ActionRow(title=key[0].upper() + key[1:])
            #                 row.add_suffix(Gtk.Label(label=str(round(float(value)/(1024 ** 3), 2)) + " Gb", xalign=1, wrap=True, hexpand=True, justify=1))
            #                 group2.add(row)
            #             elif key not in ["id", "class", "description"]:
            #                 row = Adw.ActionRow(title=key[0].upper() + key[1:])
            #                 row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True, justify=1))
            #                 group2.add(row)

    def update_pci_page(self, btn=None):
        for child in self.pci_page_children:
            self.pci_content.remove(child)
        self.pci_page_children = []
        out = self.execute_terminal_command("lspci")
        if out == "":
            page = self.empty_command_page("lspci")
            self.pci_content.add(page)
            self.pci_page_children.append(page)
        else:
            out = out.splitlines()
            text = "range "
            pattern = r'(\S+)\s(.*?):\s(.*)'
            group2 = Adw.PreferencesGroup(title="PCIs", description="command: lspci")
            refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
            refresh_button.connect("clicked", self.update_pci_page)
            group2.set_header_suffix(refresh_button)
            self.pci_content.add(group2)
            self.pci_page_children.append(group2)
            for line in out:
                match = re.match(pattern, line)
                if match:
                    first_part = match.group(1)
                    second_part = match.group(2)
                    third_part = match.group(3)

                    action_row = Adw.ActionRow(title=third_part, subtitle=second_part)
                    group2.add(action_row)

    def update_usb_page(self, btn=None):
        for child in self.usb_page_children:
            self.usb_content.remove(child)
        self.usb_page_children = []
        out = self.execute_terminal_command("lsusb")
        if out == "":
            page = self.empty_command_page("lsusb")
            self.usb_content.add(page)
            self.usb_page_children.append(page)
        else:
            out = out.splitlines()
            group2 = Adw.PreferencesGroup(title="Usb", description="command: lsusb")
            refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
            refresh_button.connect("clicked", self.update_usb_page)
            group2.set_header_suffix(refresh_button)
            self.usb_content.add(group2)
            self.usb_page_children.append(group2)
            for line in out:
                result = []
                parts = line.split(' ')
                bus_device = ' '.join(parts[:4]).replace(':', '')
                identifier = ' '.join(parts[4:6])
                vendor_product = ' '.join(parts[6:])
                result.append(bus_device)
                result.append(identifier)
                result.append(vendor_product)

                name, value = result[1].split(' ', 1)

                expander_row = Adw.ExpanderRow(title=result[2])
                group2.add(expander_row)

                action_row = Adw.ActionRow(title=name)
                action_row.add_suffix(Gtk.Label(label=value, xalign=1, justify=1))
                expander_row.add_row(action_row)

                action_row = Adw.ActionRow(title="Bus")
                action_row.add_suffix(Gtk.Label(label=result[0], wrap=True,hexpand=True, xalign=1, justify=1))
                expander_row.add_row(action_row)

    def update_network_page(self, btn=None):
        for child in self.network_page_children:
            self.network_content.remove(child)
        self.network_page_children = []
        out = self.execute_terminal_command("ip -j address")
        if out == "":
            page = self.empty_command_page("ip address")
            self.network_content.add(page)
            self.network_page_children.append(page)
        else:
            data = json.loads(out)
            for line in data:
                group2 = Adw.PreferencesGroup(title=line['ifname'], description="command: ip address", margin_bottom=20)
                refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
                refresh_button.connect("clicked", self.update_network_page)
                group2.set_header_suffix(refresh_button)
                self.network_content.add(group2)
                self.network_page_children.append(group2)
                for key, value in line.items():

                    if isinstance(value, list):
                        for val in value:
                            if isinstance(val, dict):
                                if key == "addr_info":
                                    expander_row = Adw.ExpanderRow(title="Address info, ip")
                                else:
                                    expander_row = Adw.ExpanderRow(title=key[0].upper() + key[1:])
                                group2.add(expander_row)
                                for key2, value2 in val.items():
                                    row = Adw.ActionRow(title=key2[0].upper() + key2[1:])
                                    expander_row.add_row(row)
                                    box = Gtk.Box(homogeneous=True, hexpand=True)
                                    box.append(Gtk.Label(label=value2, xalign=1, wrap=True, justify=1))
                                    row.add_suffix(box)
                        try:
                            value[0]
                        except:
                            pass
                        else:
                            if not isinstance(value[0], dict):
                                expander_row = Adw.ExpanderRow(title=key[0].upper() + key[1:])
                                group2.add(expander_row)
                                text = ""
                                for val in value:
                                    text += val + ", "
                                row = Adw.ActionRow(title=text)#val[0].upper() + val[1:])
                                expander_row.add_row(row)
                            # box = Gtk.Box(homogeneous=True, hexpand=True)
                            # box.append(Gtk.Label(label=value2, xalign=1, wrap=True, justify=1))
                            # row.add_suffix(box)
                    elif key not in ["ifname","ifindex", "addr_info"]:
                        row = Adw.ActionRow(title=key[0].upper() + key[1:] )
                        row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True, justify=1))
                        group2.add(row)

        # for child in self.network_page_children:
        #     self.network_content.remove(child)
        # self.network_page_children = []
        # out = self.execute_terminal_command("lshw -json -c network")
        # if out == "":
        #     page = self.empty_command_page("lshw -c network")
        #     self.network_content.add(page)
        #     self.network_page_children.append(page)
        # else:
        #     data = json.loads(out)
        #     for line in data:
        #         group2 = Adw.PreferencesGroup(title=line['description'], description="command: lshw -c network", margin_bottom=20)
        #         refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
        #         refresh_button.connect("clicked", self.update_network_page)
        #         group2.set_header_suffix(refresh_button)
        #         self.network_content.add(group2)
        #         self.network_page_children.append(group2)
        #         for key, value in line.items():
        #             if isinstance(value, dict):
        #                 expander_row = Adw.ExpanderRow(title=key[0].upper() + key[1:])
        #                 group2.add(expander_row)
        #                 for key2, value2 in value.items():
        #                     row = Adw.ActionRow(title=key2[0].upper() + key2[1:])
        #                     expander_row.add_row(row)
        #                     box = Gtk.Box(homogeneous=True, hexpand=True)
        #                     box.append(Gtk.Label(label=value2, xalign=1, wrap=True, justify=1))
        #                     row.add_suffix(box)
        #             elif key not in ["ifname","ifindex", "addr_info", "id", "class", "description"]:
        #                 row = Adw.ActionRow(title=key[0].upper() + key[1:] )
        #                 row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True, justify=1))
        #                 group2.add(row)

    def update_hardware_page(self, btn=None):
        for child in self.hardware_page_children:
            self.hardware_content.remove(child)
        self.hardware_page_children = []
        out = self.execute_terminal_command("lscpu -J")
        if out == "":
            page = self.empty_command_page("lscpu")
            self.hardware_content.add(page)
            self.hardware_page_children.append(page)
        else:
            data = json.loads(out)
            group2 = Adw.PreferencesGroup(title="CPU", description="command: lshw -c cpu")
            refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
            refresh_button.connect("clicked", self.update_hardware_page)
            group2.set_header_suffix(refresh_button)
            self.hardware_content.add(group2)
            self.hardware_page_children.append(group2)
            add_flags = False
            for line in data['lscpu']:
                row = Adw.ActionRow()
                for key, value in line.items():
                    if value == "Flags:":
                        row = Adw.ExpanderRow(title=value[0].upper() + value[1:])
                        group2.add(row)
                        add_flags = True
                    elif add_flags:
                        row2 = Adw.ActionRow(title=value)
                        row.add_row(row2)
                        add_flags = False
                    elif key == "field":
                        row = Adw.ActionRow(title=value[0].upper() + value[1:])
                    elif key == "data":
                        row.add_suffix(Gtk.Label(label=value[0].upper() + value[1:], xalign=1, wrap=True, hexpand=True, justify=1))
                        group2.add(row)
                    # if isinstance(value, dict):
                    #     expander_row = Adw.ExpanderRow(title=key[0].upper() + key[1:])
                    #     group2.add(expander_row)
                    #     for key2, value2 in value.items():
                    #         row = Adw.ActionRow(title=key2[0].upper() + key2[1:])
                    #         expander_row.add_row(row)
                    #         box = Gtk.Box(homogeneous=True, hexpand=True)
                    #         box.append(Gtk.Label(label=value2, xalign=1, wrap=True, justify=1))
                    #         row.add_suffix(box)
                    # elif key not in ["id", "class", "description"]:



        # for child in self.hardware_page_children:
        #     self.hardware_content.remove(child)
        # self.hardware_page_children = []
        # out = self.execute_terminal_command("lshw -json -c cpu")
        # if out == "":
        #     page = self.empty_command_page("lshw")
        #     self.hardware_content.add(page)
        #     self.hardware_page_children.append(page)
        # else:
        #     data = json.loads(out)
        #     for line in data:
        #         group2 = Adw.PreferencesGroup(title="CPU", description="command: lshw -c cpu")
        #         refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
        #         refresh_button.connect("clicked", self.update_hardware_page)
        #         group2.set_header_suffix(refresh_button)
        #         self.hardware_content.add(group2)
        #         self.hardware_page_children.append(group2)
        #         for key, value in line.items():
        #             if isinstance(value, dict):
        #                 expander_row = Adw.ExpanderRow(title=key[0].upper() + key[1:])
        #                 group2.add(expander_row)
        #                 for key2, value2 in value.items():
        #                     row = Adw.ActionRow(title=key2[0].upper() + key2[1:])
        #                     expander_row.add_row(row)
        #                     box = Gtk.Box(homogeneous=True, hexpand=True)
        #                     box.append(Gtk.Label(label=value2, xalign=1, wrap=True, justify=1))
        #                     row.add_suffix(box)
        #             elif key not in ["id", "class", "description"]:
        #                 row = Adw.ActionRow(title=key[0].upper() + key[1:])
        #                 row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True, justify=1))
        #                 group2.add(row)

        # out = self.execute_terminal_command("lshw -json -c display")
        # if out != "":
        #     data = json.loads(out)
        #     for line in data:
        #         group2 = Adw.PreferencesGroup(title="Display", description="command: lshw -c display")
        #         refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
        #         refresh_button.connect("clicked", self.update_hardware_page)
        #         group2.set_header_suffix(refresh_button)
        #         self.hardware_content.add(group2)
        #         self.hardware_page_children.append(group2)
        #         for key, value in line.items():
        #             if isinstance(value, dict):
        #                 expander_row = Adw.ExpanderRow(title=key[0].upper() + key[1:])
        #                 group2.add(expander_row)
        #                 for key2, value2 in value.items():
        #                     row = Adw.ActionRow(title=key2[0].upper() + key2[1:])
        #                     expander_row.add_row(row)
        #                     box = Gtk.Box(homogeneous=True, hexpand=True)
        #                     box.append(Gtk.Label(label=value2, xalign=1, wrap=True, justify=1))
        #                     row.add_suffix(box)
        #             elif key not in ["id", "class", "description"]:
        #                 row = Adw.ActionRow(title=key[0].upper() + key[1:])
        #                 row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True, justify=1))
        #                 group2.add(row)

        # out = self.execute_terminal_command("lshw -json -c input")
        # if out != "":
        #     data = json.loads(out)
        #     group2 = Adw.PreferencesGroup(title="Inputs", description="command: lshw -c input")
        #     refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
        #     refresh_button.connect("clicked", self.update_hardware_page)
        #     group2.set_header_suffix(refresh_button)
        #     self.hardware_content.add(group2)
        #     self.hardware_page_children.append(group2)
        #     for line in data:
        #         expander_row = Adw.ExpanderRow(title=line['product'])
                # expander_row.add_suffix(Gtk.Label(label=line['product'], xalign=1, wrap=True, hexpand=True, justify=1))
        #         group2.add(expander_row)
        #         for key, value in line.items():
        #             if key not in ["product", "class"]:
        #                 row = Adw.ActionRow(title=key[0].upper() + key[1:])
        #                 row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True, justify=1))
        #                 expander_row.add_row(row)
        #                 pass


        # out = self.execute_terminal_command("lshw -json -c bus")
        # if out != "":
        #     data = json.loads(out)
        #     for line in data:
        #         group2 = Adw.PreferencesGroup(title=line['description'], description="command: lshw -c bus")
        #         refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
        #         refresh_button.connect("clicked", self.update_hardware_page)
        #         group2.set_header_suffix(refresh_button)
        #         self.hardware_content.add(group2)
        #         self.hardware_page_children.append(group2)
        #         for key, value in line.items():
        #             if isinstance(value, dict):
        #                 expander_row = Adw.ExpanderRow(title=key[0].upper() + key[1:])
        #                 group2.add(expander_row)
        #                 for key2, value2 in value.items():
        #                     row = Adw.ActionRow(title=key2[0].upper() + key2[1:])
        #                     expander_row.add_row(row)
        #                     box = Gtk.Box(homogeneous=True, hexpand=True)
        #                     box.append(Gtk.Label(label=value2, xalign=1, wrap=True, justify=1))
        #                     row.add_suffix(box)
        #             elif isinstance(value, list):
        #                 expander_row = Adw.ExpanderRow(title=key)
        #                 group2.add(expander_row)
        #                 for val in value:
        #                     row = Adw.ActionRow(title=val)
        #                     expander_row.add_row(row)
        #                     row.add_suffix(Gtk.Label(label="", xalign=1, wrap=True, justify=1))
        #             elif key not in ["id"]:
        #                 row = Adw.ActionRow(title=key[0].upper() + key[1:])
        #                 row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True, justify=1))
        #                 group2.add(row)

        # out = self.execute_terminal_command("lshw -json -c system")
        # data = json.loads(out)
        # for line in data:
        #     group2 = Adw.PreferencesGroup(title="System") #
        #     self.hardware_content.add(group2)
        #     self.hardware_page_children.append(group2)
        #     for key, value in line.items():
        #         if isinstance(value, dict):
        #             expander_row = Adw.ExpanderRow(title=key)
        #             group2.add(expander_row)
        #             for key2, value2 in value.items():
        #                 row = Adw.ActionRow(title=key2)
        #                 expander_row.add_row(row)
        #                 box = Gtk.Box(homogeneous=True, hexpand=True)
        #                 box.append(Gtk.Label(label=value2, xalign=1, wrap=True))
        #                 row.add_suffix(box)
        #         elif isinstance(value, list):
        #             expander_row = Adw.ExpanderRow(title=key)
        #             group2.add(expander_row)
        #             for val in value:
        #                 row = Adw.ActionRow(title=val)
        #                 expander_row.add_row(row)
        #                 row.add_suffix(Gtk.Label(label="", xalign=1, wrap=True))
        #         elif key not in [""]:
        #             row = Adw.ActionRow(title=key)
        #             row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, hexpand=True))
        #             group2.add(row)
