"""
Canvas Scene for Animator
Handles item management, layer order, selection events, Alt-drag duplication, and project state.
"""

from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QObject
from PySide6.QtGui import QPainter, QColor, QPen
from ui.canvas.items import ResizableItem, ArtboardItem, RectangleItem, EllipseItem, TextItem, PathItem


class CanvasScene(QGraphicsScene):
    # Signals for UI synchronization
    selectionChangedCustom = Signal(list)
    itemModified = Signal(object)
    itemAdded = Signal(object)
    itemRemoved = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.setBackgroundBrush(QColor("#141417"))
        
        self.artboard = None
        self.current_tool = "select"  # select, rect, ellipse, text, path
        self._drag_start_pos = None
        self._temp_creating_item = None

        # Components registry (Figma component concept)
        self.components_registry = {}  # id -> item template or metadata

        self.selectionChanged.connect(self._on_selection_changed)

    def set_default_artboard(self, width=800, height=600):
        if self.artboard:
            self.removeItem(self.artboard)
        self.artboard = ArtboardItem(-width / 2, -height / 2, width, height, "Artboard 1")
        self.addItem(self.artboard)
        self.itemAdded.emit(self.artboard)

    def _on_selection_changed(self):
        selected = [item for item in self.selectedItems() if isinstance(item, ResizableItem)]
        self.selectionChangedCustom.emit(selected)

    def item_geometry_changed(self, item):
        self.itemModified.emit(item)

    def duplicate_item(self, item: ResizableItem, offset=QPointF(20, 20)):
        """Duplicate an item and add to scene with selection transferred."""
        if not hasattr(item, "duplicate"):
            return None
            
        new_item = item.duplicate(offset)
        self.addItem(new_item)
        
        # Clear other selections and select new
        self.clearSelection()
        new_item.setSelected(True)
        self.itemAdded.emit(new_item)
        self.itemModified.emit(new_item)
        return new_item

    def get_ordered_items(self):
        """Get items in layer order (excluding artboard background)."""
        items = []
        for it in self.items():
            if isinstance(it, ResizableItem) and not isinstance(it, ArtboardItem):
                items.append(it)
        return items

    def create_outline_for_item(self, text_item: TextItem):
        """Convert TextItem to PathItem."""
        path_item = text_item.create_outlines()
        self.addItem(path_item)
        self.removeItem(text_item)
        self.itemRemoved.emit(text_item)
        self.itemAdded.emit(path_item)
        self.clearSelection()
        path_item.setSelected(True)
        self.itemModified.emit(path_item)
        return path_item

    def make_component(self, item: ResizableItem):
        """Mark an item as a reusable Figma-like Component."""
        item.is_component = True
        item.master_component_id = item.item_id
        self.components_registry[item.item_id] = {
            "name": item.name,
            "type": type(item).__name__,
            "fill": item.fill_color.name(),
            "stroke": item.stroke_color.name(),
            "w": item.w,
            "h": item.h,
        }
        item.update()
        self.itemModified.emit(item)

    def instantiate_component(self, comp_id: str, pos=QPointF(0, 0)):
        """Create an instance of a registered Component."""
        comp_data = self.components_registry.get(comp_id)
        if not comp_data:
            return None
        
        # Find master or recreate
        item_type = comp_data["type"]
        if item_type == "RectangleItem":
            new_item = RectangleItem(pos.x(), pos.y(), comp_data["w"], comp_data["h"], f"{comp_data['name']} (Instance)")
        elif item_type == "EllipseItem":
            new_item = EllipseItem(pos.x(), pos.y(), comp_data["w"], comp_data["h"], f"{comp_data['name']} (Instance)")
        elif item_type == "TextItem":
            new_item = TextItem(pos.x(), pos.y(), "Instance Text", f"{comp_data['name']} (Instance)")
        else:
            new_item = RectangleItem(pos.x(), pos.y(), 100, 100, f"{comp_data['name']} (Instance)")

        new_item.fill_color = QColor(comp_data["fill"])
        new_item.stroke_color = QColor(comp_data["stroke"])
        new_item.master_component_id = comp_id
        
        self.addItem(new_item)
        self.clearSelection()
        new_item.setSelected(True)
        self.itemAdded.emit(new_item)
        return new_item

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Figma-style dark infinite canvas grid."""
        super().drawBackground(painter, rect)
        
        painter.save()
        grid_size = 20
        pen = QPen(QColor("#22222a"), 0.5)
        pen.setCosmetic(True)
        painter.setPen(pen)

        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        right = int(rect.right())
        bottom = int(rect.bottom())

        # Sub-grid points or lines
        for x in range(left, right, grid_size):
            painter.drawLine(x, top, x, bottom)
        for y in range(top, bottom, grid_size):
            painter.drawLine(left, y, right, y)

        painter.restore()
