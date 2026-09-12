"""
Layers & Components Panel for Animator
Provides Figma-style layer hierarchy, visibility/lock toggles, component library, and animation presets.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor
from ui.canvas.items import ResizableItem, ArtboardItem, RectangleItem, EllipseItem, TextItem, PathItem


class LayersPanel(QWidget):
    itemSelected = Signal(object)
    createPresetRequested = Signal(str)
    insertComponentRequested = Signal(str)

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self._updating_tree = False

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 1. Layers Tab
        layers_tab = QWidget()
        layers_layout = QVBoxLayout(layers_tab)
        layers_layout.setContentsMargins(6, 6, 6, 6)
        layers_layout.setSpacing(6)

        # Action bar
        btn_layout = QHBoxLayout()
        self.btn_up = QPushButton("▲ Up")
        self.btn_up.setToolTip("Bring Forward")
        self.btn_down = QPushButton("▼ Down")
        self.btn_down.setToolTip("Send Backward")
        self.btn_delete = QPushButton("✕ Delete")
        self.btn_delete.setToolTip("Delete Item")
        
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        btn_layout.addWidget(self.btn_delete)
        layers_layout.addLayout(btn_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(3)
        self.tree.setColumnWidth(0, 160)  # Name
        self.tree.setColumnWidth(1, 30)   # Visibility
        self.tree.setColumnWidth(2, 30)   # Lock
        layers_layout.addWidget(self.tree)

        self.tab_widget.addTab(layers_tab, "Layers")

        # 2. Components Tab (Figma-style)
        comps_tab = QWidget()
        comps_layout = QVBoxLayout(comps_tab)
        comps_layout.setContentsMargins(6, 6, 6, 6)
        comps_layout.setSpacing(6)

        lbl_comp_desc = QLabel("Reusable Components & Assets")
        lbl_comp_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        comps_layout.addWidget(lbl_comp_desc)

        self.comp_list = QListWidget()
        comps_layout.addWidget(self.comp_list)

        self.btn_insert_comp = QPushButton("+ Insert Instance")
        self.btn_insert_comp.setObjectName("primaryBtn")
        comps_layout.addWidget(self.btn_insert_comp)

        self.tab_widget.addTab(comps_tab, "Components")

        # 3. Presets Tab
        presets_tab = QWidget()
        presets_layout = QVBoxLayout(presets_tab)
        presets_layout.setContentsMargins(6, 6, 6, 6)
        presets_layout.setSpacing(6)

        lbl_preset_desc = QLabel("Animation & Design Templates")
        lbl_preset_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        presets_layout.addWidget(lbl_preset_desc)

        self.preset_list = QListWidget()
        self._populate_default_presets()
        presets_layout.addWidget(self.preset_list)

        self.btn_apply_preset = QPushButton("Apply Template")
        self.btn_apply_preset.setObjectName("accentBtn")
        presets_layout.addWidget(self.btn_apply_preset)

        self.tab_widget.addTab(presets_tab, "Presets")

    def _connect_signals(self):
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        self.scene.selectionChangedCustom.connect(self._on_scene_selection_changed)
        self.scene.itemAdded.connect(self.refresh_layers)
        self.scene.itemRemoved.connect(self.refresh_layers)
        self.scene.itemModified.connect(self.refresh_layers)

        self.btn_up.clicked.connect(self._move_layer_up)
        self.btn_down.clicked.connect(self._move_layer_down)
        self.btn_delete.clicked.connect(self._delete_selected_layer)
        self.btn_insert_comp.clicked.connect(self._on_insert_component)
        self.btn_apply_preset.clicked.connect(self._on_apply_preset)

    def _populate_default_presets(self):
        presets = [
            ("🎬 Terminal Typing Banner", "terminal_typing"),
            ("✨ Glowing Neon Title", "neon_title"),
            ("📱 Social Post Promo", "social_promo"),
            ("⚡ Quick CTA Card", "cta_card"),
        ]
        for title, key in presets:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.preset_list.addItem(item)

    def refresh_layers(self, *args):
        if self._updating_tree:
            return

        self._updating_tree = True
        self.tree.clear()

        items = self.scene.items()
        # Filter for ResizableItems and sort by Z-value descending (top first)
        design_items = [it for it in items if isinstance(it, ResizableItem)]
        design_items.sort(key=lambda x: x.zValue(), reverse=True)

        for it in design_items:
            icon_symbol = "📄"
            if isinstance(it, ArtboardItem):
                icon_symbol = "🖼️"
            elif isinstance(it, RectangleItem):
                icon_symbol = "⬜"
            elif isinstance(it, EllipseItem):
                icon_symbol = "⚪"
            elif isinstance(it, TextItem):
                icon_symbol = "🔤"
            elif isinstance(it, PathItem):
                icon_symbol = "✒️"

            if it.is_component:
                icon_symbol = "❖"

            tree_item = QTreeWidgetItem([f"{icon_symbol} {it.name}", "👁️" if it.isVisible() else "🙈", "🔒" if it.is_locked else "🔓"])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, it)
            if it.isSelected():
                tree_item.setSelected(True)
            self.tree.addTopLevelItem(tree_item)

        self._refresh_components_list()
        self._updating_tree = False

    def _refresh_components_list(self):
        self.comp_list.clear()
        for comp_id, info in self.scene.components_registry.items():
            item = QListWidgetItem(f"❖ {info['name']}")
            item.setData(Qt.ItemDataRole.UserRole, comp_id)
            self.comp_list.addItem(item)

    def _on_tree_selection_changed(self):
        if self._updating_tree:
            return
        selected_tree_items = self.tree.selectedItems()
        self.scene.blockSignals(True)
        self.scene.clearSelection()
        for t_item in selected_tree_items:
            canvas_item = t_item.data(0, Qt.ItemDataRole.UserRole)
            if canvas_item:
                canvas_item.setSelected(True)
        self.scene.blockSignals(False)
        
        # Trigger inspector update
        selected = [it.data(0, Qt.ItemDataRole.UserRole) for it in selected_tree_items if it.data(0, Qt.ItemDataRole.UserRole)]
        self.scene.selectionChangedCustom.emit(selected)

    def _on_tree_item_clicked(self, item, column):
        canvas_item = item.data(0, Qt.ItemDataRole.UserRole)
        if not canvas_item:
            return

        if column == 1:  # Visibility
            canvas_item.setVisible(not canvas_item.isVisible())
            item.setText(1, "👁️" if canvas_item.isVisible() else "🙈")
            self.scene.update()
        elif column == 2:  # Lock
            canvas_item.is_locked = not canvas_item.is_locked
            item.setText(2, "🔒" if canvas_item.is_locked else "🔓")
            self.scene.update()

    def _on_scene_selection_changed(self, selected_items):
        if self._updating_tree:
            return
        self._updating_tree = True
        self.tree.clearSelection()
        for i in range(self.tree.topLevelItemCount()):
            t_item = self.tree.topLevelItem(i)
            canvas_item = t_item.data(0, Qt.ItemDataRole.UserRole)
            if canvas_item in selected_items:
                t_item.setSelected(True)
        self._updating_tree = False

    def _move_layer_up(self):
        selected = self.scene.selectedItems()
        for it in selected:
            it.setZValue(it.zValue() + 1.0)
        self.refresh_layers()

    def _move_layer_down(self):
        selected = self.scene.selectedItems()
        for it in selected:
            if not isinstance(it, ArtboardItem):
                it.setZValue(it.zValue() - 1.0)
        self.refresh_layers()

    def _delete_selected_layer(self):
        selected = list(self.scene.selectedItems())
        if hasattr(self.scene, "delete_items"):
            self.scene.delete_items(selected)
        else:
            for it in selected:
                if not isinstance(it, ArtboardItem):
                    self.scene.removeItem(it)
                    self.scene.itemRemoved.emit(it)
        self.refresh_layers()

    def _on_insert_component(self):
        curr = self.comp_list.currentItem()
        if curr:
            comp_id = curr.data(Qt.ItemDataRole.UserRole)
            self.insertComponentRequested.emit(comp_id)

    def _on_apply_preset(self):
        curr = self.preset_list.currentItem()
        if curr:
            preset_key = curr.data(Qt.ItemDataRole.UserRole)
            self.createPresetRequested.emit(preset_key)
