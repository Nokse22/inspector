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

import gettext 
import gi, os, subprocess, threading, time, json, re, fnmatch

class CommandTestWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'CommandTestWindow'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = Gio.Settings.new('io.github.nokse22.inspector')

        # self.set_default_size(600, 820)
        self.settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)

        self.set_title(_("Inspector"))
        self.set_modal(False)
        # hd = self.get_content().get_child().get_visible_child().get_last_child().get_last_child().get_last_child().get_last_child().get_prev_sibling().get_child().get_child().get_first_child()

        hd = self.get_content().get_child().get_visible_child().get_first_child() #.get_child().get_child().get_last_child().get_prev_sibling().get_child().get_child().get_first_child()
        # print(hd)

        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        menu.append(_("Reload"), "app.reload")
        menu.append(_("Keyboard shortcuts"), "win.show-help-overlay")
        menu.append(_("About Inspector"), "app.about")

        menu_button.set_menu_model(menu)
        #hd.pack_start(menu_button)
        about_button = Gtk.Button(icon_name="help-about-symbolic", valign=3, action_name='app.about')
        about_button.set_tooltip_text(_("About Inspector"))
        hd.pack_start(about_button)

        self.usb_content = Adw.PreferencesPage(title=_("USB"), icon_name="media-removable-symbolic")
        self.usb_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.usb_content)

        self.disks_content = Adw.PreferencesPage(title=_("Disk"), icon_name="drive-harddisk-symbolic")
        self.disks_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.disks_content)

        self.memory_content = Adw.PreferencesPage(title=_("Memory"), icon_name="drive-harddisk-solidstate-symbolic")
        self.memory_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.memory_content)

        self.pci_content = Adw.PreferencesPage(title=_("PCI"), icon_name="drive-optical-symbolic")
        self.pci_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.pci_content)

        self.network_content = Adw.PreferencesPage(title=_("Network"), icon_name="network-transmit-receive-symbolic")
        self.network_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.network_content)

        self.hardware_content = Adw.PreferencesPage(title=_("CPU"), icon_name="system-run-symbolic")
        self.hardware_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.hardware_content)

        self.motherboard_content = Adw.PreferencesPage(title=_("Motherboard"), icon_name="video-display-symbolic")
        self.motherboard_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.motherboard_content)

        self.system_content = Adw.PreferencesPage(title=_("System"), icon_name="preferences-desktop-remote-desktop-symbolic")
        self.system_content.get_first_child().get_first_child().get_first_child().set_maximum_size(800)
        self.add(self.system_content)

        self.disk_page_children = []
        self.memory_page_children = []
        self.pci_page_children = []
        self.usb_page_children = []
        self.network_page_children = []
        self.hardware_page_children = []
        self.motherboard_page_children = []
        self.system_page_children = []

        self.update_disk_page()
        self.update_memory_page()
        self.update_pci_page()
        self.update_usb_page()
        self.update_network_page()
        self.update_motherboard_page()
        self.update_hardware_page()
        self.update_system_page()

    def execute_terminal_command(self, command):
        if 'FLATPAK_ID' in os.environ:
            console_permissions = "flatpak-spawn --host "
        else:
            console_permissions = ""
        txt = console_permissions + command
        print(txt)
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
        empty_command_status_page = Adw.StatusPage(title=_("The command is not supported"),
                icon_name="computer-fail-symbolic", hexpand=True, vexpand=True,
                description=_("The command {0} returned empty.\n"
                              "Try running it on your terminal, it should prompt you to "
                              "install the package on your system.").format(command))
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
        group = Adw.PreferencesGroup(title=_("System"), description=_("command: uname"))
        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
        refresh_button.connect("clicked", self.update_system_page)
        group.set_header_suffix(refresh_button)
        self.system_content.add(group)
        self.system_page_children.append(group)

        out = self.execute_terminal_command("uname -s")
        row = Adw.ActionRow(title=_("Kernel Name"))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -n")
        row = Adw.ActionRow(title=_("Network Node Hostname"))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -r")
        row = Adw.ActionRow(title=_("Kernel Release"))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -v")
        row = Adw.ActionRow(title=_("Kernel Version"))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -m")
        row = Adw.ActionRow(title=_("Machine Hardware Name"))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -p")
        row = Adw.ActionRow(title=_("Processor Type"))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -i")
        row = Adw.ActionRow(title=_("Hardware Platform"))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        out = self.execute_terminal_command("uname -o")
        row = Adw.ActionRow(title=_("Operating System"))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
        group.add(row)

        # cat /etc/os-release

        group = Adw.PreferencesGroup(title=_("Distro"), description=_("command: cat /etc/os-release"))
        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
        refresh_button.connect("clicked", self.update_system_page)
        group.set_header_suffix(refresh_button)
        self.system_content.add(group)
        self.system_page_children.append(group)
        
        if 'SNAP' in os.environ:
            out = self.execute_terminal_command("cat /var/lib/snapd/hostfs/etc/os-release")
        else:
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
                row.add_suffix(Gtk.Label(label=value.replace('"', ''), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
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
            loop_group = None
            data = json.loads(out)
            try:
                devices = data["blockdevices"]
            except:
                devices = []
            for device in devices:
                try:
                    name = device['name']
                except:
                    name = "N/A"
                if not fnmatch.fnmatch(name, 'loop*'):
                    try:
                        size = device['size']
                    except:
                        size = ""
                    text = f"Name: {name}, Size: {size}"
                    group = Adw.PreferencesGroup(title=name, description=_("command: lsblk"))
                    refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
                    refresh_button.set_tooltip_text(_("Refresh"))
                    refresh_button.connect("clicked", self.update_disk_page)
                    group.set_header_suffix(refresh_button)
                    self.disks_content.add(group)
                    self.disk_page_children.append(group)
                    expander_row = Adw.ExpanderRow(title=_("Total size: "+size))
                    group.add(expander_row)
                else:
                    if loop_group == None:
                        loop_count = self.execute_terminal_command("lsblk -d | grep loop | wc -l")
                        loop_group = Adw.PreferencesGroup(title=_("Loop devices"), description=_("command: lsblk"))
                        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
                        refresh_button.set_tooltip_text(_("Refresh"))
                        refresh_button.connect("clicked", self.update_disk_page)
                        loop_group.set_header_suffix(refresh_button)
                        self.disks_content.add(loop_group)
                        self.disk_page_children.append(loop_group)
                        loop_expander_row = Adw.ExpanderRow(title=gettext.ngettext("Device Count: %s", "Devices Count: %s", loop_count) % loop_count.rstrip())
                        loop_group.add(loop_expander_row)
                    try:
                        subtitle = device['mountpoints'][0]
                    except:
                        try:
                            subtitle = device['mountpoint']
                        except:
                            subtitle = ""
                    row = Adw.ActionRow(title=name, subtitle=subtitle)
                    try:
                        size = device['size']
                    except:
                        size = "N/A"
                    row.add_suffix(Gtk.Label(label=size, wrap=True, selectable=True))
                    loop_expander_row.add_row(row)
                if "children" in device:
                    group = Adw.PreferencesGroup()
                    self.disks_content.add(group)
                    self.disk_page_children.append(group)
                    try:
                        partitions = device["children"]
                    except:
                        partitions = []
                    for partition in partitions:
                        try:
                            subtitle = partition['mountpoints'][0]
                            if subtitle and fnmatch.fnmatch(subtitle, "*snap*"):
                                subtitle = '/'
                        except:
                            try:
                                subtitle = partition['mountpoint']
                            except:
                                subtitle = ""
                        try:
                            name = partition['name']
                        except:
                            name = "Name"
                        row = Adw.ActionRow(title=name, subtitle=subtitle)
                        try:
                            size = partition['size']
                        except:
                            size = "N/A"
                        row.add_suffix(Gtk.Label(label=size, wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1))
                        expander_row.add_row(row)


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
            group2 = Adw.PreferencesGroup(title=_("Ranges"), description=_("command: lsmem"))
            refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
            refresh_button.set_tooltip_text(_("Refresh"))
            refresh_button.connect("clicked", self.update_memory_page)
            group2.set_header_suffix(refresh_button)
            self.memory_content.add(group2)
            self.memory_page_children.append(group2)
            # total = 0
            try:
                memory = data["memory"]
            except:
                memory = []
            for device in memory:
                try:
                    block = device['block']
                except:
                    block = ""
                try:
                    size = device['size']
                except:
                    size = ""
                try:
                    range_ = device['range']
                except:
                    range_ = ""
                text = "range " + block
                box = Gtk.Box(homogeneous=True, hexpand=True, width_request=150)
                box.append(Gtk.Label(label=size, wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1))
                box.append(Gtk.Label(label=block, wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1))
                row = Adw.ActionRow(title=_("Memory"), subtitle=range_)
                row.add_suffix(box)
                group2.add(row)

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
            group2 = Adw.PreferencesGroup(title=_("PCIs"), description=_("command: lspci"))
            refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
            refresh_button.set_tooltip_text(_("Refresh"))
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
            group2 = Adw.PreferencesGroup(title=_("USB"), description=_("command: lsusb"))
            refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
            refresh_button.set_tooltip_text(_("Refresh"))
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
                action_row.add_suffix(Gtk.Label(label=value, xalign=1, justify=1, selectable=True))
                expander_row.add_row(action_row)

                action_row = Adw.ActionRow(title=_("Bus"))
                action_row.add_suffix(Gtk.Label(label=result[0], wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
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
                try:
                    name = line['ifname']
                except:
                    name = "N/A"
                group2 = Adw.PreferencesGroup(title=name, description=_("command: ip address"), margin_bottom=20)
                refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
                refresh_button.set_tooltip_text(_("Refresh"))
                refresh_button.connect("clicked", self.update_network_page)
                group2.set_header_suffix(refresh_button)
                self.network_content.add(group2)
                self.network_page_children.append(group2)
                for key, value in line.items():

                    if isinstance(value, list):
                        for val in value:
                            if isinstance(val, dict):
                                if key == "addr_info":
                                    expander_row = Adw.ExpanderRow(title=_("Address info, ip"))
                                else:
                                    expander_row = Adw.ExpanderRow(title=key[0].upper() + key[1:])
                                group2.add(expander_row)
                                for key2, value2 in val.items():
                                    row = Adw.ActionRow(title=key2[0].upper() + key2[1:])
                                    expander_row.add_row(row)
                                    box = Gtk.Box(homogeneous=True, hexpand=True)
                                    box.append(Gtk.Label(label=value2, xalign=1, wrap=True, wrap_mode=1, selectable=True, hexpand=True, justify=1))
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
                                row = Adw.ActionRow(title=text)
                                expander_row.add_row(row)
                    elif key not in ["ifname","ifindex", "addr_info"]:
                        row = Adw.ActionRow(title=key[0].upper() + key[1:] )
                        row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, wrap_mode=1, selectable=True, hexpand=True, justify=1))
                        group2.add(row)

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
            group2 = Adw.PreferencesGroup(title=_("CPU"), description=_("command: lshw -c cpu"))
            refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
            refresh_button.set_tooltip_text(_("Refresh"))
            refresh_button.connect("clicked", self.update_hardware_page)
            group2.set_header_suffix(refresh_button)
            self.hardware_content.add(group2)
            self.hardware_page_children.append(group2)
            add_flags = False
            try:
                lines = data['lscpu']
            except:
                lines = []
            for line in lines:
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
                        row.add_suffix(Gtk.Label(label=value[0].upper() + value[1:], xalign=1, wrap=True, wrap_mode=1, selectable=True, hexpand=True, justify=1))
                        group2.add(row)

    def update_motherboard_page(self, btn=None):
        # Clear the previous content
        for child in self.motherboard_page_children:
            self.motherboard_content.remove(child)
        self.motherboard_page_children = []
        
        dmi_path = "/sys/devices/virtual/dmi/id/"
        dmi_keys = [
            ("bios_date", _("BIOS Date")),
            ("bios_release", _("BIOS Release")),
            ("bios_vendor", _("BIOS Vendor")),
            ("bios_version", _("BIOS Version")),
            ("board_asset_tag", _("Board Asset Tag")),
            ("board_name", _("Board Name")),
            ("board_serial", _("Board Serial Number")),
            ("board_vendor", _("Board Vendor")),
            ("board_version", _("Board Version")),
            ("chassis_asset_tag", _("Chassis Asset Tag")),
            ("chassis_serial", _("Chassis Serial Number")),
            ("chassis_type", _("Chassis Type")),
            ("chassis_vendor", _("Chassis Vendor")),
            ("chassis_version", _("Chassis Version")),
            ("product_family", _("Product Family")),
            ("product_name", _("Product Name")),
            ("product_serial", _("Product Serial Number")),
            ("product_sku", _("Product SKU")),
            ("product_uuid", _("Product UUID")),
            ("product_version", _("Product Version")),
            ("power", _("Power")),
            # ("subsystem", _("Subsystem")),
            ("sys_vendor", _("System Vendor")),
        ]

        power_keys = [
            ("control", _("Control")),
            ("runtime_active_time", _("Runtime Active Time")),
            ("runtime_status", _("Runtime Status")),
            ("runtime_suspended_time", _("Runtime Suspended Time"))
        ]

        # Create and set the main preferences group for motherboard info
        group = Adw.PreferencesGroup(title=_("Motherboard"), description=_("Details from /sys/devices/virtual/dmi/id"))
        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic", valign=3, css_classes=["flat"])
        refresh_button.set_tooltip_text(_("Refresh"))
        refresh_button.connect("clicked", self.update_motherboard_page)
        group.set_header_suffix(refresh_button)
        self.motherboard_content.add(group)
        self.motherboard_page_children.append(group)

        # Populate the group with DMI details
        for key, label in dmi_keys:
            if key == "power":
                expander_row = Adw.ExpanderRow(title=label)
                group.add(expander_row)
                for key2, label2 in power_keys:
                    row = Adw.ActionRow(title=label2)
                    try:
                        with open(os.path.join(dmi_path + "power/", key2), 'r') as f:
                            value2 = f.read().strip() or "N/A"
                    except:
                        value2 = "N/A"  # Or any default value if you cannot access a file
                    row.add_suffix(Gtk.Label(label=value2, wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
                    expander_row.add_row(row)
                continue
            try:
                with open(os.path.join(dmi_path, key), 'r') as f:
                    value = f.read().strip() or "N/A"
            except:
                value = "N/A"  # Or any default value if you cannot access a file

            row = Adw.ActionRow(title=label)
            row.add_suffix(Gtk.Label(label=value, wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
            group.add(row)

