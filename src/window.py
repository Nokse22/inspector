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
from gi.repository import GLib

import gettext 
import gi, os, subprocess, threading, time, json, re, fnmatch, datetime, io, markdown_it, weasyprint

@Gtk.Template(resource_path='/io/github/nokse22/inspector/ui/window.ui')
class InspectorWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'InspectorWindow'

    motherboard_content = Gtk.Template.Child()
    system_content = Gtk.Template.Child()
    disks_content = Gtk.Template.Child()
    pci_content = Gtk.Template.Child()
    memory_content = Gtk.Template.Child()
    usb_content = Gtk.Template.Child()
    kernel_content = Gtk.Template.Child()
    network_content = Gtk.Template.Child()
    cpu_content = Gtk.Template.Child()

    overlay_split_view = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    window_title = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = Gio.Settings.new('io.github.nokse22.inspector')

        self.settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)

        self.main_stack.connect("notify::visible-child-name", self.on_stack_child_name_changed)

        self.update_motherboard_page()
        self.update_usb_page()
        self.update_disk_page()
        self.update_pci_page()
        self.update_memory_page()
        self.update_network_page()
        self.update_cpu_page()
        self.update_system_page()
        self.update_kernel_page()

    def on_stack_child_name_changed(self, stack, child_name):
        self.window_title.set_title(self.main_stack.get_visible_child().get_name())

    @Gtk.Template.Callback("on_sidebar_button_clicked")
    def on_sidebar_button_clicked(self, btn):
        self.overlay_split_view.set_show_sidebar(True)

    @Gtk.Template.Callback("on_reload_clicked")
    def on_reload_clicked(self, btn):
        page_name = self.main_stack.get_visible_child_name()
        match page_name:
            case "usb_devices":
                self.update_usb_page()
            case "disk_drives":
                self.update_disk_page()
            case "pci_devices":
                self.update_pci_page()
            case "memory":
                self.update_memory_page()
            case "network_devices":
                self.update_network_page()
            case "processor":
                self.update_cpu_page()
            case "motherboard":
                self.update_motherboard_page()
            case "distribution":
                self.update_system_page()
            case "kernel":
                self.update_kernel_page()

    @Gtk.Template.Callback("on_md_export_clicked")
    def on_md_export_clicked(self, btn):
        global report
        report_raw = self.generate_report_text()

        report = report_raw
        
        self.file_save_dialog('md')

    @Gtk.Template.Callback("on_html_export_clicked")
    def on_html_export_clicked(self, btn):
        global report
        report_raw = self.generate_report_text()

        md = (markdown_it.MarkdownIt('commonmark', {'breaks':True, 'html':True}))

        report = md.render(report_raw)

        self.file_save_dialog('html')

    @Gtk.Template.Callback("on_pdf_export_clicked")
    def on_pdf_export_clicked(self, btn):
        global report
        report_raw = self.generate_report_text()
        return
        report_file = io.BytesIO()
        xhtml2pdf.pisa.CreatePDF(report_raw, report_file)
        report = report_file.getbuffer()

        self.file_save_dialog('pdf')

    def file_save_dialog(self, type):
        file_save = Gtk.FileDialog()
        file_save.set_initial_name(f"inspector-report-{datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.{type}")
        file_save.save_text_file(self, None, self.file_save_response)

    def file_save_response(self, dialog, result):
        global report
        try:
            file = dialog.save_text_file_finish(result)
        except:
            pass
        else:
            report_bytes = GLib.Bytes.new(report.encode("utf-8"))
            file[0].replace_contents_bytes_async(report_bytes, None, False, Gio.FileCreateFlags.NONE)
            del report

    def execute_terminal_command(self, command):
        if 'FLATPAK_ID' in os.environ:
            console_permissions = "flatpak-spawn --host "
        else:
            console_permissions = ""
        txt = console_permissions + command
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
        empty_command_status_page = Adw.StatusPage(title=_("Error executing command"),
                icon_name="computer-fail-symbolic", hexpand=True, vexpand=True,
                description=_("The command {0} returned empty.").format(command))
        group.add(empty_command_status_page)
        return group

    def update_system_page(self, *args, export_data = False):
        self.remove_content(self.system_content)
        out = self.execute_terminal_command("uname -a")
        if out == "":
            page = self.empty_command_page("uname")
            self.system_content.append(page)
            return

        title_string = "Distribution"
        description_string = "Details from /etc/os-release"
        group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_(title_string), description=(description_string))
        self.system_content.append(group)
        if export_data:
            markdown_data = f"\n\n## {title_string}\n`{description_string}`\n\n"

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

            if export_data:
                markdown_data += f"**{key}:** {value.replace('"', '')}\n"
        
        if export_data:
            return markdown_data

    def update_kernel_page(self, *args, export_data = False):
        self.remove_content(self.kernel_content)
        out = self.execute_terminal_command("uname -a")
        if out == "":
            page = self.empty_command_page("uname")
            self.kernel_content.append(page)
            return
        title_string = "System"
        description_string = "Command: uname"
        group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_(title_string), description=_(description_string))
        self.kernel_content.append(group)
        if export_data:
            markdown_data = f"\n\n## {title_string}\n`{description_string}`\n\n"
        
        title_string = "Kernel Name"
        out = self.execute_terminal_command("uname -s")
        row = Adw.ActionRow(title=_(title_string))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1, css_classes=["dim-label"]))
        group.add(row)
        if export_data:
            markdown_data += f"**{title_string}:** {out.replace('\n', "")}\n"

        title_string = "Network Node Hostname"
        out = self.execute_terminal_command("uname -n")
        row = Adw.ActionRow(title=_(title_string))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1, css_classes=["dim-label"]))
        group.add(row)
        if export_data:
            markdown_data += f"**{title_string}:** {out.replace('\n', "")}\n"

        title_string = "Kernel Release"
        out = self.execute_terminal_command("uname -r")
        row = Adw.ActionRow(title=_(title_string))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1, css_classes=["dim-label"]))
        group.add(row)
        if export_data:
            markdown_data += f"**{title_string}:** {out.replace('\n', "")}\n"

        title_string = "Kernel Version"
        out = self.execute_terminal_command("uname -v")
        row = Adw.ActionRow(title=_(title_string))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1, css_classes=["dim-label"]))
        group.add(row)
        if export_data:
            markdown_data += f"**{title_string}:** {out.replace('\n', "")}\n"

        title_string = "Machine Hardware Name"
        out = self.execute_terminal_command("uname -m")
        row = Adw.ActionRow(title=_(title_string))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1, css_classes=["dim-label"]))
        group.add(row)
        if export_data:
            markdown_data += f"**{title_string}:** {out.replace('\n', "")}\n"

        title_string = "Processor Type"
        out = self.execute_terminal_command("uname -p")
        row = Adw.ActionRow(title=_(title_string))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1, css_classes=["dim-label"]))
        group.add(row)
        if export_data:
            markdown_data += f"**{title_string}:** {out.replace('\n', "")}\n"

        title_string = "Hardware Platform"
        out = self.execute_terminal_command("uname -i")
        row = Adw.ActionRow(title=_(title_string))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1, css_classes=["dim-label"]))
        group.add(row)
        if export_data:
            markdown_data += f"**{title_string}:** {out.replace('\n', "")}\n"

        title_string = "Operating System"
        out = self.execute_terminal_command("uname -o")
        row = Adw.ActionRow(title=_(title_string))
        row.add_suffix(Gtk.Label(label=out.replace('\n', ""), wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1, css_classes=["dim-label"]))
        group.add(row)
        if export_data:
            markdown_data += f"**{title_string}:** {out.replace('\n', "")}\n"

        if export_data:
            return markdown_data

    def update_disk_page(self, *args, export_data = False):
        self.remove_content(self.disks_content)
        out = self.execute_terminal_command("lsblk -J")

        if out == "":
            page = self.empty_command_page("lsblk")
            self.disks_content.append(page)
        else:
            if export_data:
                markdown_data = ""
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
                    if "children" in device:
                        try:
                            size = device['size']
                        except:
                            size = ""
                        description_string = "Command: lsblk"
                        group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=name, description=_(description_string))
                        self.disks_content.append(group)
                        expander_row = Adw.ExpanderRow(title=_("Total size: "+size))
                        group.add(expander_row)
                        if export_data:
                            markdown_data += f"\n\n## {name}\n`{description_string}`\n\n**{"Total size: "+size}**\n"
                    else:
                        try:
                            size = device['size']
                        except:
                            size = ""
                        description_string = "Command: lsblk"
                        group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=name, description=_(description_string))
                        self.disks_content.append(group)
                        action_row = Adw.ActionRow(title=_("Total size: "+size))
                        group.add(action_row)
                        if export_data:
                            markdown_data += f"\n\n## {name}\n`{description_string}`\n\n**{"Total size: "+size}**\n"
                else:
                    if loop_group == None:
                        title_string = "Loop devices"
                        description_string = "Command: lsblk"
                        loop_count = self.execute_terminal_command("lsblk -d | grep loop | wc -l")
                        loop_group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_(title_string), description=_(description_string))
                        self.disks_content.append(loop_group)
                        loop_expander_row = Adw.ExpanderRow(title=gettext.ngettext("Device Count: %s", "Devices Count: %s", loop_count) % loop_count.rstrip())
                        loop_group.add(loop_expander_row)
                        if export_data:
                            markdown_data += f"\n\n## {title_string}\n\n`{description_string}`\n**{"Total size: "+size}:** {gettext.ngettext("Device Count: %s", "Devices Count: %s", loop_count) % loop_count.rstrip()}\n"
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
                    if export_data:
                        markdown_data += f"\n\n## {name}\n**{subtitle}:**{size}\n"
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

                        if export_data:
                            if subtitle != "":
                                markdown_data += f"* {name} - {subtitle} - {size}\n"
                            else:
                                markdown_data += f"* {name} - {size}\n"

            if export_data:
                return markdown_data

    def update_memory_page(self, *args, export_data = False):
        self.remove_content(self.memory_content)
        out = self.execute_terminal_command("lsmem -J")
        if out == "":
            page = self.empty_command_page("lsmem")
            self.memory_content.append(page)
        else:
            data = json.loads(out)
            title_string = "Ranges"
            description_string = "Command: lsmem"
            group2 = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_(title_string), description=_(description_string))
            self.memory_content.append(group2)
            if export_data:
                markdown_data = f"\n\n## {title_string}\n`{description_string}`\n\n"
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
                box = Gtk.Box(homogeneous=True, hexpand=True, width_request=150)
                box.append(Gtk.Label(label=size, wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1))
                box.append(Gtk.Label(label=block, wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1))
                title_string = "Memory"
                row = Adw.ActionRow(title=_(title_string), subtitle=range_)
                row.add_suffix(box)
                group2.add(row)

                if export_data:
                    markdown_data += f"**{title_string}:**{range_} - {size} - {block}\n"
            
            if export_data:
                return markdown_data

    def update_pci_page(self, *args, export_data = False):
        self.remove_content(self.pci_content)
        out = self.execute_terminal_command("lspci")
        if out == "":
            page = self.empty_command_page("lspci")
            self.pci_content.append(page)
        else:
            out = out.splitlines()
            text = "range "
            pattern = r'(\S+)\s(.*?):\s(.*)'
            title_string = "PCI"
            description_string = "Command: lspci"
            group2 = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_(title_string), description=_(description_string))
            self.pci_content.append(group2)
            if export_data:
                markdown_data = f"\n\n## {title_string}\n`{description_string}`\n\n"
            for line in out:
                match = re.match(pattern, line)
                if match:
                    first_part = match.group(1)
                    second_part = match.group(2)
                    third_part = match.group(3)

                    action_row = Adw.ActionRow(title=third_part, subtitle=second_part)
                    group2.add(action_row)

                    if export_data:
                        markdown_data += f"**{third_part}:** {second_part} - {first_part}\n" # should the first_part be displayed in report? it doesn't show in the window?

            if export_data:
                return markdown_data

    def update_usb_page(self, *args, export_data = False):
        self.remove_content(self.usb_content)
        out = self.execute_terminal_command("lsusb")
        if out == "":
            page = self.empty_command_page("lsusb")
            self.usb_content.append(page)
        else:
            out = out.splitlines()
            title_string = "USB"
            description_string = "Command: lsusb"
            group2 = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_(title_string), description=_(description_string))
            self.usb_content.append(group2)
            if export_data:
                markdown_data = f"\n\n## {title_string}\n`{description_string}`\n\n"
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
                action_row.add_suffix(Gtk.Label(label=value, xalign=1, justify=1, selectable=True, css_classes=["dim-label"]))
                expander_row.add_row(action_row)

                action_row = Adw.ActionRow(title=_("Bus"))
                action_row.add_suffix(Gtk.Label(label=result[0], wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1, css_classes=["dim-label"]))
                expander_row.add_row(action_row)

                if export_data:
                    markdown_data += f"**{result[2]}:**\n* {name} - {value}\n* {"Bus"} - {result[0]}\n"
        
            if export_data:
                return markdown_data

    def update_network_page(self, *args, export_data = False):
        self.remove_content(self.network_content)
        out = self.execute_terminal_command("ip -j address")
        if out == "":
            page = self.empty_command_page("ip address")
            self.network_content.append(page)
        else:
            markdown_data = ""
            data = json.loads(out)
            for line in data:
                try:
                    title_string = line['ifname']
                except:
                    title_string = "N/A"
                description_string = "Command: ip address"
                group2 = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=title_string, description=_(description_string))
                self.network_content.append(group2)
                if export_data:
                    markdown_data += f"\n\n## {title_string}\n`{description_string}`\n\n"
                for key, value in line.items():

                    if isinstance(value, list):
                        for val in value:
                            if isinstance(val, dict):
                                if key == "addr_info":
                                    title_string = "Address info, ip"
                                    expander_row = Adw.ExpanderRow(title=_(title_string))
                                    markdown_data += f"**{title_string}**\n"
                                else:
                                    expander_row = Adw.ExpanderRow(title=key[0].upper() + key[1:])
                                    markdown_data += f"**{key[0].upper() + key[1:]}**\n"
                                group2.add(expander_row)
                                for key2, value2 in val.items():
                                    row = Adw.ActionRow(title=key2[0].upper() + key2[1:])
                                    expander_row.add_row(row)
                                    box = Gtk.Box(homogeneous=True, hexpand=True)
                                    box.append(Gtk.Label(label=value2, xalign=1, wrap=True, wrap_mode=1, selectable=True, hexpand=True, justify=1))
                                    row.add_suffix(box)
                                    if export_data:
                                        markdown_data += f"* {key2[0].upper() + key2[1:]}:  {value2}\n"
                        try:
                            value[0]
                        except:
                            pass
                        else:
                            if not isinstance(value[0], dict):
                                expander_row = Adw.ExpanderRow(title=key[0].upper() + key[1:])
                                group2.add(expander_row)
                                text = ""
                                textmd = ""
                                for val in value:
                                    text += val + ", "
                                    textmd += f"\n* {val}"
                                row = Adw.ActionRow(title=text)
                                expander_row.add_row(row)
                                if export_data:
                                    markdown_data += f"**{key[0].upper() + key[1:]}:** {textmd}\n"
                    elif key not in ["ifname","ifindex", "addr_info"]:
                        row = Adw.ActionRow(title=key[0].upper() + key[1:])
                        row.add_suffix(Gtk.Label(label=value, xalign=1, wrap=True, wrap_mode=1, selectable=True, hexpand=True, justify=1, css_classes=["dim-label"]))
                        group2.add(row)
                        if export_data:
                            markdown_data += f"**{key[0].upper() + key[1:]}:** {value}\n"

            if export_data:
                return markdown_data

    def remove_content(self, box):
        child = box.get_first_child()
        while child != None:
            box.remove(child)
            del child
            child = box.get_first_child()

    def update_cpu_page(self, *args, export_data = False):
        self.remove_content(self.cpu_content)
        out = self.execute_terminal_command("lscpu -J")
        if out == "":
            page = self.empty_command_page("lscpu")
            self.cpu_content.append(page)
        else:
            data = json.loads(out)
            title_string = "CPU"
            description_string = "Command: lscpu"
            group2 = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_(title_string), description=_(description_string))
            self.cpu_content.append(group2)
            if export_data:
                markdown_data = f"\n\n## {title_string}\n`{description_string}`\n\n"


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
                        if export_data:
                            markdown_data += f"**{value[0].upper() + value[1:]}**\n"
                        add_flags = True
                    elif add_flags:
                        row2 = Adw.ActionRow(title=value)
                        row.add_row(row2)
                        if export_data:
                            markdown_data += f"* `{value}`\n"
                        add_flags = False
                    elif key == "field":
                        row = Adw.ActionRow(title=value[0].upper() + value[1:])
                        if export_data:
                            markdown_data += f"**{value[0].upper() + value[1:]}** "
                    elif key == "data":

                        row.add_suffix(Gtk.Label(label=value[0].upper() + value[1:], css_classes=["dim-label"],
                                xalign=1, wrap=True, wrap_mode=1, selectable=True, hexpand=True, justify=1))
                        group2.add(row)
                        if export_data:
                            markdown_data += f"{value[0].upper() + value[1:]}\n"
            
            if export_data:
                return markdown_data

    def update_motherboard_page(self, *args, export_data = False):
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
        title_string = "Motherboard"
        description_string = "Details from /sys/devices/virtual/dmi/id"
        group = Adw.PreferencesGroup(margin_top=24, margin_bottom=24, title=_(title_string), description=_(description_string))
        self.motherboard_content.append(group)
        if export_data:
            markdown_data = f"\n\n## {title_string}\n`{description_string}`\n\n"

        # Populate the group with DMI details
        for key, label in dmi_keys:
            if key == "power":
                expander_row = Adw.ExpanderRow(title=label)
                group.add(expander_row)
                if export_data:
                    markdown_data += f"**{label}:**\n"
                for key2, label2 in power_keys:
                    row = Adw.ActionRow(title=label2)
                    try:
                        with open(os.path.join(dmi_path + "power/", key2), 'r') as f:
                            value2 = f.read().strip() or "N/A"
                    except:
                        value2 = "N/A"  # Or any default value if you cannot access a file
                    row.add_suffix(Gtk.Label(label=value2, wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1))
                    expander_row.add_row(row)
                    if export_data:
                        markdown_data += f"* {label2} - {value2}\n"
                continue
            try:
                with open(os.path.join(dmi_path, key), 'r') as f:
                    value = f.read().strip() or "N/A"
            except:
                value = "N/A"  # Or any default value if you cannot access a file

            row = Adw.ActionRow(title=label)
            row.add_suffix(Gtk.Label(label=value, wrap=True, wrap_mode=1, selectable=True, hexpand=True, xalign=1, justify=1, css_classes=["dim-label"]))
            group.add(row)

            if export_data:
                markdown_data += f"**{label}:** {value}\n"
        
        if export_data:
            return markdown_data

    def generate_report_text(self, *args): # produces a large markdown formatted string containing all data that inspector can see

        # save all text output from the various pages
        # it would be possible to have it auto save this data to memory when updating the pages anyway giving 
        # faster report generation when the user wants but at the expense of slightly poorer memory efficency during general use
        md_report_string = f"# Inspector Report:\n**Report done at: `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`**\n**Report issues or contribute at: https://github.com/Nokse22/inspector**"
        md_report_string += f"\n\n# Motherboard Information:{self.update_motherboard_page(export_data = True)}"
        md_report_string += f"\n\n# USB Device Information:{self.update_usb_page(export_data = True)}"
        md_report_string += f"\n\n# Disk Information:{self.update_disk_page(export_data = True)}"
        md_report_string += f"\n\n# PCI Device Information:{self.update_pci_page(export_data = True)}"
        md_report_string += f"\n\n# Memory/RAM Information:{self.update_memory_page(export_data = True)}"
        md_report_string += f"\n\n# Network Device Information:{self.update_network_page(export_data = True)}"
        md_report_string += f"\n\n# Processor/CPU Information:{self.update_cpu_page(export_data = True)}"
        md_report_string += f"\n\n# System Information:{self.update_system_page(export_data = True)}"
        md_report_string += f"\n\n# Kernel Information:{self.update_kernel_page(export_data = True)}"

        return md_report_string