"""Dialog windows for JFView."""

import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QCheckBox, QPushButton, QFileDialog, QListWidget,
    QListWidgetItem, QComboBox, QGroupBox, QGridLayout,
    QDialogButtonBox, QScrollArea, QWidget, QProgressBar,
    QRadioButton, QButtonGroup, QSizePolicy, QMessageBox,
    QSlider,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PIL import Image


class ResizeDialog(QDialog):
    """Dialog for resizing images."""

    def __init__(self, current_width, current_height, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resize Image")
        self.setMinimumWidth(350)

        self.original_width = current_width
        self.original_height = current_height
        self.aspect_ratio = current_width / current_height if current_height else 1

        self._updating = False

        layout = QVBoxLayout(self)

        # Current size info
        info_label = QLabel(f"Current size: {current_width} × {current_height} pixels")
        info_label.setStyleSheet("color: #666; margin-bottom: 8px;")
        layout.addWidget(info_label)

        # Size group
        size_group = QGroupBox("New Size")
        size_layout = QGridLayout()

        size_layout.addWidget(QLabel("Width:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 65535)
        self.width_spin.setValue(current_width)
        self.width_spin.setSuffix(" px")
        size_layout.addWidget(self.width_spin, 0, 1)

        size_layout.addWidget(QLabel("Height:"), 1, 0)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 65535)
        self.height_spin.setValue(current_height)
        self.height_spin.setSuffix(" px")
        size_layout.addWidget(self.height_spin, 1, 1)

        self.keep_aspect = QCheckBox("Maintain aspect ratio")
        self.keep_aspect.setChecked(True)
        size_layout.addWidget(self.keep_aspect, 2, 0, 1, 2)

        # Percentage resize
        size_layout.addWidget(QLabel("Scale:"), 3, 0)
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(1, 1000)
        self.scale_spin.setValue(100)
        self.scale_spin.setSuffix(" %")
        size_layout.addWidget(self.scale_spin, 3, 1)

        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        # Resample method
        method_group = QGroupBox("Resample Method")
        method_layout = QVBoxLayout()
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "Lanczos (Best Quality)",
            "Bicubic",
            "Bilinear",
            "Nearest (Fastest)",
        ])
        method_layout.addWidget(self.method_combo)
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Connections
        self.width_spin.valueChanged.connect(self._width_changed)
        self.height_spin.valueChanged.connect(self._height_changed)
        self.scale_spin.valueChanged.connect(self._scale_changed)

    def _width_changed(self, value):
        if self._updating:
            return
        self._updating = True
        if self.keep_aspect.isChecked():
            new_height = int(value / self.aspect_ratio)
            self.height_spin.setValue(max(1, new_height))
        scale = int(value / self.original_width * 100)
        self.scale_spin.setValue(max(1, scale))
        self._updating = False

    def _height_changed(self, value):
        if self._updating:
            return
        self._updating = True
        if self.keep_aspect.isChecked():
            new_width = int(value * self.aspect_ratio)
            self.width_spin.setValue(max(1, new_width))
        scale = int(value / self.original_height * 100)
        self.scale_spin.setValue(max(1, scale))
        self._updating = False

    def _scale_changed(self, value):
        if self._updating:
            return
        self._updating = True
        self.width_spin.setValue(max(1, int(self.original_width * value / 100)))
        self.height_spin.setValue(max(1, int(self.original_height * value / 100)))
        self._updating = False

    def get_new_size(self):
        return self.width_spin.value(), self.height_spin.value()

    def get_resample_method(self):
        methods = [
            Image.LANCZOS,
            Image.BICUBIC,
            Image.BILINEAR,
            Image.NEAREST,
        ]
        return methods[self.method_combo.currentIndex()]


