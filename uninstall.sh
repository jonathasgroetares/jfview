#!/bin/bash
# JFView Uninstaller
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)."
    exit 1
fi

echo "Uninstalling JFView..."

rm -rf /opt/jfview
rm -f /usr/local/bin/jfview
rm -f /usr/share/applications/jfview.desktop
update-desktop-database /usr/share/applications/ 2>/dev/null || true

echo "✓ JFView uninstalled."

