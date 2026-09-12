"""
Canvas View for Animator
Provides infinite canvas, smooth zooming (mouse-centered), pan (space/middle click),
and interactive creation of Figma-like elements.
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QKeyEvent, QCursor
from ui.canvas.items import RectangleItem, EllipseItem, TextItem, ArtboardItem
from core.undo_manager import AddItemCommand


class CanvasView(QGraphicsView):
    zoomChanged = Signal(float)  # Current zoom percentage

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.TextAntialiasing
        )
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        self._is_panning = False
        self._pan_start_pos = QPointF()
        self._space_pressed = False
        self._zoom_factor = 1.0

        # Creation mode tracking
        self.active_tool = "select"  # select, rect, ellipse, text
        self._creation_start_scene_pos = None

    def set_tool(self, tool_name: str):
        self.active_tool = tool_name
        if tool_name == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif tool_name in ("rect", "ellipse"):
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif tool_name == "text":
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.IBeamCursor)

    def wheelEvent(self, event: QWheelEvent):
        """
        Figma-style wheel interaction:
        - Ctrl + Wheel: Zoom in / Zoom out (centered at mouse)
        - Shift + Wheel: Pan left / right (horizontal scroll)
        - Normal Wheel: Pan up / down (vertical scroll like arrow keys)
        """
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_in_factor = 1.15
            zoom_out_factor = 1 / zoom_in_factor

            if event.angleDelta().y() > 0:
                if self._zoom_factor < 20.0:
                    self.scale(zoom_in_factor, zoom_in_factor)
                    self._zoom_factor *= zoom_in_factor
            else:
                if self._zoom_factor > 0.05:
                    self.scale(zoom_out_factor, zoom_out_factor)
                    self._zoom_factor *= zoom_out_factor

            self.zoomChanged.emit(self._zoom_factor * 100.0)
            event.accept()
            return

        # Normal Wheel or Shift+Wheel: Pan like arrow keys
        delta_y = event.angleDelta().y()
        delta_x = event.angleDelta().x()
        scroll_speed = 1.2

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Horizontal pan
            effective_delta = delta_y if delta_x == 0 else delta_x
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - effective_delta * scroll_speed))
        else:
            # Vertical pan (like up/down arrow keys)
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta_y * scroll_speed))

        event.accept()

    def reset_zoom(self):
        self.resetTransform()
        self._zoom_factor = 1.0
        self.zoomChanged.emit(100.0)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_pressed = True
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return

        # Arrow key navigation (Nudge items or scroll canvas)
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            step = 10.0 if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) else 1.0
            dx, dy = 0.0, 0.0
            if event.key() == Qt.Key.Key_Left:
                dx = -step
            elif event.key() == Qt.Key.Key_Right:
                dx = step
            elif event.key() == Qt.Key.Key_Up:
                dy = -step
            elif event.key() == Qt.Key.Key_Down:
                dy = step

            selected = [it for it in self.scene().selectedItems() if not isinstance(it, ArtboardItem)]
            if selected:
                # Nudge selected items
                for it in selected:
                    old_geom = (it.x(), it.y(), it.w, it.h, it.rotation())
                    it.setPos(it.x() + dx, it.y() + dy)
                    it.update()
                    new_geom = (it.x(), it.y(), it.w, it.h, it.rotation())
                    if hasattr(self.scene(), "record_transform"):
                        self.scene().record_transform(it, old_geom, new_geom)
                event.accept()
                return
            else:
                # Scroll canvas view in empty space
                pan_step = int(step * 4.0)
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + int(dx * 4))
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() + int(dy * 4))
                event.accept()
                return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_pressed = False
            self.set_tool(self.active_tool)
            event.accept()
            return
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        # Space + Left click or Middle click -> Pan
        if self._space_pressed or event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        # Interactive item creation on canvas
        if self.active_tool in ("rect", "ellipse", "text") and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self._creation_start_scene_pos = scene_pos
            
            if self.active_tool == "text":
                # Create text immediately at click position
                txt_item = TextItem(scene_pos.x(), scene_pos.y(), "Typing Animation Text", "Text")
                self.scene().addItem(txt_item)
                self.scene().clearSelection()
                txt_item.setSelected(True)
                self.scene().itemAdded.emit(txt_item)
                if hasattr(self.scene(), "undo_manager"):
                    self.scene().undo_manager.push(AddItemCommand(self.scene(), txt_item))
                self.set_tool("select")
                event.accept()
                return

            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.pos() - self._pan_start_pos
            self._pan_start_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.OpenHandCursor if self._space_pressed else Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        if self._creation_start_scene_pos is not None and self.active_tool in ("rect", "ellipse"):
            scene_pos = self.mapToScene(event.pos())
            start_p = self._creation_start_scene_pos
            self._creation_start_scene_pos = None

            x = min(start_p.x(), scene_pos.x())
            y = min(start_p.y(), scene_pos.y())
            w = max(20.0, abs(scene_pos.x() - start_p.x()))
            h = max(20.0, abs(scene_pos.y() - start_p.y()))

            if self.active_tool == "rect":
                item = RectangleItem(x, y, w, h, "Rectangle")
            elif self.active_tool == "ellipse":
                item = EllipseItem(x, y, w, h, "Ellipse")
            else:
                item = None

            if item:
                self.scene().addItem(item)
                self.scene().clearSelection()
                item.setSelected(True)
                self.scene().itemAdded.emit(item)
                if hasattr(self.scene(), "undo_manager"):
                    self.scene().undo_manager.push(AddItemCommand(self.scene(), item))

            self.set_tool("select")
            event.accept()
            return

        super().mouseReleaseEvent(event)
