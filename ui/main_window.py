"""
Main Application Window for Animator
Combines Figma-style infinite vector canvas with Premiere-style video timeline,
dedicated vertical SVG animation side panel, and typography tools.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QToolButton,
    QDockWidget, QLabel, QPushButton, QButtonGroup, QStatusBar, QMessageBox,
    QApplication, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QIcon, QKeySequence, QShortcut, QColor

from ui.canvas.canvas_scene import CanvasScene
from ui.canvas.canvas_view import CanvasView
from ui.canvas.items import RectangleItem, EllipseItem, TextItem, ArtboardItem
from ui.panels.layers_panel import LayersPanel
from ui.panels.inspector_panel import InspectorPanel
from ui.panels.animation_panel import AnimationSidePanel
from ui.panels.timeline_panel import TimelinePanel
from ui.theme import DARK_THEME_QSS
from core.undo_manager import UndoManager
from ui.components.font_picker_dialog import FontPickerDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Animator - Vector & SVG Animation Studio")
        self.resize(1440, 900)
        self.setMinimumSize(1000, 700)

        # Apply dark theme
        self.setStyleSheet(DARK_THEME_QSS)

        # Undo / Redo Manager
        self.undo_manager = UndoManager()

        # Core Components
        self.scene = CanvasScene(self.undo_manager, self)
        self.view = CanvasView(self.scene, self)

        self._setup_ui()
        self._setup_menus_and_toolbars()
        self._setup_shortcuts()
        self._connect_sync_signals()

        # Initialize canvas with a default Figma-style artboard
        self.scene.set_default_artboard(800, 500)
        self._create_initial_demo_content()
        self.layers_panel.refresh_layers()

    def _setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Central Splitter (Canvas + Bottom Timeline)
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.v_splitter.addWidget(self.view)

        # Bottom Timeline Panel (Video Editing Style)
        self.timeline_panel = TimelinePanel(self.scene, self)
        self.timeline_panel.setMinimumHeight(150)
        self.v_splitter.addWidget(self.timeline_panel)
        self.v_splitter.setSizes([650, 200])

        main_layout.addWidget(self.v_splitter)
        self.setCentralWidget(central_widget)

        # Left Dock: Layers, Components & Presets
        self.dock_left = QDockWidget("LAYERS & ASSETS", self)
        self.dock_left.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.dock_left.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.layers_panel = LayersPanel(self.scene, self)
        self.dock_left.setWidget(self.layers_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_left)

        # Right Dock: Always-Accessible Tabs for Design Inspector & SVG Animation Studio
        self.dock_right = QDockWidget("INSPECTOR & ANIMATION", self)
        self.dock_right.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.dock_right.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)

        # Right tab widget holding Inspector and Animation Studio
        self.right_tab_widget = QTabWidget()
        self.inspector_panel = InspectorPanel(self.scene, self)
        self.animation_panel = AnimationSidePanel(self.scene, self.view, self)

        self.right_tab_widget.addTab(self.inspector_panel, "Design")
        self.right_tab_widget.addTab(self.animation_panel, "⚡ Animation Studio")
        self.right_tab_widget.setCurrentIndex(1)  # Default to Animation Studio as requested

        self.dock_right.setWidget(self.right_tab_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_right)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.lbl_status_zoom = QLabel("100%")
        self.lbl_status_info = QLabel("Ready | Alt+Drag: Duplicate | Space+Drag: Pan | Scroll: Zoom")
        self.status_bar.addWidget(self.lbl_status_info, 1)
        self.status_bar.addPermanentWidget(self.lbl_status_zoom)

    def _setup_menus_and_toolbars(self):
        toolbar = QToolBar("Main Tools", self)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # App Brand
        lbl_app = QLabel(" ⚡ Animator ")
        lbl_app.setStyleSheet("font-weight: 900; font-size: 14px; color: #38bdf8; padding-right: 12px;")
        toolbar.addWidget(lbl_app)

        # Tool selection group
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)

        tools = [
            ("Select (V)", "select", True),
            ("Rectangle (R)", "rect", False),
            ("Ellipse (O)", "ellipse", False),
            ("Text (T)", "text", False),
        ]

        for name, tool_id, checked in tools:
            btn = QToolButton()
            btn.setText(name)
            btn.setCheckable(True)
            btn.setChecked(checked)
            btn.clicked.connect(lambda chk=False, t=tool_id: self._on_tool_selected(t))
            self.tool_group.addButton(btn)
            toolbar.addWidget(btn)

        toolbar.addSeparator()

        # Undo / Redo Actions
        self.btn_undo = QToolButton()
        self.btn_undo.setText("↶ Undo")
        self.btn_undo.setToolTip("Undo (Ctrl+Z)")
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo_manager.undo)
        toolbar.addWidget(self.btn_undo)

        self.btn_redo = QToolButton()
        self.btn_redo.setText("↷ Redo")
        self.btn_redo.setToolTip("Redo (Ctrl+Shift+Z)")
        self.btn_redo.setEnabled(False)
        self.btn_redo.clicked.connect(self.undo_manager.redo)
        toolbar.addWidget(self.btn_redo)

        self.undo_manager.canUndoChanged.connect(self.btn_undo.setEnabled)
        self.undo_manager.canRedoChanged.connect(self.btn_redo.setEnabled)

        toolbar.addSeparator()

        # Vector & Figma Actions
        self.btn_outline = QToolButton()
        self.btn_outline.setText("⚡ Create Outlines")
        self.btn_outline.setToolTip("Convert selected Text into Vector Path Outlines")
        self.btn_outline.clicked.connect(self._create_outline_from_toolbar)
        toolbar.addWidget(self.btn_outline)

        self.btn_font_modal = QToolButton()
        self.btn_font_modal.setText("🔤 Font Picker")
        self.btn_font_modal.setToolTip("Open full-featured Typography & Font Picker modal")
        self.btn_font_modal.clicked.connect(self._open_font_picker_from_toolbar)
        toolbar.addWidget(self.btn_font_modal)

        self.btn_comp = QToolButton()
        self.btn_comp.setText("❖ Component")
        self.btn_comp.setToolTip("Turn selected shape into reusable Component")
        self.btn_comp.clicked.connect(self._create_component_from_toolbar)
        toolbar.addWidget(self.btn_comp)

        toolbar.addSeparator()

        # Playback toggle on toolbar
        self.btn_tb_play = QToolButton()
        self.btn_tb_play.setText("▶ Play Loop")
        self.btn_tb_play.setStyleSheet("color: #38bdf8; font-weight: bold;")
        self.btn_tb_play.clicked.connect(self.animation_panel.toggle_play)
        toolbar.addWidget(self.btn_tb_play)

        # Quick Export Buttons
        toolbar.addSeparator()
        btn_exp_svg = QToolButton()
        btn_exp_svg.setText("🚀 SVG")
        btn_exp_svg.setToolTip("Export Looping Animated SVG")
        btn_exp_svg.clicked.connect(self.animation_panel._export_animated_svg)
        toolbar.addWidget(btn_exp_svg)

        btn_exp_gif = QToolButton()
        btn_exp_gif.setText("🎞️ GIF")
        btn_exp_gif.setToolTip("Export Looping GIF")
        btn_exp_gif.clicked.connect(self.animation_panel._export_gif)
        toolbar.addWidget(btn_exp_gif)

        # Zoom Controller on Right
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Policy.Expanding, spacer.sizePolicy().Policy.Preferred)
        toolbar.addWidget(spacer)

        self.btn_reset_zoom = QToolButton()
        self.btn_reset_zoom.setText("100%")
        self.btn_reset_zoom.clicked.connect(self.view.reset_zoom)
        toolbar.addWidget(self.btn_reset_zoom)

    def _setup_shortcuts(self):
        # Undo / Redo
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo_manager.undo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self.undo_manager.redo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.undo_manager.redo)

        # Tools
        QShortcut(QKeySequence(Qt.Key.Key_V), self, lambda: self._select_tool_by_id("select"))
        QShortcut(QKeySequence(Qt.Key.Key_R), self, lambda: self._select_tool_by_id("rect"))
        QShortcut(QKeySequence(Qt.Key.Key_O), self, lambda: self._select_tool_by_id("ellipse"))
        QShortcut(QKeySequence(Qt.Key.Key_T), self, lambda: self._select_tool_by_id("text"))

        # Space to toggle play/pause when not editing text
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._on_space_pressed)

        # Delete / Backspace
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self.layers_panel._delete_selected_layer)
        QShortcut(QKeySequence(Qt.Key.Key_Backspace), self, self.layers_panel._delete_selected_layer)

        # Duplicate (Ctrl + D)
        QShortcut(QKeySequence("Ctrl+D"), self, self._duplicate_selected)

    def _on_space_pressed(self):
        # If focus is on QLineEdit or QTextEdit, allow regular typing
        focus_w = QApplication.focusWidget()
        if hasattr(focus_w, "text") or hasattr(focus_w, "toPlainText"):
            return
        self.animation_panel.toggle_play()

    def _connect_sync_signals(self):
        # View zoom update
        self.view.zoomChanged.connect(self._on_zoom_changed)

        # Timeline and Animation Panel synchronization
        self.animation_panel.playStateChanged.connect(self._on_play_state_synced)
        self.animation_panel.seekProgressChanged.connect(self.timeline_panel.set_progress)

        self.timeline_panel.playToggled.connect(self._on_timeline_play_toggled)
        self.timeline_panel.seekChanged.connect(self.animation_panel.set_progress)

        # Presets and Components
        self.layers_panel.createPresetRequested.connect(self._apply_preset_template)
        self.layers_panel.insertComponentRequested.connect(self._insert_component_instance)

    def _on_tool_selected(self, tool_id: str):
        self.view.set_tool(tool_id)

    def _select_tool_by_id(self, tool_id: str):
        for btn in self.tool_group.buttons():
            if tool_id in btn.text().lower():
                btn.setChecked(True)
                self.view.set_tool(tool_id)
                break

    def _on_zoom_changed(self, zoom_pct: float):
        txt = f"{int(zoom_pct)}%"
        self.btn_reset_zoom.setText(txt)
        self.lbl_status_zoom.setText(txt)

    def _on_play_state_synced(self, is_playing: bool):
        self.timeline_panel.set_playing(is_playing)
        self.btn_tb_play.setText("⏸ Pause" if is_playing else "▶ Play Loop")

    def _on_timeline_play_toggled(self, is_playing: bool):
        if is_playing:
            self.animation_panel.play()
        else:
            self.animation_panel.pause()

    def _create_outline_from_toolbar(self):
        selected = self.scene.selectedItems()
        for it in selected:
            if isinstance(it, TextItem):
                self.scene.create_outline_for_item(it)
                self.status_bar.showMessage("Text converted to Vector Path Outlines!", 3000)
                return
        QMessageBox.information(self, "Create Outlines", "Please select a Text item on the canvas to vectorize.")

    def _open_font_picker_from_toolbar(self):
        selected = self.scene.selectedItems()
        target_text = None
        for it in selected:
            if isinstance(it, TextItem):
                target_text = it
                break
        if not target_text:
            for it in self.scene.items():
                if isinstance(it, TextItem):
                    target_text = it
                    break
        family = target_text.font_family if target_text else "Segoe UI"
        dlg = FontPickerDialog(family, target_item=target_text, parent=self)
        if dlg.exec() and target_text:
            target_text.font_family = dlg.current_family
            target_text.adjust_size_to_text()
            target_text.update()
            self.scene.update()
            self.scene.itemModified.emit(target_text)
            self.status_bar.showMessage(f"Font changed to '{dlg.current_family}'", 3000)

    def _create_component_from_toolbar(self):
        selected = self.scene.selectedItems()
        if selected:
            self.scene.make_component(selected[0])
            self.status_bar.showMessage(f"Component '{selected[0].name}' created!", 3000)

    def _duplicate_selected(self):
        selected = self.scene.selectedItems()
        for it in selected:
            self.scene.duplicate_item(it)

    def _insert_component_instance(self, comp_id: str):
        self.scene.instantiate_component(comp_id, QPointF(0, 0))

    def _apply_preset_template(self, preset_key: str):
        """Build ready-to-animate scenes based on chosen template."""
        if preset_key == "terminal_typing":
            # Terminal background card
            term_bg = RectangleItem(-300, -120, 600, 240, "Terminal Card")
            term_bg.fill_color = QColor("#0d1117")
            term_bg.stroke_color = QColor("#30363d")
            term_bg.border_radius = 12.0
            self.scene.addItem(term_bg)
            self.scene.itemAdded.emit(term_bg)

            # Terminal header dots
            dot_colors = ["#ff5f56", "#ffbd2e", "#27c93f"]
            for i, col in enumerate(dot_colors):
                dot = EllipseItem(-280 + i * 18, -105, 10, 10, f"Dot {i+1}")
                dot.fill_color = QColor(col)
                dot.stroke_width = 0
                self.scene.addItem(dot)
                self.scene.itemAdded.emit(dot)

            # Code text
            code_text = TextItem(-280, -60, "const animator = new SVGStudio();", "Typing Code")
            code_text.font_family = "Consolas"
            code_text.font_size = 20.0
            code_text.fill_color = QColor("#58a6ff")
            code_text.cursor_char = "█"
            code_text.adjust_size_to_text()
            self.scene.addItem(code_text)
            self.scene.itemAdded.emit(code_text)

        elif preset_key == "neon_title":
            bg = RectangleItem(-320, -90, 640, 180, "Neon Glow Frame")
            bg.fill_color = QColor("#09090b")
            bg.stroke_color = QColor("#ec4899")
            bg.stroke_width = 3.0
            bg.border_radius = 20.0
            self.scene.addItem(bg)
            self.scene.itemAdded.emit(bg)

            title = TextItem(-270, -30, "NEON VECTOR ANIMATION", "Neon Text")
            title.font_family = "Segoe UI"
            title.font_size = 32.0
            title.font_bold = True
            title.fill_color = QColor("#f43f5e")
            title.adjust_size_to_text()
            self.scene.addItem(title)
            self.scene.itemAdded.emit(title)

        self.layers_panel.refresh_layers()

    def _create_initial_demo_content(self):
        """Populate canvas with an aesthetic starter project."""
        # 1. Main Background Card
        bg_card = RectangleItem(-320, -140, 640, 280, "Hero Banner Card")
        bg_card.fill_color = QColor("#1e1e2d")
        bg_card.stroke_color = QColor("#0d99ff")
        bg_card.stroke_width = 2.0
        bg_card.border_radius = 16.0
        self.scene.addItem(bg_card)

        # 2. Decorative geometric accents
        acc_circle = EllipseItem(210, -110, 80, 80, "Accent Orb")
        acc_circle.fill_color = QColor("#0d99ff")
        acc_circle.opacity_val = 0.25
        acc_circle.stroke_width = 0
        self.scene.addItem(acc_circle)

        # 3. Main Title
        title_item = TextItem(-280, -95, "Figma & Video-Style SVG Animator", "Title Text")
        title_item.font_family = "Segoe UI"
        title_item.font_size = 26.0
        title_item.font_bold = True
        title_item.fill_color = QColor("#ffffff")
        title_item.enable_typing_anim = False
        title_item.adjust_size_to_text()
        self.scene.addItem(title_item)

        # 4. Animated Typing Text
        typing_item = TextItem(-280, -25, "Crafting seamless vector typing animations...", "Typing Effect Text")
        typing_item.font_family = "Consolas"
        typing_item.font_size = 20.0
        typing_item.font_bold = False
        typing_item.fill_color = QColor("#38bdf8")
        typing_item.enable_typing_anim = True
        typing_item.show_cursor = True
        typing_item.cursor_char = "█"
        typing_item.adjust_size_to_text()
        self.scene.addItem(typing_item)

        # 5. Outlined Badge
        btn_badge = RectangleItem(-280, 50, 200, 42, "Action Badge")
        btn_badge.fill_color = QColor("#0d99ff")
        btn_badge.stroke_color = QColor("#0284c7")
        btn_badge.border_radius = 8.0
        self.scene.addItem(btn_badge)

        btn_text = TextItem(-250, 58, "Create Outlines", "Badge Text")
        btn_text.font_family = "Segoe UI"
        btn_text.font_size = 14.0
        btn_text.font_bold = True
        btn_text.fill_color = QColor("#ffffff")
        btn_text.enable_typing_anim = False
        btn_text.adjust_size_to_text()
        self.scene.addItem(btn_text)

        # Select the typing item by default
        typing_item.setSelected(True)
