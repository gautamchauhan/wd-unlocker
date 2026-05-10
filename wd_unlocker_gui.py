#!/usr/bin/env python3
"""
WD Unlocker - GUI application for unlocking Western Digital hard disks on Linux
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import subprocess
import threading

class WDUnlockerWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="WD Disk Unlocker")
        self.set_border_width(20)
        self.set_default_size(400, 250)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.add(vbox)
        
        # Header with icon and title
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_halign(Gtk.Align.CENTER)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large' weight='bold'>Western Digital Disk Unlocker</span>")
        header_box.pack_start(title_label, False, False, 0)
        vbox.pack_start(header_box, False, False, 0)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup("<span size='small'>Enter your WD disk password to unlock</span>")
        info_label.set_halign(Gtk.Align.CENTER)
        vbox.pack_start(info_label, False, False, 0)
        
        # Password entry
        password_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        password_label = Gtk.Label(label="Password:")
        password_label.set_width_chars(10)
        password_box.pack_start(password_label, False, False, 0)
        
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.set_invisible_char("●")
        self.password_entry.set_placeholder_text("Enter your disk password")
        self.password_entry.set_activates_default(True)
        password_box.pack_start(self.password_entry, True, True, 0)
        
        # Show/hide password toggle
        self.show_password_check = Gtk.CheckButton(label="Show")
        self.show_password_check.connect("toggled", self.on_show_password_toggled)
        password_box.pack_start(self.show_password_check, False, False, 0)
        
        vbox.pack_start(password_box, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_line_wrap(True)
        self.status_label.set_max_width_chars(50)
        vbox.pack_start(self.status_label, False, False, 0)
        
        # Progress spinner
        self.spinner = Gtk.Spinner()
        vbox.pack_start(self.spinner, False, False, 0)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.CENTER)
        
        self.unlock_button = Gtk.Button(label="Unlock")
        self.unlock_button.set_size_request(120, 35)
        self.unlock_button.connect("clicked", self.on_unlock_clicked)
        self.unlock_button.set_can_default(True)
        self.unlock_button.get_style_context().add_class("suggested-action")
        button_box.pack_start(self.unlock_button, False, False, 0)
        
        close_button = Gtk.Button(label="Close")
        close_button.set_size_request(120, 35)
        close_button.connect("clicked", lambda x: self.destroy())
        button_box.pack_start(close_button, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # Set default button
        self.unlock_button.grab_default()
        
    def on_show_password_toggled(self, checkbox):
        self.password_entry.set_visibility(checkbox.get_active())
        
    def on_unlock_clicked(self, button):
        password = self.password_entry.get_text()
        
        if not password:
            self.show_status("Please enter a password", "error")
            return
            
        # Disable button and show spinner
        self.unlock_button.set_sensitive(False)
        self.password_entry.set_sensitive(False)
        self.spinner.start()
        self.show_status("Unlocking device...", "info")
        
        # Run unlock in separate thread
        thread = threading.Thread(target=self.unlock_device, args=(password,))
        thread.daemon = True
        thread.start()
        
    def unlock_device(self, password):
        try:
            import os
            import shutil
            import tempfile
            
            # Find wdpass command - try multiple methods
            wdpass_path = None
            
            # Method 1: Check if wdpass is in PATH
            if shutil.which('wdpass'):
                wdpass_path = shutil.which('wdpass')
            # Method 2: Direct path in user's local bin
            elif os.path.exists(os.path.expanduser('~/.local/bin/wdpass')):
                wdpass_path = os.path.expanduser('~/.local/bin/wdpass')
            # Method 3: Try using python module directly
            else:
                # Try to use py3_sg module directly
                try:
                    import sys
                    result = subprocess.run(
                        [sys.executable, '-m', 'py3_sg.wdpass', '--help'],
                        capture_output=True,
                        timeout=2
                    )
                    if result.returncode == 0 or 'usage' in result.stdout.decode().lower():
                        wdpass_path = f"{sys.executable}|||MODULE|||"  # Special marker
                except:
                    pass
            
            if not wdpass_path:
                GLib.idle_add(self.show_status, "✗ wdpass not found. Please run install.sh first.", "error")
                GLib.idle_add(self.reset_ui)
                return
            
            # Create a temporary script to handle password input
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script:
                if '|||MODULE|||' in wdpass_path:
                    # Use python module directly
                    python_exe = wdpass_path.split('|||MODULE|||')[0]
                    script.write(f'''#!/bin/bash
echo "{password}" | {python_exe} -m py3_sg.wdpass -u 2>&1
exit ${{PIPESTATUS[1]}}
''')
                else:
                    script.write(f'''#!/bin/bash
echo "{password}" | {wdpass_path} -u 2>&1
exit ${{PIPESTATUS[1]}}
''')
                script_path = script.name
            
            os.chmod(script_path, 0o700)
            
            try:
                # Use pkexec for graphical sudo prompt
                if shutil.which('pkexec'):
                    process = subprocess.Popen(
                        ['pkexec', '--disable-internal-agent', script_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:
                    # Fallback to regular sudo
                    process = subprocess.Popen(
                        ['sudo', '-S', script_path],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                
                stdout, stderr = process.communicate(timeout=30)
                
                # Update UI in main thread
                full_output = stdout + stderr
                
                if process.returncode == 0 or "unlocked" in full_output.lower():
                    GLib.idle_add(self.show_status, "✓ Device unlocked successfully!", "success")
                elif "cancelled" in full_output.lower() or "dismissed" in full_output.lower():
                    GLib.idle_add(self.show_status, "✗ Authentication cancelled", "error")
                elif "incorrect" in full_output.lower() or "wrong" in full_output.lower():
                    GLib.idle_add(self.show_status, "✗ Incorrect password", "error")
                elif "no device" in full_output.lower() or "not found" in full_output.lower():
                    GLib.idle_add(self.show_status, "✗ No WD device detected", "error")
                elif "root privileges" in full_output.lower():
                    GLib.idle_add(self.show_status, "✗ Authentication required", "error")
                else:
                    # Try to extract meaningful error
                    lines = [l.strip() for l in full_output.split('\n') if l.strip()]
                    error_msg = next((l for l in lines if l.startswith('[') or 'error' in l.lower()), 
                                   lines[-1] if lines else "Operation failed")
                    GLib.idle_add(self.show_status, f"✗ {error_msg[:80]}", "error")
                    
            finally:
                # Clean up temp script
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
