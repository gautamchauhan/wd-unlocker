#!/bin/bash

# Uninstall script for WD Unlocker

echo "======================================"
echo "WD Unlocker Uninstall Script"
echo "======================================"
echo ""

# Remove desktop entry
if [ -f "$HOME/.local/share/applications/wd-unlocker.desktop" ]; then
    echo "Removing desktop entry..."
    rm "$HOME/.local/share/applications/wd-unlocker.desktop"
fi

# Option to remove wdpass
read -p "Do you want to remove wdpass utility? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pipx uninstall wdpass 2>/dev/null || echo "wdpass not found in pipx"
    echo "wdpass removed."
fi

echo ""
echo "WD Unlocker has been uninstalled."
echo "Note: System dependencies (python3-gi, etc.) were not removed."
echo ""
