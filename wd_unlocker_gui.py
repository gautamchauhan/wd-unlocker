#!/usr/bin/env python3
"""
WD Unlocker - GUI application for unlocking Western Digital hard disks on Linux
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os
import subprocess
import threading


SUPPORTED_MODEL_PREFIXES = ('My Passport',)


def detect_wd_passport():
    """Find a connected WD My Passport via sysfs and report its lock state.

    A locked My Passport exposes its SCSI device with size=0 (the data side
    is gated behind the firmware password); once unlocked the same device
    reports its real sector count. That lets us detect lock state without
    running anything privileged.

    Returns a dict {device, model, size_sectors, status} for the first match,
    or None if no supported WD device is connected.
    """
    sys_block = '/sys/block'
    try:
        names = sorted(os.listdir(sys_block))
    except OSError:
        return None

    candidates = []
    for name in names:
        if not name.startswith('sd'):
            continue
        device_dir = os.path.join(sys_block, name, 'device')
        try:
            with open(os.path.join(device_dir, 'vendor')) as f:
                vendor = f.read().strip()
            with open(os.path.join(device_dir, 'model')) as f:
                model = f.read().strip()
            with open(os.path.join(device_dir, 'type')) as f:
                scsi_type = f.read().strip()
            with open(os.path.join(sys_block, name, 'size')) as f:
                size_sectors = int(f.read().strip())
        except (OSError, ValueError):
            continue

        if vendor != 'WD':
            continue
        if scsi_type != '0':  # 0 = SCSI direct-access (disk)
            continue
        if not any(model.startswith(p) for p in SUPPORTED_MODEL_PREFIXES):
            continue

        candidates.append({
            'device': f'/dev/{name}',
            'model': model,
            'size_sectors': size_sectors,
            'status': 'unlocked' if size_sectors > 0 else 'locked',
        })

    if not candidates:
        return None
    # If more than one supported drive is present (e.g. one locked, one
    # unlocked), prefer the locked one so the user sees the actionable state.
    for c in candidates:
        if c['status'] == 'locked':
            return c
    return candidates[0]


def format_size(size_sectors):
    """Format a 512-byte sector count as a human-readable size."""
    if size_sectors <= 0:
        return ''
    gb = size_sectors * 512 / 1e9
    if gb >= 1000:
        return f'{gb / 1000:.2f} TB'
    return f'{gb:.0f} GB'


class WDUnlockerWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="WD Disk Unlocker")
        self.set_border_width(20)
        self.set_default_size(420, 280)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.detected_disk = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.add(vbox)

        # Title
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_halign(Gtk.Align.CENTER)
        title_label = Gtk.Label()
        title_label.set_markup(
            "<span size='large' weight='bold'>Western Digital Disk Unlocker</span>"
        )
        header_box.pack_start(title_label, False, False, 0)
        vbox.pack_start(header_box, False, False, 0)

        # Dynamic per-state info line; populated by refresh_state().
        self.info_label = Gtk.Label()
        self.info_label.set_halign(Gtk.Align.CENTER)
        self.info_label.set_line_wrap(True)
        self.info_label.set_max_width_chars(50)
        vbox.pack_start(self.info_label, False, False, 0)

        # Password row — only shown when a locked disk is detected.
        self.password_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        password_label = Gtk.Label(label="Password:")
        password_label.set_width_chars(10)
        self.password_box.pack_start(password_label, False, False, 0)

        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.set_invisible_char("●")
        self.password_entry.set_placeholder_text("Enter your disk password")
        self.password_entry.set_activates_default(True)
        self.password_box.pack_start(self.password_entry, True, True, 0)

        self.show_password_check = Gtk.CheckButton(label="Show")
        self.show_password_check.connect("toggled", self.on_show_password_toggled)
        self.password_box.pack_start(self.show_password_check, False, False, 0)

        # no_show_all so the window-level show_all() in main() can't override
        # the visibility we set in refresh_state().
        self.password_box.set_no_show_all(True)
        vbox.pack_start(self.password_box, False, False, 0)

        # Transient operation status (success / error / info).
        self.status_label = Gtk.Label()
        self.status_label.set_line_wrap(True)
        self.status_label.set_max_width_chars(50)
        vbox.pack_start(self.status_label, False, False, 0)

        self.spinner = Gtk.Spinner()
        vbox.pack_start(self.spinner, False, False, 0)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.CENTER)

        self.unlock_button = Gtk.Button(label="Unlock")
        self.unlock_button.set_size_request(110, 35)
        self.unlock_button.connect("clicked", self.on_unlock_clicked)
        self.unlock_button.set_can_default(True)
        self.unlock_button.get_style_context().add_class("suggested-action")
        self.unlock_button.set_no_show_all(True)
        button_box.pack_start(self.unlock_button, False, False, 0)

        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.set_size_request(100, 35)
        refresh_button.connect("clicked", lambda x: self.refresh_state())
        button_box.pack_start(refresh_button, False, False, 0)

        close_button = Gtk.Button(label="Close")
        close_button.set_size_request(100, 35)
        close_button.connect("clicked", lambda x: self.destroy())
        button_box.pack_start(close_button, False, False, 0)

        vbox.pack_start(button_box, False, False, 0)

        self.unlock_button.grab_default()

        self.refresh_state()

    def refresh_state(self, clear_status=True):
        """Re-detect the WD disk and adjust the info text + form visibility."""
        self.detected_disk = detect_wd_passport()
        if clear_status:
            self.status_label.set_text("")

        if not self.detected_disk:
            self.info_label.set_markup(
                "<span size='small'>No WD My Passport detected. "
                "Connect your drive and click <b>Refresh</b>.</span>"
            )
            self.password_box.hide()
            self.unlock_button.hide()
            return

        model = GLib.markup_escape_text(self.detected_disk['model'])
        size = format_size(self.detected_disk['size_sectors'])
        size_suffix = f' ({size})' if size else ''

        if self.detected_disk['status'] == 'unlocked':
            self.info_label.set_markup(
                f"<span size='small'>✓ <b>{model}</b>{size_suffix} "
                f"is already unlocked.</span>"
            )
            self.password_box.hide()
            self.unlock_button.hide()
        else:
            self.info_label.set_markup(
                f"<span size='small'>🔒 <b>{model}</b> is locked. "
                f"Enter the password to unlock.</span>"
            )
            self.password_box.show_all()
            self.unlock_button.show()
            self.password_entry.grab_focus()

    def on_show_password_toggled(self, checkbox):
        self.password_entry.set_visibility(checkbox.get_active())

    def on_unlock_clicked(self, button):
        password = self.password_entry.get_text()

        if not password:
            self.show_status("Please enter a password", "error")
            return

        self.unlock_button.set_sensitive(False)
        self.password_entry.set_sensitive(False)
        self.spinner.start()
        self.show_status("Unlocking device...", "info")

        device = self.detected_disk['device'] if self.detected_disk else None
        thread = threading.Thread(target=self.unlock_device, args=(password, device))
        thread.daemon = True
        thread.start()

    def unlock_device(self, password, device):
        try:
            import shutil
            import tempfile

            wdpass_path = None
            if shutil.which('wdpass'):
                wdpass_path = shutil.which('wdpass')
            elif os.path.exists(os.path.expanduser('~/.local/bin/wdpass')):
                wdpass_path = os.path.expanduser('~/.local/bin/wdpass')
            else:
                try:
                    import sys
                    result = subprocess.run(
                        [sys.executable, '-m', 'py3_sg.wdpass', '--help'],
                        capture_output=True,
                        timeout=2
                    )
                    if result.returncode == 0 or 'usage' in result.stdout.decode().lower():
                        wdpass_path = f"{sys.executable}|||MODULE|||"
                except:
                    pass

            if not wdpass_path:
                GLib.idle_add(self.show_status, "✗ wdpass not found. Please run install.sh first.", "error")
                GLib.idle_add(self.reset_ui)
                return

            # device comes from sysfs (/dev/sdX); not user input, so safe to interpolate
            device_arg = f' -d {device}' if device else ''
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script:
                if '|||MODULE|||' in wdpass_path:
                    python_exe = wdpass_path.split('|||MODULE|||')[0]
                    script.write(f'''#!/bin/bash
echo "{password}" | {python_exe} -m py3_sg.wdpass -u{device_arg} 2>&1
exit ${{PIPESTATUS[1]}}
''')
                else:
                    script.write(f'''#!/bin/bash
echo "{password}" | {wdpass_path} -u{device_arg} 2>&1
exit ${{PIPESTATUS[1]}}
''')
                script_path = script.name

            os.chmod(script_path, 0o700)

            try:
                if shutil.which('pkexec'):
                    process = subprocess.Popen(
                        ['pkexec', '--disable-internal-agent', script_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:
                    process = subprocess.Popen(
                        ['sudo', '-S', script_path],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                stdout, stderr = process.communicate(timeout=30)
                full_output = stdout + stderr

                if process.returncode == 0 or "unlocked" in full_output.lower():
                    GLib.idle_add(self.show_status, "✓ Device unlocked successfully!", "success")
                    # Hide the form immediately so a stale-password retry can't fire
                    # during the window before sysfs reflects the new device size.
                    GLib.idle_add(self._hide_unlock_form)
                    # USB re-enumeration can take a few seconds on slower hosts.
                    GLib.timeout_add(3000, self._refresh_after_unlock)
                elif "cancelled" in full_output.lower() or "dismissed" in full_output.lower():
                    GLib.idle_add(self.show_status, "✗ Authentication cancelled", "error")
                elif "incorrect" in full_output.lower() or "wrong" in full_output.lower():
                    GLib.idle_add(self.show_status, "✗ Incorrect password", "error")
                elif "no device" in full_output.lower() or "not found" in full_output.lower():
                    GLib.idle_add(self.show_status, "✗ No WD device detected", "error")
                elif "root privileges" in full_output.lower():
                    GLib.idle_add(self.show_status, "✗ Authentication required", "error")
                else:
                    lines = [l.strip() for l in full_output.split('\n') if l.strip()]
                    error_msg = next((l for l in lines if l.startswith('[') or 'error' in l.lower()),
                                   lines[-1] if lines else "Operation failed")
                    GLib.idle_add(self.show_status, f"✗ {error_msg[:80]}", "error")

            finally:
                try:
                    os.unlink(script_path)
                except:
                    pass

        except subprocess.TimeoutExpired:
            GLib.idle_add(self.show_status, "✗ Operation timed out", "error")
        except Exception as e:
            GLib.idle_add(self.show_status, f"✗ Error: {str(e)[:80]}", "error")
        finally:
            GLib.idle_add(self.reset_ui)

    def _hide_unlock_form(self):
        self.password_box.hide()
        self.unlock_button.hide()

    def _refresh_after_unlock(self):
        self.refresh_state(clear_status=False)
        return False

    def show_status(self, message, status_type):
        if status_type == "success":
            markup = f"<span foreground='#2ecc71' weight='bold'>{message}</span>"
        elif status_type == "error":
            markup = f"<span foreground='#e74c3c' weight='bold'>{message}</span>"
        else:
            markup = f"<span foreground='#3498db'>{message}</span>"

        self.status_label.set_markup(markup)

    def reset_ui(self):
        self.spinner.stop()
        self.unlock_button.set_sensitive(True)
        self.password_entry.set_sensitive(True)


def main():
    win = WDUnlockerWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    win.spinner.stop()
    Gtk.main()


if __name__ == "__main__":
    main()
