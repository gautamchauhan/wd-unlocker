# WD Unlocker for Ubuntu

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.x-blue.svg)

A simple GUI application to unlock Western Digital hard disks on Ubuntu/Linux. This tool provides a user-friendly interface for the `wdpass` utility, eliminating the need for the Windows-only WD Unlocker executable.

## Features

- 🖥️ Clean and intuitive GTK3 GUI
- 🔐 Secure password entry with show/hide toggle
- ⚡ Quick unlock with visual feedback
- 🐧 Native Linux application
- 💻 Works on Ubuntu 25.10 and other Linux distributions

## Prerequisites

- Ubuntu/Debian-based Linux distribution
- Python 3
- Sudo access (required for unlocking operations)

## Installation

### Quick Install

Run the installation script:

```bash
chmod +x install.sh
./install.sh
```

The script will:
1. Update your package list
2. Install all required dependencies
3. Install pipx and the wdpass utility
4. Set up the GUI application
5. Create a desktop entry for easy access

### Manual Installation

If you prefer to install manually:

```bash
# Update system
sudo apt update

# Install dependencies
sudo apt install python3 python3-dev python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 lsscsi sg3-utils

# Install pipx
sudo apt install pipx
pipx ensurepath

# Install wdpass
pipx install wdpass

# Make GUI executable
chmod +x wd_unlocker_gui.py
```

## Usage

### Running the Application

**Option 1: From Terminal**
```bash
./wd_unlocker_gui.py
```

**Option 2: From Applications Menu**
After installation, search for "WD Disk Unlocker" in your applications menu.

### Unlocking Your Disk

1. Launch the application
2. Enter your WD disk password
3. Click "Unlock"
4. Enter your sudo password when prompted
5. Wait for the success message

## Command Line Alternative

If you prefer using the command line:

```bash
sudo wdpass -u
```

## Troubleshooting

### "wdpass not found" Error
Ensure pipx is installed and in your PATH:
```bash
pipx ensurepath
source ~/.bashrc
```

### Permission Denied
Make sure the script is executable:
```bash
chmod +x wd_unlocker_gui.py
```

### GTK Warnings
Install the required GTK packages:
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

### Disk Not Detected
Ensure your WD disk is connected and recognized:
```bash
lsscsi
```

### PEP 668 Error (Ubuntu 23.10+)
The install script uses pipx to avoid this issue. If you still encounter it, the script will handle it automatically.

## Technical Details

This application is a GTK3-based frontend for the `wdpass` utility from the `py3_sg` package. It uses:

- **Python 3**: Core programming language
- **GTK 3**: GUI framework
- **pipx**: Python application installer (isolated environments)
- **wdpass**: Western Digital password utility
- **sg3-utils**: SCSI device utilities

## Security Note

- Passwords are handled securely and not stored
- The application requires sudo access to communicate with disk hardware
- Always use strong passwords for your WD disks

## Author

**Gautam Chauhan**
- Email: thisisgautamchauhan@gmail.com
- GitHub: [@gautam-chauhan](https://github.com/gautam-chauhan)

## Credits

- **wdpass utility**: Part of py3_sg package
- **GUI Application**: Created for Ubuntu users who need WD disk unlock functionality

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Support

For issues with:
- **GUI Application**: Open an issue in this repository
- **wdpass utility**: Refer to the py3_sg documentation
- **WD Hardware**: Contact Western Digital support

## Acknowledgments

- Thanks to all contributors who help improve this project
- Inspired by the need for a native Linux solution for WD disk unlocking