class PanoramaDialog(QDialog):
    """Dialog for creating panoramic images by stitching."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Panorama")
        self.setMinimumSize(700, 500)

        self.images = []  # List of (path, PIL.Image) tuples

        layout = QVBoxLayout(self)

        # Direction
        dir_group = QGroupBox("Direction")
        dir_layout = QHBoxLayout()
        self.dir_group = QButtonGroup()

        self.horizontal_radio = QRadioButton("Horizontal (side by side)")
        self.horizontal_radio.setChecked(True)
        self.vertical_radio = QRadioButton("Vertical (top to bottom)")

        self.dir_group.addButton(self.horizontal_radio, 0)
        self.dir_group.addButton(self.vertical_radio, 1)

        dir_layout.addWidget(self.horizontal_radio)
        dir_layout.addWidget(self.vertical_radio)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        # Image list and controls
        list_group = QGroupBox("Images")
        list_layout = QHBoxLayout()

        # List widget
        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(80, 80))
        self.image_list.setMinimumHeight(200)
        list_layout.addWidget(self.image_list, 1)

        # Buttons for managing images
        btn_layout = QVBoxLayout()

        add_btn = QPushButton("Add Images...")
        add_btn.clicked.connect(self._add_images)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_image)
        btn_layout.addWidget(remove_btn)

        move_up_btn = QPushButton("Move Up")
        move_up_btn.clicked.connect(self._move_up)
        btn_layout.addWidget(move_up_btn)

        move_down_btn = QPushButton("Move Down")
        move_down_btn.clicked.connect(self._move_down)
        btn_layout.addWidget(move_down_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # Options
        opt_group = QGroupBox("Options")
        opt_layout = QHBoxLayout()

        self.match_size = QCheckBox("Match sizes (resize smaller images)")
        self.match_size.setChecked(True)
        opt_layout.addWidget(self.match_size)

        opt_layout.addWidget(QLabel("Spacing:"))
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 100)
        self.spacing_spin.setValue(0)
        self.spacing_spin.setSuffix(" px")
        opt_layout.addWidget(self.spacing_spin)

        opt_group.setLayout(opt_layout)
        layout.addWidget(opt_group)

        # Info label
        self.info_label = QLabel("Add at least 2 images to create a panorama.")
        self.info_label.setStyleSheet("color: #666;")
        layout.addWidget(self.info_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.gif);;All Files (*)",
        )
        for f in files:
            try:
                img = Image.open(f)
                img.load()  # Force load
                self.images.append((f, img))

                # Create thumbnail for list
                thumb = img.copy()
                thumb.thumbnail((80, 80))

                item = QListWidgetItem()
                name = os.path.basename(f)
                item.setText(f"{name} ({img.width}×{img.height})")

                # Convert PIL thumbnail to QPixmap
                if thumb.mode != "RGB":
                    thumb = thumb.convert("RGB")
                data = thumb.tobytes("raw", "RGB")
                qimg = QImage(data, thumb.width, thumb.height,
                              thumb.width * 3, QImage.Format_RGB888)
                item.setIcon(QIcon(QPixmap.fromImage(qimg)))

                self.image_list.addItem(item)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load {f}:\n{e}")

        self._update_info()

    def _remove_image(self):
        row = self.image_list.currentRow()
        if row >= 0:
            self.image_list.takeItem(row)
            self.images.pop(row)
            self._update_info()

    def _move_up(self):
        row = self.image_list.currentRow()
        if row > 0:
            item = self.image_list.takeItem(row)
            self.image_list.insertItem(row - 1, item)
            self.image_list.setCurrentRow(row - 1)
            self.images[row], self.images[row - 1] = (
                self.images[row - 1],
                self.images[row],
            )

    def _move_down(self):
        row = self.image_list.currentRow()
        if row < self.image_list.count() - 1:
            item = self.image_list.takeItem(row)
            self.image_list.insertItem(row + 1, item)
            self.image_list.setCurrentRow(row + 1)
            self.images[row], self.images[row + 1] = (
                self.images[row + 1],
                self.images[row],
            )

    def _clear_all(self):
        self.image_list.clear()
        self.images.clear()
        self._update_info()

    def _update_info(self):
        count = len(self.images)
        if count < 2:
            self.info_label.setText(
                f"{count} image(s) added. Need at least 2."
            )
        else:
            direction = "horizontally" if self.horizontal_radio.isChecked() else "vertically"
            self.info_label.setText(
                f"{count} images will be joined {direction}."
            )

    def _validate_and_accept(self):
        if len(self.images) < 2:
            QMessageBox.warning(
                self,
                "Not Enough Images",
                "Please add at least 2 images to create a panorama.",
            )
            return
        self.accept()

    def is_horizontal(self):
        return self.horizontal_radio.isChecked()

    def should_match_size(self):
        return self.match_size.isChecked()

    def get_spacing(self):
        return self.spacing_spin.value()

    def get_images(self):
        return [img for _, img in self.images]

    def create_panorama(self) -> Image.Image:
        """Create the panorama image from the loaded images."""
        images = [img.copy().convert("RGB") for _, img in self.images]
        horizontal = self.is_horizontal()
        match_size = self.should_match_size()
        spacing = self.get_spacing()

        if match_size:
            if horizontal:
                # Match heights
                max_height = max(img.height for img in images)
                resized = []
                for img in images:
                    if img.height != max_height:
                        ratio = max_height / img.height
                        new_width = int(img.width * ratio)
                        img = img.resize(
                            (new_width, max_height), Image.LANCZOS
                        )
                    resized.append(img)
                images = resized
            else:
                # Match widths
                max_width = max(img.width for img in images)
                resized = []
                for img in images:
                    if img.width != max_width:
                        ratio = max_width / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize(
                            (max_width, new_height), Image.LANCZOS
                        )
                    resized.append(img)
                images = resized

        if horizontal:
            total_width = sum(img.width for img in images) + spacing * (len(images) - 1)
            max_height = max(img.height for img in images)
            panorama = Image.new("RGB", (total_width, max_height), (255, 255, 255))
            x_offset = 0
            for img in images:
                y_offset = (max_height - img.height) // 2
                panorama.paste(img, (x_offset, y_offset))
                x_offset += img.width + spacing
        else:
            max_width = max(img.width for img in images)
            total_height = sum(img.height for img in images) + spacing * (len(images) - 1)
            panorama = Image.new("RGB", (max_width, total_height), (255, 255, 255))
            y_offset = 0
            for img in images:
                x_offset = (max_width - img.width) // 2
                panorama.paste(img, (x_offset, y_offset))
                y_offset += img.height + spacing

        return panorama


class BrightnessContrastDialog(QDialog):
    """Dialog for adjusting brightness and contrast."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Brightness / Contrast")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # Brightness
        layout.addWidget(QLabel("Brightness:"))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_label = QLabel("0")
        h1 = QHBoxLayout()
        h1.addWidget(self.brightness_slider)
        h1.addWidget(self.brightness_label)
        layout.addLayout(h1)
        self.brightness_slider.valueChanged.connect(
            lambda v: self.brightness_label.setText(str(v))
        )

        # Contrast
        layout.addWidget(QLabel("Contrast:"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_label = QLabel("0")
        h2 = QHBoxLayout()
        h2.addWidget(self.contrast_slider)
        h2.addWidget(self.contrast_label)
        layout.addLayout(h2)
        self.contrast_slider.valueChanged.connect(
            lambda v: self.contrast_label.setText(str(v))
        )

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_brightness_factor(self):
        """Return brightness factor (1.0 = no change)."""
        return 1.0 + self.brightness_slider.value() / 100.0

    def get_contrast_factor(self):
        """Return contrast factor (1.0 = no change)."""
        return 1.0 + self.contrast_slider.value() / 100.0


class NewImageDialog(QDialog):
    """Dialog for creating a new blank image."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Image")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        grid = QGridLayout()
        grid.addWidget(QLabel("Width:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 65535)
        self.width_spin.setValue(800)
        self.width_spin.setSuffix(" px")
        grid.addWidget(self.width_spin, 0, 1)

        grid.addWidget(QLabel("Height:"), 1, 0)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 65535)
        self.height_spin.setValue(600)
        self.height_spin.setSuffix(" px")
        grid.addWidget(self.height_spin, 1, 1)

        grid.addWidget(QLabel("Background:"), 2, 0)
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["White", "Black", "Transparent"])
        grid.addWidget(self.bg_combo, 2, 1)

        layout.addLayout(grid)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_size(self):
        return self.width_spin.value(), self.height_spin.value()

    def get_background(self):
        idx = self.bg_combo.currentIndex()
        if idx == 0:
            return (255, 255, 255, 255)
        elif idx == 1:
            return (0, 0, 0, 255)
        else:
            return (0, 0, 0, 0)
