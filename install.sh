#!/bin/bash

# WD Unlocker Installation Script for Ubuntu
# This script installs dependencies and sets up the WD Unlocker application

set -e

echo "======================================"
echo "WD Unlocker Installation Script"
echo "======================================"
echo ""

# Check if running on Ubuntu/Debian
if ! command -v apt &> /dev/null; then
    echo "Error: This script requires apt package manager (Ubuntu/Debian)"
    exit 1
fi

# Update package list
echo "[1/5] Updating package list..."
sudo apt update

# Install Python and required packages
echo "[2/5] Installing Python dependencies..."
sudo apt install -y python3 python3-dev python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 lsscsi sg3-utils pipx

# Ensure pipx is set up
echo "[3/5] Setting up pipx..."
pipx ensurepath 2>/dev/null || true

# Install wdpass
echo "[4/5] Installing wdpass utility..."
if pipx list 2>/dev/null | grep -q "wdpass"; then
    # After an OS major upgrade (e.g. Ubuntu 25.10 → 26.04), the pipx venv's
    # Python symlink can point to an interpreter that no longer exists. Detect
    # that and rebuild the venv instead of trying to upgrade in place.
    PIPX_HOME_DIR="${PIPX_HOME:-$HOME/.local/share/pipx}"
    WDPASS_VENV_PY="$PIPX_HOME_DIR/venvs/wdpass/bin/python"
    if [ ! -x "$WDPASS_VENV_PY" ] || ! "$WDPASS_VENV_PY" --version &>/dev/null; then
        echo "wdpass venv has a broken Python interpreter, reinstalling..."
        pipx reinstall wdpass || pipx install wdpass --force
    else
        echo "wdpass already installed, upgrading..."
        pipx upgrade wdpass 2>/dev/null || pipx install wdpass --force
    fi
else
    pipx install wdpass
fi

# Make the GUI script executable
echo "[5/5] Setting up WD Unlocker GUI..."

# Get the directory where install.sh is located (works even if run from different directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR/wd_unlocker_gui.py"

# Create desktop entry
DESKTOP_FILE="$HOME/.local/share/applications/wd-unlocker.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=WD Disk Unlocker
Comment=Unlock Western Digital Hard Disks
Exec=$SCRIPT_DIR/wd_unlocker_gui.py
Icon=drive-harddisk
Terminal=false
Type=Application
Categories=System;Utility;
Keywords=western;digital;unlock;disk;drive;
EOF

echo ""
echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo ""
echo "You can now run the application by:"
echo "  1. Running: ./wd_unlocker_gui.py"
echo "  2. Searching for 'WD Disk Unlocker' in your applications menu"
echo ""
echo "Note: You will need to enter your sudo password when unlocking a disk."
echo ""
