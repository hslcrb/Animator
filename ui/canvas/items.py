"""
Canvas item definitions including Shapes, Texts, Artboards, and Path Outlines.
Supports selection bounding boxes, handles, Alt+Drag duplication, and styling.
"""

from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsPathItem,
    QGraphicsSceneMouseEvent, QGraphicsScene
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetricsF,
    QPainterPath, QCursor, QTransform
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
import uuid


class SelectionHandle:
    TOP_LEFT = 0
    TOP_MID = 1
    TOP_RIGHT = 2
    MID_RIGHT = 3
    BOTTOM_RIGHT = 4
    BOTTOM_MID = 5
    BOTTOM_LEFT = 6
    MID_LEFT = 7
    ROTATE = 8


class CanvasItemBase:
    """Shared functionality for design items."""
    def __init__(self):
        self.item_id = str(uuid.uuid4())[:8]
        self.name = "Item"
        self.fill_color = QColor("#3b82f6")
        self.stroke_color = QColor("#1d4ed8")
        self.stroke_width = 1.0
        self.border_radius = 0.0
        self.opacity_val = 1.0
        self.is_component = False
        self.master_component_id = None
        self.is_locked = False
        
        # Drag duplicate tracking
        self._alt_drag_started = False
        self._initial_pos = QPointF()

    def duplicate(self, offset=QPointF(20, 20)):
        raise NotImplementedError


