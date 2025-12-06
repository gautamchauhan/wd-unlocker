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

# Install py3_sg (wdpass) - inject into a dedicated environment
echo "[4/5] Installing wdpass utility..."
if pipx list 2>/dev/null | grep -q "py3.sg"; then
    echo "wdpass already installed, upgrading..."
    pipx upgrade py3-sg 2>/dev/null || pipx install py3-sg --force
else
    # Install in a way that exposes the wdpass command
    pipx install py3-sg --include-deps
fi

# Make the GUI script executable
echo "[5/5] Setting up WD Unlocker GUI..."
chmod +x wd_unlocker_gui.py

# Create desktop entry
DESKTOP_FILE="$HOME/.local/share/applications/wd-unlocker.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=WD Disk Unlocker
Comment=Unlock Western Digital Hard Disks
Exec=$(pwd)/wd_unlocker_gui.py
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
