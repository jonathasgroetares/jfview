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
rm -f /usr/share/pixmaps/jfview.png
for size in 16 24 32 48 64 128 256; do
    rm -f "/usr/share/icons/hicolor/${size}x${size}/apps/jfview.png"
done

update-desktop-database /usr/share/applications/ 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo "✓ JFView uninstalled."
