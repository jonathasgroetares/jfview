# JFView - Lightweight Image Viewer & Simple Editor

**JFView** is a fast, Debian/Ubuntu/Mint-compatible desktop image viewer and editor inspired by IrfanView. It is designed for everyday viewing, quick manipulation, clipboard workflows, filters/effects, and stitching panoramas.

---

## Features

- **Format Support (Open & Save)**:
  - Supports PNG, JPEG/JPG, BMP, GIF, TIFF, WebP, ICO, PPM/PGM/PBM.
  - Safe format conversions and adaptive palette/quality handling.
- **Clipboard Integration**:
  - Paste directly from clipboard (`Ctrl+V` or Edit > Paste).
  - Automatically adjusts the canvas/workspace to the dimensions of the pasted image.
  - Copy whole image or active crop selection to clipboard (`Ctrl+C`).
  - Save pasted images immediately with `Ctrl+S` or `Ctrl+Shift+S`.
- **Image Editing & Transformations**:
  - **Crop Mode (`C`)**: Draw a crop rectangle directly on canvas and crop with `Ctrl+Shift+X`.
  - **Resize (`Ctrl+R`)**: Resampling filters (Lanczos, Bicubic, Bilinear, Nearest), aspect ratio locking, percentage scaling.
  - **Rotation & Flipping**: Rotate 90° CW, 90° CCW, 180°, flip horizontally (`H`), flip vertically (`V`).
  - **Undo / Redo (`Ctrl+Z` / `Ctrl+Y`)**: Multi-level history.
- **Effects & Filters**:
  - **Grayscale**
  - **Negative (Invert)**
  - **Border / Edge Detection** (Contours line extraction)
  - **Nanquim (India Ink)**: High-contrast comic/ink art filter combining edge detection and dark thresholding
  - **Sepia tone**
  - **Emboss & Contour**
  - **Sharpen & Blur**
  - **Posterize & Solarize**
  - **Auto Contrast & Histogram Equalization**
  - **Interactive Brightness & Contrast adjustment dialog**
- **Panoramic Stitching (`Ctrl+Shift+P` / Tools > Create Panorama...)**:
  - Combine multiple images in **Horizontal** (side-by-side) or **Vertical** (top-to-bottom) layout.
  - Add, remove, and reorder images up/down.
  - Automatic size matching (resizes dimensions proportionally to match tallest or widest photo).
  - Configurable pixel spacing between joined images.

---

## Installation & Running

### Requirements
- Python 3.8+
- PyQt5 (`python3-pyqt5` or `pip install PyQt5`)
- Pillow (`python3-pil` or `pip install Pillow`)
- NumPy (`python3-numpy` or `pip install numpy`)

### Quick Start
You can launch JFView directly from the project folder:
```bash
./run.sh
# or open an image directly:
./run.sh /path/to/image.png
```

Or run via python module:
```bash
python3 -m jfview.main
```

### System-wide Installation (Debian / Ubuntu / Mint)
Run the included installer with sudo:
```bash
sudo ./install.sh
```
This installs `jfview` to `/opt/jfview`, creates `/usr/local/bin/jfview`, and registers the desktop shortcut with file associations so you can right-click any image in your file manager and choose "Open With JFView".

To uninstall:
```bash
sudo ./uninstall.sh
```

---

## Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl+O` | Open image |
| `Ctrl+S` | Save image |
| `Ctrl+Shift+S` | Save As... |
| `Ctrl+V` | Paste image from clipboard (auto-resizes workspace) |
| `Ctrl+C` | Copy image or selection to clipboard |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `C` | Toggle Crop Selection tool |
| `Ctrl+Shift+X` | Execute Crop to Selection |
| `Ctrl+R` | Resize image dialog |
| `Ctrl+Right` | Rotate 90° clockwise |
| `Ctrl+Left` | Rotate 90° counter-clockwise |
| `H` / `V` | Flip horizontally / vertically |
| `+` / `-` (or Mouse Wheel) | Zoom in / Zoom out |
| `Ctrl+0` | Fit image to window |
| `Ctrl+1` | 100% Actual size |
| `Ctrl+Shift+P` | Create Panorama |

## 🤖 Acknowledgements & AI Stack

This project was built using **vibe coding** methodologies powered by the following AI models and developer tools:

* **IDE / Workspace:** [Antigravity IDE](https://antigravity.dev)
* **Core Models:**
  * Anthropic Claude (Sonnet & Opus 4.6)
  * Google Gemini (3.8 Flash)