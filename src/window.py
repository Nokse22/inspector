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

@Gtk.Template(resource_path='/io/github/nokse22/inspector/ui/window.ui')
class InspectorWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'InspectorWindow'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = Gio.Settings.new('io.github.nokse22.inspector')

        # self.set_default_size(800, 820)
        self.props.width_request=360
        self.props.height_request=400
        self.settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)

        self.split_view = Adw.OverlaySplitView(collapsed=False)

        # self.set_content(self.split_view)
        self.toolbar_view = Adw.ToolbarView()
        self.split_view.set_content(self.toolbar_view)
        headerbar = Adw.HeaderBar()
        self.title_label = Gtk.Label(label="Usb")
        headerbar.set_title_widget(self.title_label)
        sidebar_button = Gtk.Button(icon_name="sidebar-show-symbolic", visible=False)
        sidebar_button.connect("clicked", self.show_sidebar)
        headerbar.pack_start(sidebar_button)
        reload_button = Gtk.Button(icon_name="view-refresh-symbolic",valign=3, css_classes=["flat"])
        reload_button.connect("clicked", self.reload_current)
        self.toolbar_view.add_top_bar(headerbar)

        self.sidebar_toolbar_view = Adw.ToolbarView()
        self.split_view.set_sidebar(self.sidebar_toolbar_view)
        sidebar_headerbar = Adw.HeaderBar()
        # self.set_title(_("Inspector"))
        sidebar_headerbar.set_show_title(True)
        self.sidebar_toolbar_view.add_top_bar(sidebar_headerbar)

        self.sidebar_scrolled_window = Gtk.ScrolledWindow(vexpand=True)
        self.sidebar_scrolled_window.set_policy(2,1)
        self.sidebar_toolbar_view.set_content(self.sidebar_scrolled_window)
        self.sidebar_list_box = Gtk.ListBox(css_classes=["navigation-sidebar"])
        self.sidebar_list_box.connect("row-selected", self.on_row_selected)
        self.sidebar_scrolled_window.set_child(self.sidebar_list_box)

        self.clamp = Adw.Clamp(margin_start=12, margin_end=12)
        self.scrolled_window = Gtk.ScrolledWindow(vexpand=True)
        self.scrolled_window.set_policy(2,1)
        self.scrolled_window.set_child(self.clamp)
        self.toolbar_view.set_content(self.scrolled_window)

        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        menu.append(_("Reload"), "app.reload")
        menu.append(_("Keyboard shortcuts"), "win.show-help-overlay")
        menu.append(_("About Inspector"), "app.about")

        menu_button.set_menu_model(menu)
        sidebar_headerbar.pack_start(menu_button)

        self.menu_button = Gtk.MenuButton(visible=False)
        self.menu_button.set_icon_name("open-menu-symbolic")
        self.menu_button.set_menu_model(menu)
        headerbar.pack_end(self.menu_button)
        headerbar.pack_end(reload_button)

        sidebar_condition = Adw.BreakpointCondition.new_length(1, 600, 2)
        sidebar_breakpoint = Adw.Breakpoint.new(sidebar_condition)

        sidebar_breakpoint.set_condition(sidebar_condition)
        sidebar_breakpoint.add_setter(self.split_view, "collapsed", True)
        sidebar_breakpoint.add_setter(menu_button, "visible", False)
        sidebar_breakpoint.add_setter(sidebar_button, "visible", True)
        sidebar_breakpoint.connect("apply", self.toggle_menu_button)
        sidebar_breakpoint.connect("unapply", self.toggle_menu_button)

        self.add_breakpoint(sidebar_breakpoint)

        self.motherboard_content = Gtk.Box(orientation=1)
        self.sidebar_list_box.append(Gtk.Label(label=_("Motherboard"), name="MOBO", xalign=0, margin_top=8, margin_bottom=8))

        self.cpu_content = Gtk.Box(orientation=1)
        self.sidebar_list_box.append(Gtk.Label(label=_("Processor"), name="CPU", xalign=0, margin_top=8, margin_bottom=8))

        self.memory_content = Gtk.Box(orientation=1)
        self.sidebar_list_box.append(Gtk.Label(label=_("Memory"), name="MEMORY", xalign=0, margin_top=8, margin_bottom=8))

        self.disks_content = Gtk.Box(orientation=1)
        self.sidebar_list_box.append(Gtk.Label(label=_("Disk Drives"), name="DISK", xalign=0, margin_top=8, margin_bottom=8))

        self.pci_content = Gtk.Box(orientation=1)
        self.sidebar_list_box.append(Gtk.Label(label=_("PCI Devices"), name="PCI", xalign=0, margin_top=8, margin_bottom=8))

        self.usb_content = Gtk.Box(orientation=1)
        self.sidebar_list_box.append(Gtk.Label(label=_("USB Devices"), name="USB", xalign=0, margin_top=8, margin_bottom=8))

        self.network_content = Gtk.Box(orientation=1)
        self.sidebar_list_box.append(Gtk.Label(label=_("Network Devices"), name="NETWORK", xalign=0, margin_top=8, margin_bottom=8))

        self.kernel_content = Gtk.Box(orientation=1)
        self.sidebar_list_box.append(Gtk.Label(label=_("Kernel"), name="KERNEL", xalign=0, margin_top=8, margin_bottom=8))

        self.system_content = Gtk.Box(orientation=1)
        self.sidebar_list_box.append(Gtk.Label(label=_("Distribution"), name="SYSTEM", xalign=0, margin_top=8, margin_bottom=8))

        self.sidebar_list_box.select_row( self.sidebar_list_box.get_row_at_index(0))

    def toggle_menu_button(self, brkpnt):
        self.menu_button.set_visible(not self.menu_button.get_visible())

    def reload_current(self, btn=None):
        name = self.sidebar_list_box.get_selected_row().get_child().get_name()
        match name:
            case "USB":
                self.update_usb_page()
            case "DISK":
                self.update_disk_page()
            case "PCI":
                self.update_pci_page()
            case "MEMORY":
                self.update_memory_page()
            case "NETWORK":
                self.update_network_page()
            case "CPU":
                self.update_cpu_page()
            case "MOBO":
                self.update_motherboard_page()
            case "SYSTEM":
                self.update_system_page()
            case "KERNEL":
                self.update_kernel_page()

    def on_row_selected(self, list_box, row):
        name = row.get_child().get_name()
        nice_name = row.get_child().get_label()
        self.title_label.set_label(nice_name)
        match name:
            case "USB":
                if self.usb_content.get_first_child() == None:
                    self.update_usb_page()
                self.clamp.set_child(self.usb_content)
            case "DISK":
                if self.disks_content.get_first_child() == None:
                    self.update_disk_page()
                self.clamp.set_child(self.disks_content)
            case "PCI":
                if self.pci_content.get_first_child() == None:
                    self.update_pci_page()
                self.clamp.set_child(self.pci_content)
            case "MEMORY":
                if self.memory_content.get_first_child() == None:
                    self.update_memory_page()
                self.clamp.set_child(self.memory_content)
            case "NETWORK":
                if self.network_content.get_first_child() == None:
                    self.update_network_page()
                self.clamp.set_child(self.network_content)
            case "CPU":
                if self.cpu_content.get_first_child() == None:
                    self.update_cpu_page()
                self.clamp.set_child(self.cpu_content)
            case "MOBO":
                if self.motherboard_content.get_first_child() == None:
                    self.update_motherboard_page()
                self.clamp.set_child(self.motherboard_content)
            case "SYSTEM":
                if self.system_content.get_first_child() == None:
                    self.update_system_page()
                self.clamp.set_child(self.system_content)
            case "KERNEL":
                if self.system_content.get_first_child() == None:
                    self.update_kernel_page()
                self.clamp.set_child(self.kernel_content)
        if self.split_view.get_collapsed():
            self.split_view.set_show_sidebar(False)

    def show_sidebar(self, btn):
        self.split_view.set_show_sidebar(not self.split_view.get_show_sidebar())


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
        group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24)
        empty_command_status_page = Adw.StatusPage(title=_("The command is not supported"),
                icon_name="computer-fail-symbolic", hexpand=True, vexpand=True,
                description=_("The command {0} returned empty.\n"
                              "Try running it on your terminal, it should prompt you to "
                              "install the package on your system.").format(command))
        group.add(empty_command_status_page)
        return group

    def update_system_page(self, btn=None):
        self.remove_content(self.system_content)
        out = self.execute_terminal_command("uname -a")
        if out == "":
            page = self.empty_command_page("uname")
            self.system_content.append(page)
            return

        group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_("Distribution"), description="Details from /etc/os-release")
        self.system_content.append(group)

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
                row.add_suffix(Gtk.Label(opacity=0.60 , label=value.replace('"', ''), wrap=True, wrap_mode=2, hexpand=True, xalign=1, justify=1))
            group.add(row)

    def update_kernel_page(self, btn=None):
        self.remove_content(self.kernel_content)
        out = self.execute_terminal_command("uname -a")
        if out == "":
            page = self.empty_command_page("uname")
            self.kernel_content.append(page)
            return
        group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_("System"), description=_("Command: uname"))
        self.kernel_content.append(group)

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

        group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_("Distribution"), description=_("Command: cat /etc/os-release"))
        self.system_content.append(group)
        
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
        self.remove_content(self.disks_content)
        out = self.execute_terminal_command("lsblk -J")

        if out == "":
            page = self.empty_command_page("lsblk")
            self.disks_content.append(page)
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
                    group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=name, description=_("Command: lsblk"))
                    self.disks_content.append(group)
                    expander_row = Adw.ExpanderRow(title=_("Total size: "+size))
                    group.add(expander_row)
                else:
                    if loop_group == None:
                        loop_count = self.execute_terminal_command("lsblk -d | grep loop | wc -l")
                        loop_group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_("Loop devices"), description=_("Command: lsblk"))
                        self.disks_content.append(loop_group)
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
                    group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, )
                    self.disks_content.append(group)
                    try:
                        partitions = device["children"]
                    except:
                        partitions = []
                    for partition in partitions:
                        try:
                            subtitle = partition['mountpoints'][0]
                            if subtitle and fnmatch.fnmatch(subtitle, "/snap"):
                                subtitle = '/'
                            if subtitle.startswith('/var/lib/snapd/hostfs/'):
                                subtitle = subtitle[21:]
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
        self.remove_content(self.memory_content)
        out = self.execute_terminal_command("lsmem -J")
        if out == "":
            page = self.empty_command_page("lsmem")
            self.memory_content.append(page)
        else:
            data = json.loads(out)
            group2 = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_("Ranges"), description=_("Command: lsmem"))
            self.memory_content.append(group2)
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
        self.remove_content(self.pci_content)
        out = self.execute_terminal_command("lspci")
        if out == "":
            page = self.empty_command_page("lspci")
            self.pci_content.append(page)
        else:
            out = out.splitlines()
            text = "range "
            pattern = r'(\S+)\s(.*?):\s(.*)'
            group2 = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_("PCIs"), description=_("Command: lspci"))
            self.pci_content.append(group2)
            for line in out:
                match = re.match(pattern, line)
                if match:
                    first_part = match.group(1)
                    second_part = match.group(2)
                    third_part = match.group(3)

                    action_row = Adw.ActionRow(title=third_part, subtitle=second_part)
                    group2.add(action_row)

    def update_usb_page(self, btn=None):
        self.remove_content(self.usb_content)
        out = self.execute_terminal_command("lsusb")
        if out == "":
            page = self.empty_command_page("lsusb")
            self.usb_content.append(page)
        else:
            out = out.splitlines()
            group2 = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_("USB"), description=_("Command: lsusb"))
            self.usb_content.append(group2)
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
        self.remove_content(self.network_content)
        out = self.execute_terminal_command("ip -j address")
        if out == "":
            page = self.empty_command_page("ip address")
            self.network_content.append(page)
        else:
            data = json.loads(out)
            for line in data:
                try:
                    name = line['ifname']
                except:
                    name = "N/A"
                group2 = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=name, description=_("Command: ip address"))
                self.network_content.append(group2)
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

    def remove_content(self, box):
        child = box.get_first_child()
        while child != None:
            box.remove(child)
            child = box.get_first_child()

    def update_cpu_page(self, btn=None):
        self.remove_content(self.cpu_content)
        out = self.execute_terminal_command("lscpu -J")
        if out == "":
            page = self.empty_command_page("lscpu")
            self.cpu_content.append(page)
        else:
            data = json.loads(out)
            group2 = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_("CPU"), description=_("Command: lshw -c cpu"))
            self.cpu_content.append(group2)

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
        self.remove_content(self.motherboard_content)
        
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
        group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_("Motherboard"), description=_("Details from /sys/devices/virtual/dmi/id"))
        self.motherboard_content.append(group)

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

