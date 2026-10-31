"""Image canvas widget for JFView."""

from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QRubberBand, QApplication,
)
from PyQt5.QtCore import Qt, QRectF, QRect, QPoint, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QWheelEvent, QColor, QBrush


class ImageCanvas(QGraphicsView):
    """Widget for displaying and interacting with images."""

    selection_changed = pyqtSignal(QRect)  # Emitted when crop selection changes
    zoom_changed = pyqtSignal(float)  # Emitted when zoom level changes
    mouse_pos_changed = pyqtSignal(int, int)  # Mouse position on image

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item = None
        self._zoom_factor = 1.0
        self._min_zoom = 0.05
        self._max_zoom = 20.0

        # Crop selection
        self._crop_mode = False
        self._rubber_band = None
        self._selection_origin = QPoint()
        self._selection_rect = QRect()

        # Appearance
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setBackgroundBrush(QColor(200, 200, 200))

        # Checkerboard pattern for transparent images
        self._setup_background()

    def _setup_background(self):
        """Create a checkerboard pattern for the background."""
        tile = QPixmap(16, 16)
        tile.fill(QColor(200, 200, 200))
        painter = QPainter(tile)
        painter.fillRect(0, 0, 8, 8, QColor(220, 220, 220))
        painter.fillRect(8, 8, 8, 8, QColor(220, 220, 220))
        painter.end()
        self.setBackgroundBrush(QBrush(tile))

    def set_image(self, pixmap: QPixmap):
        """Set the displayed image."""
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self._selection_rect = QRect()

    def get_pixmap(self) -> QPixmap:
        """Get the current displayed pixmap."""
        if self._pixmap_item:
            return self._pixmap_item.pixmap()
        return None

    def has_image(self) -> bool:
        """Check if an image is loaded."""
        return self._pixmap_item is not None

    def fit_in_view(self):
        """Fit the image in the view."""
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
            self._zoom_factor = self.transform().m11()
            self.zoom_changed.emit(self._zoom_factor)

    def zoom_to(self, factor: float):
        """Zoom to a specific factor."""
        factor = max(self._min_zoom, min(self._max_zoom, factor))
        self.resetTransform()
        self.scale(factor, factor)
        self._zoom_factor = factor
        self.zoom_changed.emit(self._zoom_factor)

    def zoom_in(self):
        """Zoom in by 25%."""
        self.zoom_to(self._zoom_factor * 1.25)

    def zoom_out(self):
        """Zoom out by 25%."""
        self.zoom_to(self._zoom_factor / 1.25)

    def zoom_original(self):
        """Reset to 100% zoom."""
        self.zoom_to(1.0)

    def get_zoom(self) -> float:
        return self._zoom_factor

    # Crop mode
    def set_crop_mode(self, enabled: bool):
        """Enable or disable crop selection mode."""
        self._crop_mode = enabled
        if enabled:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.ArrowCursor)
            if self._rubber_band:
                self._rubber_band.hide()
            self._selection_rect = QRect()

    def is_crop_mode(self) -> bool:
        return self._crop_mode

    def get_selection_rect(self) -> QRect:
        """Get the selection rectangle in image coordinates."""
        return self._selection_rect

    # Event overrides
    def wheelEvent(self, event: QWheelEvent):
        """Zoom with mouse wheel."""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def mousePressEvent(self, event):
        if self._crop_mode and event.button() == Qt.LeftButton:
            self._selection_origin = event.pos()
            if not self._rubber_band:
                self._rubber_band = QRubberBand(QRubberBand.Rectangle, self)
            self._rubber_band.setGeometry(QRect(self._selection_origin, QSize()))
            self._rubber_band.show()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Track mouse position on image
        if self._pixmap_item:
            scene_pos = self.mapToScene(event.pos())
            x, y = int(scene_pos.x()), int(scene_pos.y())
            pixmap = self._pixmap_item.pixmap()
            if 0 <= x < pixmap.width() and 0 <= y < pixmap.height():
                self.mouse_pos_changed.emit(x, y)

        if self._crop_mode and self._rubber_band and self._rubber_band.isVisible():
            self._rubber_band.setGeometry(
                QRect(self._selection_origin, event.pos()).normalized()
            )
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._crop_mode and event.button() == Qt.LeftButton and self._rubber_band:
            # Convert rubber band rect to scene/image coordinates
            rb_rect = self._rubber_band.geometry()
            top_left = self.mapToScene(rb_rect.topLeft())
            bottom_right = self.mapToScene(rb_rect.bottomRight())

            x1 = max(0, int(top_left.x()))
            y1 = max(0, int(top_left.y()))
            x2 = int(bottom_right.x())
            y2 = int(bottom_right.y())

            if self._pixmap_item:
                pixmap = self._pixmap_item.pixmap()
                x2 = min(pixmap.width(), x2)
                y2 = min(pixmap.height(), y2)

            self._selection_rect = QRect(x1, y1, x2 - x1, y2 - y1)
            self.selection_changed.emit(self._selection_rect)
        else:
            super().mouseReleaseEvent(event)
