"""
Inspector / Properties Panel for Animator
Figma-inspired properties inspector for coordinates, geometry, fill/stroke,
typography, and the crucial 'Create Outlines' vector path conversion.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QPushButton, QSlider, QComboBox, QColorDialog,
    QGroupBox, QScrollArea, QFrame, QFontComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from ui.canvas.items import ResizableItem, TextItem, RectangleItem, EllipseItem, PathItem, ArtboardItem


class InspectorPanel(QWidget):
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.current_item = None
        self._is_updating_ui = False

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        self.layout = QVBoxLayout(scroll_content)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(12)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # 1. Item Header & Name
        header_layout = QHBoxLayout()
        self.lbl_item_type = QLabel("No Selection")
        self.lbl_item_type.setStyleSheet("font-weight: 700; font-size: 13px; color: #f1f5f9;")
        self.btn_create_comp = QPushButton("❖ Create Component")
        self.btn_create_comp.setToolTip("Turn into a reusable Figma component")
        self.btn_create_comp.setStyleSheet("font-size: 11px; padding: 3px 6px;")
        header_layout.addWidget(self.lbl_item_type)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_create_comp)
        self.layout.addLayout(header_layout)

        # 2. Transform Section (X, Y, W, H, Rotation, Opacity)
        gb_transform = QGroupBox("TRANSFORM")
        grid_t = QGridLayout(gb_transform)
        grid_t.setSpacing(6)

        grid_t.addWidget(QLabel("X"), 0, 0)
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-9999, 9999)
        grid_t.addWidget(self.spin_x, 0, 1)

        grid_t.addWidget(QLabel("Y"), 0, 2)
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-9999, 9999)
        grid_t.addWidget(self.spin_y, 0, 3)

        grid_t.addWidget(QLabel("W"), 1, 0)
        self.spin_w = QDoubleSpinBox()
        self.spin_w.setRange(1, 9999)
        grid_t.addWidget(self.spin_w, 1, 1)

        grid_t.addWidget(QLabel("H"), 1, 2)
        self.spin_h = QDoubleSpinBox()
        self.spin_h.setRange(1, 9999)
        grid_t.addWidget(self.spin_h, 1, 3)

        grid_t.addWidget(QLabel("Rot°"), 2, 0)
        self.spin_rot = QDoubleSpinBox()
        self.spin_rot.setRange(-360, 360)
        grid_t.addWidget(self.spin_rot, 2, 1)

        grid_t.addWidget(QLabel("Radius"), 2, 2)
        self.spin_radius = QDoubleSpinBox()
        self.spin_radius.setRange(0, 500)
        grid_t.addWidget(self.spin_radius, 2, 3)

        grid_t.addWidget(QLabel("Opacity"), 3, 0)
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        grid_t.addWidget(self.slider_opacity, 3, 1, 1, 2)
        self.lbl_opacity = QLabel("100%")
        grid_t.addWidget(self.lbl_opacity, 3, 3)

        self.layout.addWidget(gb_transform)

        # 3. Appearance (Fill & Stroke)
        gb_style = QGroupBox("FILL & STROKE")
        v_style = QVBoxLayout(gb_style)
        v_style.setSpacing(8)

        # Fill Row
        h_fill = QHBoxLayout()
        h_fill.addWidget(QLabel("Fill"))
        self.btn_fill_color = QPushButton()
        self.btn_fill_color.setFixedSize(28, 22)
        self.txt_fill_hex = QLineEdit("#3b82f6")
        self.txt_fill_hex.setFixedWidth(80)
        h_fill.addWidget(self.btn_fill_color)
        h_fill.addWidget(self.txt_fill_hex)
        h_fill.addStretch()
        v_style.addLayout(h_fill)

        # Stroke Row
        h_stroke = QHBoxLayout()
        h_stroke.addWidget(QLabel("Stroke"))
        self.btn_stroke_color = QPushButton()
        self.btn_stroke_color.setFixedSize(28, 22)
        self.txt_stroke_hex = QLineEdit("#1d4ed8")
        self.txt_stroke_hex.setFixedWidth(80)
        self.spin_stroke_w = QDoubleSpinBox()
        self.spin_stroke_w.setRange(0, 50)
        self.spin_stroke_w.setValue(1.0)
        self.spin_stroke_w.setFixedWidth(60)
        h_stroke.addWidget(self.btn_stroke_color)
        h_stroke.addWidget(self.txt_stroke_hex)
        h_stroke.addWidget(self.spin_stroke_w)
        v_style.addLayout(h_stroke)

        self.layout.addWidget(gb_style)

        # 4. Typography & Outlines (Only for TextItem)
        self.gb_text = QGroupBox("TEXT & OUTLINES")
        v_text = QVBoxLayout(self.gb_text)
        v_text.setSpacing(8)

        v_text.addWidget(QLabel("Content"))
        self.txt_content = QLineEdit()
        v_text.addWidget(self.txt_content)

        h_font = QHBoxLayout()
        self.combo_font = QFontComboBox()
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(6, 200)
        self.spin_font_size.setValue(28)
        h_font.addWidget(self.combo_font)
        h_font.addWidget(self.spin_font_size)
        v_text.addLayout(h_font)

        h_style_btn = QHBoxLayout()
        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedWidth(36)
        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedWidth(36)
        h_style_btn.addWidget(self.btn_bold)
        h_style_btn.addWidget(self.btn_italic)
        h_style_btn.addStretch()
        v_text.addLayout(h_style_btn)

        # Create Outlines Button (High priority requirement)
        self.btn_create_outlines = QPushButton("⚡ Create Outlines (Vectorize)")
        self.btn_create_outlines.setObjectName("accentBtn")
        self.btn_create_outlines.setToolTip("Convert text into native SVG vector path shapes")
        v_text.addWidget(self.btn_create_outlines)

        self.layout.addWidget(self.gb_text)

        self.layout.addStretch()
        self.setEnabled(False)

    def _connect_signals(self):
        self.scene.selectionChangedCustom.connect(self._on_selection_changed)
        self.scene.itemModified.connect(self._on_item_modified)

        # Transforms
        self.spin_x.valueChanged.connect(self._apply_transform)
        self.spin_y.valueChanged.connect(self._apply_transform)
        self.spin_w.valueChanged.connect(self._apply_transform)
        self.spin_h.valueChanged.connect(self._apply_transform)
        self.spin_rot.valueChanged.connect(self._apply_transform)
        self.spin_radius.valueChanged.connect(self._apply_radius)
        self.slider_opacity.valueChanged.connect(self._apply_opacity)

        # Colors
        self.btn_fill_color.clicked.connect(self._pick_fill_color)
        self.btn_stroke_color.clicked.connect(self._pick_stroke_color)
        self.txt_fill_hex.editingFinished.connect(self._apply_fill_hex)
        self.txt_stroke_hex.editingFinished.connect(self._apply_stroke_hex)
        self.spin_stroke_w.valueChanged.connect(self._apply_stroke_width)

        # Text
        self.txt_content.textChanged.connect(self._apply_text_content)
        self.combo_font.currentFontChanged.connect(self._apply_font)
        self.spin_font_size.valueChanged.connect(self._apply_font)
        self.btn_bold.toggled.connect(self._apply_font)
        self.btn_italic.toggled.connect(self._apply_font)
        self.btn_create_outlines.clicked.connect(self._on_create_outlines)

        # Component
        self.btn_create_comp.clicked.connect(self._on_make_component)

    def _on_selection_changed(self, selected_items):
        if not selected_items:
            self.current_item = None
            self.lbl_item_type.setText("No Selection")
            self.setEnabled(False)
            return

        self.current_item = selected_items[0]
        self.setEnabled(True)
        self.populate_item_values(self.current_item)

    def _on_item_modified(self, item):
        if item == self.current_item and not self._is_updating_ui:
            self.populate_item_values(item)

    def populate_item_values(self, item: ResizableItem):
        self._is_updating_ui = True

        type_name = type(item).__name__.replace("Item", "")
        if item.is_component:
            type_name = f"❖ {type_name} (Component)"
        self.lbl_item_type.setText(type_name)

        # Transform
        self.spin_x.setValue(item.x())
        self.spin_y.setValue(item.y())
        self.spin_w.setValue(item.w)
        self.spin_h.setValue(item.h)
        self.spin_rot.setValue(item.rotation())
        self.spin_radius.setValue(getattr(item, "border_radius", 0.0))
        op_val = int(item.opacity_val * 100)
        self.slider_opacity.setValue(op_val)
        self.lbl_opacity.setText(f"{op_val}%")

        # Fill & Stroke
        self._update_color_button(self.btn_fill_color, item.fill_color)
        self.txt_fill_hex.setText(item.fill_color.name())
        self._update_color_button(self.btn_stroke_color, item.stroke_color)
        self.txt_stroke_hex.setText(item.stroke_color.name())
        self.spin_stroke_w.setValue(item.stroke_width)

        # Text Section Visibility
        is_text = isinstance(item, TextItem)
        self.gb_text.setVisible(is_text)
        if is_text:
            self.txt_content.setText(item.text)
            self.combo_font.setCurrentFont(QFont(item.font_family))
            self.spin_font_size.setValue(int(item.font_size))
            self.btn_bold.setChecked(item.font_bold)
            self.btn_italic.setChecked(item.font_italic)

        self._is_updating_ui = False

    def _update_color_button(self, btn: QPushButton, color: QColor):
        btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #4a4a58; border-radius: 4px;")

    def _apply_transform(self):
        if self._is_updating_ui or not self.current_item:
            return
        self.current_item.setPos(self.spin_x.value(), self.spin_y.value())
        self.current_item.prepareGeometryChange()
        self.current_item.w = max(5.0, self.spin_w.value())
        self.current_item.h = max(5.0, self.spin_h.value())
        self.current_item.setRotation(self.spin_rot.value())
        self.current_item.update()
        self.scene.itemModified.emit(self.current_item)

    def _apply_radius(self):
        if self._is_updating_ui or not self.current_item:
            return
        if hasattr(self.current_item, "border_radius"):
            self.current_item.border_radius = self.spin_radius.value()
            self.current_item.update()

    def _apply_opacity(self, val):
        if self._is_updating_ui or not self.current_item:
            return
        self.lbl_opacity.setText(f"{val}%")
        self.current_item.opacity_val = val / 100.0
        self.current_item.update()

    def _pick_fill_color(self):
        if not self.current_item:
            return
        col = QColorDialog.getColor(self.current_item.fill_color, self, "Pick Fill Color")
        if col.isValid():
            self.current_item.fill_color = col
            self._update_color_button(self.btn_fill_color, col)
            self.txt_fill_hex.setText(col.name())
            self.current_item.update()

    def _pick_stroke_color(self):
        if not self.current_item:
            return
        col = QColorDialog.getColor(self.current_item.stroke_color, self, "Pick Stroke Color")
        if col.isValid():
            self.current_item.stroke_color = col
            self._update_color_button(self.btn_stroke_color, col)
            self.txt_stroke_hex.setText(col.name())
            self.current_item.update()

    def _apply_fill_hex(self):
        if not self.current_item:
            return
        c = QColor(self.txt_fill_hex.text())
        if c.isValid():
            self.current_item.fill_color = c
            self._update_color_button(self.btn_fill_color, c)
            self.current_item.update()

    def _apply_stroke_hex(self):
        if not self.current_item:
            return
        c = QColor(self.txt_stroke_hex.text())
        if c.isValid():
            self.current_item.stroke_color = c
            self._update_color_button(self.btn_stroke_color, c)
            self.current_item.update()

    def _apply_stroke_width(self, val):
        if self._is_updating_ui or not self.current_item:
            return
        self.current_item.stroke_width = val
        self.current_item.update()

    def _apply_text_content(self, text):
        if self._is_updating_ui or not isinstance(self.current_item, TextItem):
            return
        self.current_item.text = text
        self.current_item.adjust_size_to_text()
        self.current_item.update()

    def _apply_font(self):
        if self._is_updating_ui or not isinstance(self.current_item, TextItem):
            return
        self.current_item.font_family = self.combo_font.currentFont().family()
        self.current_item.font_size = float(self.spin_font_size.value())
        self.current_item.font_bold = self.btn_bold.isChecked()
        self.current_item.font_italic = self.btn_italic.isChecked()
        self.current_item.adjust_size_to_text()
        self.current_item.update()

    def _on_create_outlines(self):
        """User clicked 'Create Outlines': converts Text to PathItem."""
        if isinstance(self.current_item, TextItem):
            new_path_item = self.scene.create_outline_for_item(self.current_item)
            self.current_item = new_path_item
            self.populate_item_values(new_path_item)

    def _on_make_component(self):
        if self.current_item:
            self.scene.make_component(self.current_item)
            self.populate_item_values(self.current_item)