class ResizableItem(QGraphicsItem, CanvasItemBase):
    """Base interactive item with selection box, resize handles, and Alt+Drag duplicate."""
    def __init__(self, x=0, y=0, w=100, h=100):
        QGraphicsItem.__init__(self)
        CanvasItemBase.__init__(self)
        
        self.setPos(x, y)
        self.w = max(10.0, float(w))
        self.h = max(10.0, float(h))
        self.handle_size = 8.0
        self.active_handle = None
        self.drag_start_pos = QPointF()
        self.drag_start_rect = QRectF(0, 0, self.w, self.h)
        
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        pad = self.handle_size + self.stroke_width + 4
        return QRectF(-pad, -pad, self.w + pad * 2, self.h + pad * 2)

    def get_content_rect(self) -> QRectF:
        return QRectF(0, 0, self.w, self.h)

    def get_handle_rects(self):
        hs = self.handle_size
        half = hs / 2
        w, h = self.w, self.h
        return {
            SelectionHandle.TOP_LEFT: QRectF(-half, -half, hs, hs),
            SelectionHandle.TOP_MID: QRectF(w / 2 - half, -half, hs, hs),
            SelectionHandle.TOP_RIGHT: QRectF(w - half, -half, hs, hs),
            SelectionHandle.MID_RIGHT: QRectF(w - half, h / 2 - half, hs, hs),
            SelectionHandle.BOTTOM_RIGHT: QRectF(w - half, h - half, hs, hs),
            SelectionHandle.BOTTOM_MID: QRectF(w / 2 - half, h - half, hs, hs),
            SelectionHandle.BOTTOM_LEFT: QRectF(-half, h - half, hs, hs),
            SelectionHandle.MID_LEFT: QRectF(-half, h / 2 - half, hs, hs),
        }

    def hoverMoveEvent(self, event):
        if not self.isSelected() or self.is_locked:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            super().hoverMoveEvent(event)
            return

        pos = event.pos()
        handle = self._get_handle_at(pos)
        if handle in (SelectionHandle.TOP_LEFT, SelectionHandle.BOTTOM_RIGHT):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif handle in (SelectionHandle.TOP_RIGHT, SelectionHandle.BOTTOM_LEFT):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif handle in (SelectionHandle.TOP_MID, SelectionHandle.BOTTOM_MID):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif handle in (SelectionHandle.MID_LEFT, SelectionHandle.MID_RIGHT):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverMoveEvent(event)

    def _get_handle_at(self, pos: QPointF):
        for h_type, rect in self.get_handle_rects().items():
            if rect.contains(pos):
                return h_type
        return None

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.is_locked:
            event.ignore()
            return

        # Alt + Drag duplication:
        if (event.modifiers() & Qt.KeyboardModifier.AltModifier) and event.button() == Qt.MouseButton.LeftButton:
            self._handle_alt_duplicate(event)
            return

        if self.isSelected() and event.button() == Qt.MouseButton.LeftButton:
            self.active_handle = self._get_handle_at(event.pos())
            if self.active_handle is not None:
                self.drag_start_pos = event.scenePos()
                self.drag_start_rect = QRectF(0, 0, self.w, self.h)
                event.accept()
                return

        super().mousePressEvent(event)

    def _handle_alt_duplicate(self, event: QGraphicsSceneMouseEvent):
        """Duplicate current item when dragged with Alt key pressed."""
        scene = self.scene()
        if scene and hasattr(scene, "duplicate_item"):
            new_item = scene.duplicate_item(self, offset=QPointF(0, 0))
            if new_item:
                # Let user drag the new duplicate instead
                self.setSelected(False)
                new_item.setSelected(True)
                new_item.mousePressEvent(event)
                event.accept()
                return

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.active_handle is not None:
            delta = event.scenePos() - self.drag_start_pos
            r = self.drag_start_rect
            
            # Map delta to local coordinates
            # Note: For simple unrotated item, local delta = scene delta
            inv_trans, _ = self.sceneTransform().inverted()
            local_delta = inv_trans.map(delta) - inv_trans.map(QPointF(0, 0))
            
            nw, nh = r.width(), r.height()
            nx, ny = self.pos().x(), self.pos().y()

            if self.active_handle == SelectionHandle.BOTTOM_RIGHT:
                nw = max(10, r.width() + local_delta.x())
                nh = max(10, r.height() + local_delta.y())
            elif self.active_handle == SelectionHandle.MID_RIGHT:
                nw = max(10, r.width() + local_delta.x())
            elif self.active_handle == SelectionHandle.BOTTOM_MID:
                nh = max(10, r.height() + local_delta.y())
            elif self.active_handle == SelectionHandle.TOP_LEFT:
                dx = min(r.width() - 10, local_delta.x())
                dy = min(r.height() - 10, local_delta.y())
                nw = r.width() - dx
                nh = r.height() - dy
                self.setPos(nx + dx, ny + dy)
            elif self.active_handle == SelectionHandle.TOP_RIGHT:
                dy = min(r.height() - 10, local_delta.y())
                nw = max(10, r.width() + local_delta.x())
                nh = r.height() - dy
                self.setPos(nx, ny + dy)
            elif self.active_handle == SelectionHandle.BOTTOM_LEFT:
                dx = min(r.width() - 10, local_delta.x())
                nw = r.width() - dx
                nh = max(10, r.height() + local_delta.y())
                self.setPos(nx + dx, ny)

            self.prepareGeometryChange()
            self.w = nw
            self.h = nh
            self.update()
            
            # Notify scene change
            if self.scene() and hasattr(self.scene(), "item_geometry_changed"):
                self.scene().item_geometry_changed(self)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        self.active_handle = None
        super().mouseReleaseEvent(event)

    def paint_selection_frame(self, painter: QPainter):
        """Figma-style sleek selection bounds and handles."""
        if not self.isSelected() or self.is_locked:
            return

        painter.save()
        # Bounding box
        pen = QPen(QColor("#0d99ff"), 1.2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(0, 0, self.w, self.h))

        # Handles
        handle_brush = QBrush(QColor("#ffffff"))
        handle_pen = QPen(QColor("#0d99ff"), 1.2)
        handle_pen.setCosmetic(True)
        painter.setPen(handle_pen)
        painter.setBrush(handle_brush)

        for rect in self.get_handle_rects().values():
            painter.drawRect(rect)

        # Component indicator badge (purple if component)
        if self.is_component:
            comp_pen = QPen(QColor("#a855f7"), 1.5)
            comp_pen.setCosmetic(True)
            painter.setPen(comp_pen)
            painter.drawRect(QRectF(-2, -2, self.w + 4, self.h + 4))

        painter.restore()


