#!/bin/bash
# ─────────────────────────────────────────────────────────────
# JFView Installer for Debian/Ubuntu/Mint
# ─────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="jfview"
INSTALL_DIR="/opt/jfview"
DESKTOP_FILE="/usr/share/applications/jfview.desktop"
BIN_LINK="/usr/local/bin/jfview"

echo "╔══════════════════════════════════════════╗"
echo "║       JFView Installer                   ║"
echo "║       Image Viewer & Editor for Linux     ║"
echo "╚══════════════════════════════════════════╝"
echo

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)."
    echo "Usage: sudo bash install.sh"
    exit 1
fi

echo "[1/4] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv python3-pyqt5 \
    python3-pil python3-numpy 2>/dev/null || true

echo "[2/4] Installing Python packages..."
pip3 install --break-system-packages Pillow numpy 2>/dev/null || \
    pip3 install Pillow numpy 2>/dev/null || true

echo "[3/4] Installing JFView to ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"
cp -r "${SCRIPT_DIR}/jfview" "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/run.sh" "${INSTALL_DIR}/"
chmod +x "${INSTALL_DIR}/run.sh"

# Create launcher script
cat > "${BIN_LINK}" << 'LAUNCHER'
#!/bin/bash
cd /opt/jfview
python3 -m jfview.main "$@"
LAUNCHER
chmod +x "${BIN_LINK}"

echo "[4/4] Installing desktop entry..."
cat > "${DESKTOP_FILE}" << DESKTOP
[Desktop Entry]
Name=JFView
Comment=Image Viewer and Editor
Exec=/usr/local/bin/jfview %f
Icon=image-viewer
Terminal=false
Type=Application
Categories=Graphics;Viewer;RasterGraphics;
MimeType=image/png;image/jpeg;image/bmp;image/gif;image/tiff;image/webp;image/svg+xml;
StartupWMClass=jfview
DESKTOP

# Update desktop database
update-desktop-database /usr/share/applications/ 2>/dev/null || true

echo
echo "✓ JFView installed successfully!"
echo
echo "You can now:"
echo "  • Run from terminal:  jfview"
echo "  • Open a file:        jfview /path/to/image.png"
echo "  • Find it in your application menu under Graphics"
echo
echo "To uninstall: sudo bash ${SCRIPT_DIR}/uninstall.sh"

