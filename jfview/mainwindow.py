"""Main application window for JFView."""

import os
import io

from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QMessageBox, QLabel,
    QToolBar, QStatusBar, QApplication, QMenu, QInputDialog,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QActionGroup, QSizePolicy,
)
from PyQt5.QtCore import Qt, QRect, QByteArray, QBuffer, QIODevice, QSize
from PyQt5.QtGui import QPixmap, QImage, QKeySequence, QIcon, QPainter

from PIL import Image

from jfview.canvas import ImageCanvas
from jfview.effects import ImageEffects
from jfview.dialogs import (
    ResizeDialog,
    PanoramaDialog,
    BrightnessContrastDialog,
    NewImageDialog,
)


# Supported formats
OPEN_FORMATS = (
    "All Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif *.webp *.ico *.ppm *.pgm *.pbm *.svg);;"
    "PNG (*.png);;"
    "JPEG (*.jpg *.jpeg);;"
    "BMP (*.bmp);;"
    "GIF (*.gif);;"
    "TIFF (*.tiff *.tif);;"
    "WebP (*.webp);;"
    "ICO (*.ico);;"
    "PPM (*.ppm *.pgm *.pbm);;"
    "All Files (*)"
)

SAVE_FORMATS = (
    "PNG (*.png);;"
    "JPEG (*.jpg *.jpeg);;"
    "BMP (*.bmp);;"
    "TIFF (*.tiff *.tif);;"
    "WebP (*.webp);;"
    "ICO (*.ico);;"
    "PPM (*.ppm);;"
    "GIF (*.gif)"
)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("JFView - Image Viewer & Editor")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        self._current_file = None
        self._modified = False
        self._undo_stack = []
        self._redo_stack = []
        self._max_undo = 30

        # Central widget
        self._canvas = ImageCanvas(self)
        self.setCentralWidget(self._canvas)

        # Connect canvas signals
        self._canvas.selection_changed.connect(self._on_selection_changed)
        self._canvas.zoom_changed.connect(self._on_zoom_changed)
        self._canvas.mouse_pos_changed.connect(self._on_mouse_pos_changed)

        # Status bar labels
        self._status_file = QLabel("No file")
        self._status_size = QLabel("")
        self._status_zoom = QLabel("100%")
        self._status_pos = QLabel("")
        self._status_selection = QLabel("")

        # Build UI
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()

        self._update_title()
        self._update_actions()

    # ── PIL ↔ Qt Conversion ──────────────────────────────────────

    @staticmethod
    def pil_to_pixmap(pil_image: Image.Image) -> QPixmap:
        """Convert PIL Image to QPixmap."""
        if pil_image.mode == "RGBA":
            data = pil_image.tobytes("raw", "RGBA")
            qimg = QImage(data, pil_image.width, pil_image.height,
                          pil_image.width * 4, QImage.Format_RGBA8888)
        elif pil_image.mode == "RGB":
            data = pil_image.tobytes("raw", "RGB")
            qimg = QImage(data, pil_image.width, pil_image.height,
                          pil_image.width * 3, QImage.Format_RGB888)
        elif pil_image.mode == "L":
            data = pil_image.tobytes("raw", "L")
            qimg = QImage(data, pil_image.width, pil_image.height,
                          pil_image.width, QImage.Format_Grayscale8)
        else:
            pil_image = pil_image.convert("RGBA")
            data = pil_image.tobytes("raw", "RGBA")
            qimg = QImage(data, pil_image.width, pil_image.height,
                          pil_image.width * 4, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimg.copy())

    @staticmethod
    def pixmap_to_pil(pixmap: QPixmap) -> Image.Image:
        """Convert QPixmap to PIL Image."""
        qimg = pixmap.toImage().convertToFormat(QImage.Format_RGBA8888)
        width = qimg.width()
        height = qimg.height()

        ptr = qimg.bits()
        ptr.setsize(height * width * 4)
        return Image.frombytes("RGBA", (width, height), bytes(ptr), "raw", "RGBA")

    # ── Actions ──────────────────────────────────────────────────

    def _create_actions(self):
        """Create all menu/toolbar actions."""

        # File actions
        self._act_new = QAction("&New", self)
        self._act_new.setShortcut(QKeySequence.New)
        self._act_new.triggered.connect(self._on_new)

        self._act_open = QAction("&Open...", self)
        self._act_open.setShortcut(QKeySequence.Open)
        self._act_open.triggered.connect(self._on_open)

        self._act_save = QAction("&Save", self)
        self._act_save.setShortcut(QKeySequence.Save)
        self._act_save.triggered.connect(self._on_save)

        self._act_save_as = QAction("Save &As...", self)
        self._act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._act_save_as.triggered.connect(self._on_save_as)

        self._act_quit = QAction("&Quit", self)
        self._act_quit.setShortcut(QKeySequence.Quit)
        self._act_quit.triggered.connect(self.close)

        # Edit actions
        self._act_undo = QAction("&Undo", self)
        self._act_undo.setShortcut(QKeySequence.Undo)
        self._act_undo.triggered.connect(self._on_undo)

        self._act_redo = QAction("&Redo", self)
        self._act_redo.setShortcut(QKeySequence.Redo)
        self._act_redo.triggered.connect(self._on_redo)

        self._act_copy = QAction("&Copy", self)
        self._act_copy.setShortcut(QKeySequence.Copy)
        self._act_copy.triggered.connect(self._on_copy)

        self._act_paste = QAction("&Paste", self)
        self._act_paste.setShortcut(QKeySequence.Paste)
        self._act_paste.triggered.connect(self._on_paste)

        self._act_select_all = QAction("Select &All", self)
        self._act_select_all.setShortcut(QKeySequence.SelectAll)
        self._act_select_all.triggered.connect(self._on_select_all)

        # View actions
        self._act_zoom_in = QAction("Zoom &In", self)
        self._act_zoom_in.setShortcut(QKeySequence.ZoomIn)
        self._act_zoom_in.triggered.connect(self._canvas.zoom_in)

        self._act_zoom_out = QAction("Zoom &Out", self)
        self._act_zoom_out.setShortcut(QKeySequence.ZoomOut)
        self._act_zoom_out.triggered.connect(self._canvas.zoom_out)

        self._act_zoom_fit = QAction("&Fit in Window", self)
        self._act_zoom_fit.setShortcut(QKeySequence("Ctrl+0"))
        self._act_zoom_fit.triggered.connect(self._canvas.fit_in_view)

        self._act_zoom_100 = QAction("&Actual Size (100%)", self)
        self._act_zoom_100.setShortcut(QKeySequence("Ctrl+1"))
        self._act_zoom_100.triggered.connect(self._canvas.zoom_original)

        # Image actions
        self._act_crop = QAction("&Crop Mode", self)
        self._act_crop.setShortcut(QKeySequence("C"))
        self._act_crop.setCheckable(True)
        self._act_crop.triggered.connect(self._on_toggle_crop)

        self._act_do_crop = QAction("Crop to &Selection", self)
        self._act_do_crop.setShortcut(QKeySequence("Ctrl+Shift+X"))
        self._act_do_crop.triggered.connect(self._on_crop)

        self._act_resize = QAction("&Resize...", self)
        self._act_resize.setShortcut(QKeySequence("Ctrl+R"))
        self._act_resize.triggered.connect(self._on_resize)

        self._act_rotate_cw = QAction("Rotate &90° CW", self)
        self._act_rotate_cw.setShortcut(QKeySequence("Ctrl+Right"))
        self._act_rotate_cw.triggered.connect(lambda: self._on_rotate(90))

        self._act_rotate_ccw = QAction("Rotate 90° CC&W", self)
        self._act_rotate_ccw.setShortcut(QKeySequence("Ctrl+Left"))
        self._act_rotate_ccw.triggered.connect(lambda: self._on_rotate(-90))

        self._act_rotate_180 = QAction("Rotate &180°", self)
        self._act_rotate_180.triggered.connect(lambda: self._on_rotate(180))

        self._act_flip_h = QAction("Flip &Horizontal", self)
        self._act_flip_h.setShortcut(QKeySequence("H"))
        self._act_flip_h.triggered.connect(self._on_flip_h)

        self._act_flip_v = QAction("Flip &Vertical", self)
        self._act_flip_v.setShortcut(QKeySequence("V"))
        self._act_flip_v.triggered.connect(self._on_flip_v)

        # Effect actions
        self._act_grayscale = QAction("&Grayscale", self)
        self._act_grayscale.triggered.connect(
            lambda: self._apply_effect(ImageEffects.grayscale)
        )

        self._act_negative = QAction("&Negative (Invert)", self)
        self._act_negative.triggered.connect(
            lambda: self._apply_effect(ImageEffects.negative)
        )

        self._act_edge = QAction("&Edge Detection", self)
        self._act_edge.triggered.connect(
            lambda: self._apply_effect(ImageEffects.edge_detection)
        )

        self._act_nanquim = QAction("Nan&quim (Ink)", self)
        self._act_nanquim.triggered.connect(
            lambda: self._apply_effect(ImageEffects.nanquim)
        )

        self._act_sepia = QAction("&Sepia", self)
        self._act_sepia.triggered.connect(
            lambda: self._apply_effect(ImageEffects.sepia)
        )

        self._act_emboss = QAction("E&mboss", self)
        self._act_emboss.triggered.connect(
            lambda: self._apply_effect(ImageEffects.emboss)
        )

        self._act_sharpen = QAction("S&harpen", self)
        self._act_sharpen.triggered.connect(
            lambda: self._apply_effect(ImageEffects.sharpen)
        )

        self._act_blur = QAction("&Blur", self)
        self._act_blur.triggered.connect(
            lambda: self._apply_effect(ImageEffects.blur)
        )

        self._act_contour = QAction("&Contour", self)
        self._act_contour.triggered.connect(
            lambda: self._apply_effect(ImageEffects.contour)
        )

        self._act_posterize = QAction("&Posterize", self)
        self._act_posterize.triggered.connect(
            lambda: self._apply_effect(ImageEffects.posterize)
        )

        self._act_solarize = QAction("So&larize", self)
        self._act_solarize.triggered.connect(
            lambda: self._apply_effect(ImageEffects.solarize)
        )

        self._act_auto_contrast = QAction("&Auto Contrast", self)
        self._act_auto_contrast.triggered.connect(
            lambda: self._apply_effect(ImageEffects.auto_contrast)
        )

        self._act_equalize = QAction("&Equalize Histogram", self)
        self._act_equalize.triggered.connect(
            lambda: self._apply_effect(ImageEffects.equalize)
        )

        self._act_brightness_contrast = QAction("Brightness / Co&ntrast...", self)
        self._act_brightness_contrast.triggered.connect(
            self._on_brightness_contrast
        )

        # Tools actions
        self._act_panorama = QAction("Create &Panorama...", self)
        self._act_panorama.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self._act_panorama.triggered.connect(self._on_panorama)

        # Help
        self._act_about = QAction("&About JFView", self)
        self._act_about.triggered.connect(self._on_about)

    def _create_menus(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self._act_new)
        file_menu.addAction(self._act_open)
        file_menu.addSeparator()
        file_menu.addAction(self._act_save)
        file_menu.addAction(self._act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self._act_quit)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self._act_undo)
        edit_menu.addAction(self._act_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self._act_copy)
        edit_menu.addAction(self._act_paste)
        edit_menu.addSeparator()
        edit_menu.addAction(self._act_select_all)

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self._act_zoom_in)
        view_menu.addAction(self._act_zoom_out)
        view_menu.addAction(self._act_zoom_fit)
        view_menu.addAction(self._act_zoom_100)

        # Image menu
        image_menu = menubar.addMenu("&Image")
        image_menu.addAction(self._act_crop)
        image_menu.addAction(self._act_do_crop)
        image_menu.addSeparator()
        image_menu.addAction(self._act_resize)
        image_menu.addSeparator()

        rotate_menu = image_menu.addMenu("&Rotate")
        rotate_menu.addAction(self._act_rotate_cw)
        rotate_menu.addAction(self._act_rotate_ccw)
        rotate_menu.addAction(self._act_rotate_180)

        image_menu.addAction(self._act_flip_h)
        image_menu.addAction(self._act_flip_v)

        # Effects menu
        effects_menu = menubar.addMenu("E&ffects")
        effects_menu.addAction(self._act_grayscale)
        effects_menu.addAction(self._act_negative)
        effects_menu.addAction(self._act_sepia)
        effects_menu.addSeparator()
        effects_menu.addAction(self._act_edge)
        effects_menu.addAction(self._act_nanquim)
        effects_menu.addAction(self._act_contour)
        effects_menu.addAction(self._act_emboss)
        effects_menu.addSeparator()
        effects_menu.addAction(self._act_sharpen)
        effects_menu.addAction(self._act_blur)
        effects_menu.addAction(self._act_posterize)
        effects_menu.addAction(self._act_solarize)
        effects_menu.addSeparator()
        effects_menu.addAction(self._act_auto_contrast)
        effects_menu.addAction(self._act_equalize)
        effects_menu.addAction(self._act_brightness_contrast)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self._act_panorama)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self._act_about)

    def _create_toolbar(self):
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addAction(self._act_new)
        toolbar.addAction(self._act_open)
        toolbar.addAction(self._act_save)
        toolbar.addSeparator()
        toolbar.addAction(self._act_undo)
        toolbar.addAction(self._act_redo)
        toolbar.addSeparator()
        toolbar.addAction(self._act_copy)
        toolbar.addAction(self._act_paste)
        toolbar.addSeparator()
        toolbar.addAction(self._act_crop)
        toolbar.addAction(self._act_do_crop)
        toolbar.addSeparator()
        toolbar.addAction(self._act_zoom_in)
        toolbar.addAction(self._act_zoom_out)
        toolbar.addAction(self._act_zoom_fit)
        toolbar.addAction(self._act_zoom_100)
        toolbar.addSeparator()
        toolbar.addAction(self._act_rotate_cw)
        toolbar.addAction(self._act_rotate_ccw)
        toolbar.addAction(self._act_flip_h)
        toolbar.addAction(self._act_flip_v)

    def _create_statusbar(self):
        """Create the status bar."""
        statusbar = self.statusBar()
        statusbar.addWidget(self._status_file, 1)
        statusbar.addPermanentWidget(self._status_selection)
        statusbar.addPermanentWidget(self._status_pos)
        statusbar.addPermanentWidget(self._status_size)
        statusbar.addPermanentWidget(self._status_zoom)

    # ── State Updates ────────────────────────────────────────────

    def _update_title(self):
        mod = " *" if self._modified else ""
        if self._current_file:
            name = os.path.basename(self._current_file)
            self.setWindowTitle(f"{name}{mod} - JFView")
        else:
            self.setWindowTitle(f"JFView - Image Viewer & Editor{mod}")

    def _update_actions(self):
        has_image = self._canvas.has_image()
        self._act_save.setEnabled(has_image)
        self._act_save_as.setEnabled(has_image)
        self._act_copy.setEnabled(has_image)
        self._act_crop.setEnabled(has_image)
        self._act_do_crop.setEnabled(has_image and not self._canvas.get_selection_rect().isEmpty())
        self._act_resize.setEnabled(has_image)
        self._act_rotate_cw.setEnabled(has_image)
        self._act_rotate_ccw.setEnabled(has_image)
        self._act_rotate_180.setEnabled(has_image)
        self._act_flip_h.setEnabled(has_image)
        self._act_flip_v.setEnabled(has_image)
        self._act_zoom_in.setEnabled(has_image)
        self._act_zoom_out.setEnabled(has_image)
        self._act_zoom_fit.setEnabled(has_image)
        self._act_zoom_100.setEnabled(has_image)
        self._act_select_all.setEnabled(has_image)

        # Effects
        for act in [
            self._act_grayscale, self._act_negative, self._act_edge,
            self._act_nanquim, self._act_sepia, self._act_emboss,
            self._act_sharpen, self._act_blur, self._act_contour,
            self._act_posterize, self._act_solarize,
            self._act_auto_contrast, self._act_equalize,
            self._act_brightness_contrast,
        ]:
            act.setEnabled(has_image)

        # Undo/Redo
        self._act_undo.setEnabled(len(self._undo_stack) > 0)
        self._act_redo.setEnabled(len(self._redo_stack) > 0)

    def _update_status(self):
        pixmap = self._canvas.get_pixmap()
        if pixmap:
            self._status_size.setText(
                f"  {pixmap.width()} × {pixmap.height()} px  "
            )
        else:
            self._status_size.setText("")

        if self._current_file:
            self._status_file.setText(f"  {self._current_file}  ")
        else:
            self._status_file.setText("  (unsaved)  ")

    def _set_image(self, pixmap: QPixmap, push_undo=True):
        """Set a new image on the canvas."""
        if push_undo and self._canvas.has_image():
            old_pixmap = self._canvas.get_pixmap()
            self._undo_stack.append(old_pixmap)
            if len(self._undo_stack) > self._max_undo:
                self._undo_stack.pop(0)
            self._redo_stack.clear()

        self._canvas.set_image(pixmap)
        self._modified = True
        self._update_title()
        self._update_actions()
        self._update_status()

    # ── Signal Handlers ──────────────────────────────────────────

    def _on_selection_changed(self, rect: QRect):
        if not rect.isEmpty():
            self._status_selection.setText(
                f"  Selection: {rect.width()}×{rect.height()} at ({rect.x()},{rect.y()})  "
            )
        else:
            self._status_selection.setText("")
        self._update_actions()

    def _on_zoom_changed(self, factor: float):
        self._status_zoom.setText(f"  {int(factor * 100)}%  ")

    def _on_mouse_pos_changed(self, x: int, y: int):
        self._status_pos.setText(f"  ({x}, {y})  ")

    # ── File Operations ──────────────────────────────────────────

    def open_file(self, filepath: str):
        """Open an image file."""
        try:
            pixmap = QPixmap(filepath)
            if pixmap.isNull():
                raise ValueError("Could not load image")
            self._current_file = filepath
            self._modified = False
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._set_image(pixmap, push_undo=False)
            self._canvas.fit_in_view()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file:\n{e}")

    def _on_new(self):
        if not self._check_save():
            return
        dlg = NewImageDialog(self)
        if dlg.exec_() == NewImageDialog.Accepted:
            w, h = dlg.get_size()
            bg = dlg.get_background()
            pil_img = Image.new("RGBA", (w, h), bg)
            pixmap = self.pil_to_pixmap(pil_img)
            self._current_file = None
            self._modified = False
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._set_image(pixmap, push_undo=False)
            self._canvas.fit_in_view()

    def _on_open(self):
        if not self._check_save():
            return
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", OPEN_FORMATS
        )
        if filepath:
            self.open_file(filepath)

    def _on_save(self):
        if self._current_file:
            self._save_to_file(self._current_file)
        else:
            self._on_save_as()

    def _on_save_as(self):
        filepath, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Image As", "", SAVE_FORMATS
        )
        if filepath:
            # Ensure correct extension
            if not os.path.splitext(filepath)[1]:
                # Extract extension from filter
                ext_map = {
                    "PNG": ".png",
                    "JPEG": ".jpg",
                    "BMP": ".bmp",
                    "TIFF": ".tiff",
                    "WebP": ".webp",
                    "ICO": ".ico",
                    "PPM": ".ppm",
                    "GIF": ".gif",
                }
                for key, ext in ext_map.items():
                    if key in selected_filter:
                        filepath += ext
                        break

            self._save_to_file(filepath)

    def _save_to_file(self, filepath: str):
        """Save current image to file."""
        try:
            pixmap = self._canvas.get_pixmap()
            if not pixmap:
                return

            pil_img = self.pixmap_to_pil(pixmap)

            ext = os.path.splitext(filepath)[1].lower()

            # Handle format-specific options
            save_kwargs = {}
            if ext in (".jpg", ".jpeg"):
                pil_img = pil_img.convert("RGB")
                save_kwargs["quality"] = 95
                save_kwargs["optimize"] = True
            elif ext == ".png":
                save_kwargs["optimize"] = True
            elif ext == ".webp":
                save_kwargs["quality"] = 90
            elif ext == ".bmp":
                pil_img = pil_img.convert("RGB")
            elif ext == ".ico":
                # ICO needs specific sizes
                pil_img = pil_img.convert("RGBA")
            elif ext == ".gif":
                pil_img = pil_img.convert("P", palette=Image.ADAPTIVE)

            pil_img.save(filepath, **save_kwargs)
            self._current_file = filepath
            self._modified = False
            self._update_title()
            self._update_status()
            self.statusBar().showMessage(f"Saved: {filepath}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file:\n{e}")

    def _check_save(self) -> bool:
        """Check if current image needs saving. Returns False if cancelled."""
        if not self._modified or not self._canvas.has_image():
            return True

        result = QMessageBox.question(
            self,
            "Unsaved Changes",
            "The image has been modified. Save changes?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if result == QMessageBox.Save:
            self._on_save()
            return True
        elif result == QMessageBox.Discard:
            return True
        else:
            return False

    # ── Edit Operations ──────────────────────────────────────────

    def _on_undo(self):
        if self._undo_stack:
            current = self._canvas.get_pixmap()
            if current:
                self._redo_stack.append(current)
            pixmap = self._undo_stack.pop()
            self._canvas.set_image(pixmap)
            self._modified = True
            self._update_title()
            self._update_actions()
            self._update_status()

    def _on_redo(self):
        if self._redo_stack:
            current = self._canvas.get_pixmap()
            if current:
                self._undo_stack.append(current)
            pixmap = self._redo_stack.pop()
            self._canvas.set_image(pixmap)
            self._modified = True
            self._update_title()
            self._update_actions()
            self._update_status()

    def _on_copy(self):
        pixmap = self._canvas.get_pixmap()
        if pixmap:
            clipboard = QApplication.clipboard()
            # If there's a selection, copy only the selection
            sel = self._canvas.get_selection_rect()
            if not sel.isEmpty():
                cropped = pixmap.copy(sel)
                clipboard.setPixmap(cropped)
                self.statusBar().showMessage("Selection copied to clipboard", 3000)
            else:
                clipboard.setPixmap(pixmap)
                self.statusBar().showMessage("Image copied to clipboard", 3000)

    def _on_paste(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        pixmap = None

        if mime.hasImage():
            qimg = clipboard.image()
            if not qimg.isNull():
                pixmap = QPixmap.fromImage(qimg)
        elif mime.hasUrls():
            for url in mime.urls():
                path = url.toLocalFile()
                if path and os.path.isfile(path):
                    p = QPixmap(path)
                    if not p.isNull():
                        pixmap = p
                        break

        if pixmap and not pixmap.isNull():
            self._current_file = None
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._set_image(pixmap, push_undo=False)
            # Auto-adjust workspace to pasted image size
            self._canvas.fit_in_view()
            self._modified = True
            self._update_title()
            self.statusBar().showMessage(
                f"Pasted image ({pixmap.width()}×{pixmap.height()})", 3000
            )
        else:
            self.statusBar().showMessage("No image in clipboard", 3000)

    def _on_select_all(self):
        """Select entire image for crop."""
        if self._canvas.has_image():
            pixmap = self._canvas.get_pixmap()
            if pixmap:
                if not self._canvas.is_crop_mode():
                    self._act_crop.setChecked(True)
                    self._canvas.set_crop_mode(True)
                rect = QRect(0, 0, pixmap.width(), pixmap.height())
                self._on_selection_changed(rect)

    # ── Image Operations ─────────────────────────────────────────

    def _on_toggle_crop(self, checked):
        self._canvas.set_crop_mode(checked)
        if checked:
            self.statusBar().showMessage(
                "Crop mode: Draw a selection rectangle, then use Image > Crop to Selection", 5000
            )
        else:
            self._status_selection.setText("")

    def _on_crop(self):
        sel = self._canvas.get_selection_rect()
        if sel.isEmpty():
            QMessageBox.information(
                self,
                "No Selection",
                "Enable Crop Mode (C) and draw a selection rectangle first.",
            )
            return

        pixmap = self._canvas.get_pixmap()
        if pixmap:
            cropped = pixmap.copy(sel)
            self._set_image(cropped)
            self._act_crop.setChecked(False)
            self._canvas.set_crop_mode(False)
            self._canvas.fit_in_view()
            self.statusBar().showMessage(
                f"Cropped to {cropped.width()}×{cropped.height()}", 3000
            )

    def _on_resize(self):
        pixmap = self._canvas.get_pixmap()
        if not pixmap:
            return

        dlg = ResizeDialog(pixmap.width(), pixmap.height(), self)
        if dlg.exec_() == ResizeDialog.Accepted:
            new_w, new_h = dlg.get_new_size()
            resample = dlg.get_resample_method()

            pil_img = self.pixmap_to_pil(pixmap)
            pil_img = pil_img.resize((new_w, new_h), resample)
            new_pixmap = self.pil_to_pixmap(pil_img)
            self._set_image(new_pixmap)
            self._canvas.fit_in_view()
            self.statusBar().showMessage(
                f"Resized to {new_w}×{new_h}", 3000
            )

    def _on_rotate(self, degrees):
        pixmap = self._canvas.get_pixmap()
        if not pixmap:
            return

        pil_img = self.pixmap_to_pil(pixmap)
        # PIL rotates counter-clockwise, so negate for CW
        pil_img = pil_img.rotate(-degrees, expand=True)
        new_pixmap = self.pil_to_pixmap(pil_img)
        self._set_image(new_pixmap)

    def _on_flip_h(self):
        pixmap = self._canvas.get_pixmap()
        if not pixmap:
            return

        pil_img = self.pixmap_to_pil(pixmap)
        pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
        self._set_image(self.pil_to_pixmap(pil_img))

    def _on_flip_v(self):
        pixmap = self._canvas.get_pixmap()
        if not pixmap:
            return

        pil_img = self.pixmap_to_pil(pixmap)
        pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)
        self._set_image(self.pil_to_pixmap(pil_img))

    # ── Effects ──────────────────────────────────────────────────

    def _apply_effect(self, effect_func):
        """Apply a PIL-based effect to the current image."""
        pixmap = self._canvas.get_pixmap()
        if not pixmap:
            return

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            pil_img = self.pixmap_to_pil(pixmap)
            result = effect_func(pil_img)
            new_pixmap = self.pil_to_pixmap(result)
            self._set_image(new_pixmap)
            self.statusBar().showMessage("Effect applied", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not apply effect:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_brightness_contrast(self):
        pixmap = self._canvas.get_pixmap()
        if not pixmap:
            return

        dlg = BrightnessContrastDialog(self)
        if dlg.exec_() == BrightnessContrastDialog.Accepted:
            pil_img = self.pixmap_to_pil(pixmap)
            brightness = dlg.get_brightness_factor()
            contrast = dlg.get_contrast_factor()

            if brightness != 1.0:
                pil_img = ImageEffects.brightness(pil_img, brightness)
            if contrast != 1.0:
                pil_img = ImageEffects.contrast(pil_img, contrast)

            self._set_image(self.pil_to_pixmap(pil_img))

    # ── Tools ────────────────────────────────────────────────────

    def _on_panorama(self):
        dlg = PanoramaDialog(self)
        if dlg.exec_() == PanoramaDialog.Accepted:
            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                panorama = dlg.create_panorama()
                pixmap = self.pil_to_pixmap(panorama)
                self._current_file = None
                self._undo_stack.clear()
                self._redo_stack.clear()
                self._set_image(pixmap, push_undo=False)
                self._canvas.fit_in_view()
                self.statusBar().showMessage(
                    f"Panorama created: {panorama.width}×{panorama.height}", 3000
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not create panorama:\n{e}"
                )
            finally:
                QApplication.restoreOverrideCursor()

    # ── About ────────────────────────────────────────────────────

    def _on_about(self):
        QMessageBox.about(
            self,
            "About JFView",
            "<h2>JFView 1.0.0</h2>"
            "<p>Image Viewer and Editor for Linux</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>View and save multiple image formats</li>"
            "<li>Paste from clipboard with auto-resize</li>"
            "<li>Crop, resize, rotate, flip</li>"
            "<li>Effects: grayscale, negative, edge detection, nanquim, sepia, and more</li>"
            "<li>Create panoramic images (horizontal/vertical)</li>"
            "<li>Undo/redo support</li>"
            "</ul>"
            "<p>Built with PyQt5 and Pillow</p>",
        )

    # ── Window Events ────────────────────────────────────────────

    def closeEvent(self, event):
        if self._check_save():
            event.accept()
        else:
            event.ignore()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and os.path.isfile(path):
                self.open_file(path)
                break