class ArtboardItem(ResizableItem):
    """Figma-like Artboard/Frame with solid or transparent background."""
    def __init__(self, x=0, y=0, w=800, h=600, name="Artboard 1"):
        super().__init__(x, y, w, h)
        self.name = name
        self.fill_color = QColor("#1e1e24")
        self.stroke_color = QColor("#383844")
        self.stroke_width = 1.0
        self.setZValue(-100)  # Always behind content

    def paint(self, painter: QPainter, option, widget=None):
        painter.save()
        painter.setOpacity(self.opacity_val)
        
        # Background
        painter.setBrush(QBrush(self.fill_color))
        painter.setPen(QPen(self.stroke_color, self.stroke_width))
        painter.drawRect(QRectF(0, 0, self.w, self.h))
        
        # Artboard label on top-left (Figma style)
        painter.setPen(QPen(QColor("#94a3b8"), 1))
        font = QFont("Segoe UI", 10, QFont.Weight.Medium)
        painter.setFont(font)
        painter.drawText(QPointF(2, -8), self.name)
        
        painter.restore()
        self.paint_selection_frame(painter)

    def duplicate(self, offset=QPointF(50, 50)):
        new_art = ArtboardItem(self.x() + offset.x(), self.y() + offset.y(), self.w, self.h, f"{self.name} Copy")
        new_art.fill_color = QColor(self.fill_color)
        new_art.stroke_color = QColor(self.stroke_color)
        new_art.stroke_width = self.stroke_width
        return new_art


class RectangleItem(ResizableItem):
    """Vector Rectangle shape with border radius and styles."""
    def __init__(self, x=0, y=0, w=150, h=100, name="Rectangle"):
        super().__init__(x, y, w, h)
        self.name = name
        self.fill_color = QColor("#3b82f6")
        self.stroke_color = QColor("#1d4ed8")
        self.stroke_width = 1.5

    def paint(self, painter: QPainter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self.opacity_val)

        pen = QPen(self.stroke_color, self.stroke_width)
        if self.stroke_width <= 0:
            pen = Qt.PenStyle.NoPen
        painter.setPen(pen)
        painter.setBrush(QBrush(self.fill_color))

        rect = QRectF(0, 0, self.w, self.h)
        if self.border_radius > 0:
            painter.drawRoundedRect(rect, self.border_radius, self.border_radius)
        else:
            painter.drawRect(rect)

        painter.restore()
        self.paint_selection_frame(painter)

    def duplicate(self, offset=QPointF(20, 20)):
        item = RectangleItem(self.x() + offset.x(), self.y() + offset.y(), self.w, self.h, f"{self.name} Copy")
        item.fill_color = QColor(self.fill_color)
        item.stroke_color = QColor(self.stroke_color)
        item.stroke_width = self.stroke_width
        item.border_radius = self.border_radius
        item.opacity_val = self.opacity_val
        item.setRotation(self.rotation())
        item.is_component = self.is_component
        item.master_component_id = self.master_component_id
        return item


class EllipseItem(ResizableItem):
    """Vector Ellipse/Circle shape."""
    def __init__(self, x=0, y=0, w=120, h=120, name="Ellipse"):
        super().__init__(x, y, w, h)
        self.name = name
        self.fill_color = QColor("#10b981")
        self.stroke_color = QColor("#047857")
        self.stroke_width = 1.5

    def paint(self, painter: QPainter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self.opacity_val)

        pen = QPen(self.stroke_color, self.stroke_width)
        if self.stroke_width <= 0:
            pen = Qt.PenStyle.NoPen
        painter.setPen(pen)
        painter.setBrush(QBrush(self.fill_color))

        painter.drawEllipse(QRectF(0, 0, self.w, self.h))

        painter.restore()
        self.paint_selection_frame(painter)

    def duplicate(self, offset=QPointF(20, 20)):
        item = EllipseItem(self.x() + offset.x(), self.y() + offset.y(), self.w, self.h, f"{self.name} Copy")
        item.fill_color = QColor(self.fill_color)
        item.stroke_color = QColor(self.stroke_color)
        item.stroke_width = self.stroke_width
        item.opacity_val = self.opacity_val
        item.setRotation(self.rotation())
        return item


class TextItem(ResizableItem):
    """Text element with typing animation capability and Create Outlines support."""
    def __init__(self, x=0, y=0, text="Typing Animation Text", name="Text"):
        super().__init__(x, y, 300, 60)
        self.name = name
        self.text = text
        self.font_family = "Segoe UI"
        self.font_size = 28.0
        self.font_bold = True
        self.font_italic = False
        self.fill_color = QColor("#ffffff")
        self.stroke_color = QColor("#000000")
        self.stroke_width = 0.0

        # Typing animation attributes
        self.enable_typing_anim = True
        self.typing_progress = 1.0  # 0.0 to 1.0 (portion of text displayed)
        self.show_cursor = True
        self.cursor_char = "|"
        self.typing_speed = 1.0     # Speed multiplier
        self.loop_delay = 1.0       # Pause before repeat (seconds)
        
        self.adjust_size_to_text()

    def adjust_size_to_text(self):
        font = self.get_font()
        fm = QFontMetricsF(font)
        bounds = fm.boundingRect(self.text + (self.cursor_char if self.show_cursor else ""))
        self.w = max(50.0, bounds.width() + 20)
        self.h = max(30.0, bounds.height() + 10)
        self.prepareGeometryChange()
        self.update()

    def get_font(self) -> QFont:
        font = QFont(self.font_family, int(self.font_size))
        font.setBold(self.font_bold)
        font.setItalic(self.font_italic)
        return font

    def get_displayed_text(self) -> str:
        """Calculate displayed characters based on typing progress (0.0 ~ 1.0)."""
        if not self.enable_typing_anim or self.typing_progress >= 1.0:
            return self.text
        
        count = int(round(len(self.text) * max(0.0, min(1.0, self.typing_progress))))
        txt = self.text[:count]
        if self.show_cursor and count < len(self.text):
            txt += self.cursor_char
        return txt

    def paint(self, painter: QPainter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setOpacity(self.opacity_val)

        font = self.get_font()
        painter.setFont(font)
        painter.setPen(QPen(self.fill_color))

        disp_text = self.get_displayed_text()
        fm = QFontMetricsF(font)
        y_offset = fm.ascent() + 5

        painter.drawText(QPointF(5, y_offset), disp_text)

        painter.restore()
        self.paint_selection_frame(painter)

    def create_outlines(self) -> "PathItem":
        """Convert current text into vector PathItem (QPainterPath outline)."""
        font = self.get_font()
        fm = QFontMetricsF(font)
        y_offset = fm.ascent() + 5
        
        path = QPainterPath()
        path.addText(QPointF(5, y_offset), font, self.text)
        
        path_bounds = path.boundingRect()
        
        path_item = PathItem(
            x=self.x(),
            y=self.y(),
            path=path,
            name=f"{self.name} Outline"
        )
        path_item.fill_color = QColor(self.fill_color)
        path_item.stroke_color = QColor(self.stroke_color)
        path_item.stroke_width = self.stroke_width
        path_item.opacity_val = self.opacity_val
        path_item.w = max(20.0, path_bounds.width() + 10)
        path_item.h = max(20.0, path_bounds.height() + 10)
        return path_item

    def duplicate(self, offset=QPointF(20, 20)):
        item = TextItem(self.x() + offset.x(), self.y() + offset.y(), self.text, f"{self.name} Copy")
        item.font_family = self.font_family
        item.font_size = self.font_size
        item.font_bold = self.font_bold
        item.font_italic = self.font_italic
        item.fill_color = QColor(self.fill_color)
        item.stroke_color = QColor(self.stroke_color)
        item.stroke_width = self.stroke_width
        item.opacity_val = self.opacity_val
        item.enable_typing_anim = self.enable_typing_anim
        item.typing_progress = self.typing_progress
        item.show_cursor = self.show_cursor
        item.adjust_size_to_text()
        return item


class PathItem(ResizableItem):
    """Vector path item created from shapes or Text Outlines."""
    def __init__(self, x=0, y=0, path=None, name="Path"):
        super().__init__(x, y, 100, 100)
        self.name = name
        self.path = path or QPainterPath()
        self.fill_color = QColor("#f43f5e")
        self.stroke_color = QColor("#be123c")
        self.stroke_width = 1.0

        if path:
            br = path.boundingRect()
            self.w = max(20.0, br.width() + 10)
            self.h = max(20.0, br.height() + 10)

    def paint(self, painter: QPainter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self.opacity_val)

        pen = QPen(self.stroke_color, self.stroke_width)
        if self.stroke_width <= 0:
            pen = Qt.PenStyle.NoPen
        painter.setPen(pen)
        painter.setBrush(QBrush(self.fill_color))

        painter.drawPath(self.path)

        painter.restore()
        self.paint_selection_frame(painter)

    def duplicate(self, offset=QPointF(20, 20)):
        item = PathItem(self.x() + offset.x(), self.y() + offset.y(), QPainterPath(self.path), f"{self.name} Copy")
        item.fill_color = QColor(self.fill_color)
        item.stroke_color = QColor(self.stroke_color)
        item.stroke_width = self.stroke_width
        item.opacity_val = self.opacity_val
        item.w = self.w
        item.h = self.h
        return item
