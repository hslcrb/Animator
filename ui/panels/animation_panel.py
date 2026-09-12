"""
Animation Vertical Side Panel for Animator
Always accessible side panel dedicated to SVG Typing Animations, looping GIF controls,
and animated background text banners.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QSlider, QCheckBox, QComboBox, QGroupBox, QSpinBox,
    QDoubleSpinBox, QColorDialog, QFileDialog, QMessageBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont
from ui.canvas.items import TextItem, RectangleItem, ArtboardItem
from core.svg_exporter import export_animated_svg, export_static_svg
from core.gif_exporter import export_looping_gif


class AnimationSidePanel(QWidget):
    # Signals to control global timeline
    playStateChanged = Signal(bool)
    seekProgressChanged = Signal(float)  # 0.0 to 1.0

    def __init__(self, scene, canvas_view, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.canvas_view = canvas_view

        # Animation playback timer for preview
        self.is_playing = False
        self.current_time_ms = 0
        self.total_duration_ms = 3000
        self.timer = QTimer(self)
        self.timer.setInterval(33)  # ~30 FPS
        self.timer.timeout.connect(self._on_tick)

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
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Title / Badge
        title_box = QHBoxLayout()
        lbl_badge = QLabel("⚡ SVG ANIMATION STUDIO")
        lbl_badge.setStyleSheet("font-weight: 800; font-size: 12px; color: #38bdf8; letter-spacing: 0.5px;")
        title_box.addWidget(lbl_badge)
        title_box.addStretch()
        layout.addLayout(title_box)

        # 1. Typing Animation Generator
        gb_typing = QGroupBox("TYPING ANIMATION")
        v_typing = QVBoxLayout(gb_typing)
        v_typing.setSpacing(8)

        v_typing.addWidget(QLabel("Typing Text:"))
        self.txt_typing_input = QTextEdit()
        self.txt_typing_input.setPlaceholderText("Enter text for typewriter effect...")
        self.txt_typing_input.setText("Crafting Vector Magic with Animator...")
        self.txt_typing_input.setMaximumHeight(60)
        v_typing.addWidget(self.txt_typing_input)

        # Speed and duration
        h_speed = QHBoxLayout()
        h_speed.addWidget(QLabel("Duration:"))
        self.spin_duration = QDoubleSpinBox()
        self.spin_duration.setRange(0.5, 30.0)
        self.spin_duration.setSingleStep(0.5)
        self.spin_duration.setValue(3.0)
        self.spin_duration.setSuffix(" s")
        h_speed.addWidget(self.spin_duration)

        h_speed.addWidget(QLabel("Delay:"))
        self.spin_delay = QDoubleSpinBox()
        self.spin_delay.setRange(0.0, 10.0)
        self.spin_delay.setSingleStep(0.5)
        self.spin_delay.setValue(1.0)
        self.spin_delay.setSuffix(" s")
        h_speed.addWidget(self.spin_delay)
        v_typing.addLayout(h_speed)

        # Cursor options
        h_cursor = QHBoxLayout()
        self.chk_cursor = QCheckBox("Show Cursor")
        self.chk_cursor.setChecked(True)
        self.combo_cursor = QComboBox()
        self.combo_cursor.addItems(["| (Bar)", "_ (Underscore)", "█ (Block)"])
        h_cursor.addWidget(self.chk_cursor)
        h_cursor.addWidget(self.combo_cursor)
        v_typing.addLayout(h_cursor)

        # Buttons to create
        self.btn_insert_text = QPushButton("+ Add Typing Text")
        self.btn_insert_text.setObjectName("primaryBtn")
        self.btn_create_banner = QPushButton("🎬 Create Background Banner + Typing")
        self.btn_create_banner.setObjectName("accentBtn")
        v_typing.addWidget(self.btn_insert_text)
        v_typing.addWidget(self.btn_create_banner)

        layout.addWidget(gb_typing)

        # 2. Live Playback & Loop Preview
        gb_preview = QGroupBox("PREVIEW & PLAYBACK")
        v_prev = QVBoxLayout(gb_preview)
        v_prev.setSpacing(8)

        h_play = QHBoxLayout()
        self.btn_play_pause = QPushButton("▶ Play Loop")
        self.btn_play_pause.setObjectName("primaryBtn")
        self.btn_reset = QPushButton("⏮ Reset")
        h_play.addWidget(self.btn_play_pause)
        h_play.addWidget(self.btn_reset)
        v_prev.addLayout(h_play)

        # Scrubber
        h_scrub = QHBoxLayout()
        h_scrub.addWidget(QLabel("Progress:"))
        self.slider_progress = QSlider(Qt.Orientation.Horizontal)
        self.slider_progress.setRange(0, 1000)
        self.slider_progress.setValue(1000)
        self.lbl_progress = QLabel("100%")
        self.lbl_progress.setFixedWidth(40)
        h_scrub.addWidget(self.slider_progress)
        h_scrub.addWidget(self.lbl_progress)
        v_prev.addLayout(h_scrub)

        self.chk_loop = QCheckBox("Loop Continuously (GIF style)")
        self.chk_loop.setChecked(True)
        v_prev.addWidget(self.chk_loop)

        layout.addWidget(gb_preview)

        # 3. Export Studio
        gb_export = QGroupBox("EXPORT STUDIO")
        v_exp = QVBoxLayout(gb_export)
        v_exp.setSpacing(8)

        lbl_exp_desc = QLabel("Export directly to browser-ready animated SVG or looping GIF:")
        lbl_exp_desc.setWordWrap(True)
        lbl_exp_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        v_exp.addWidget(lbl_exp_desc)

        self.btn_export_anim_svg = QPushButton("🚀 Export Animated SVG (SMIL/CSS)")
        self.btn_export_anim_svg.setObjectName("primaryBtn")
        self.btn_export_anim_svg.setToolTip("Export SVG with native CSS typewriter keyframes that loop in any browser")

        self.btn_export_gif = QPushButton("🎞️ Export Looping GIF")
        self.btn_export_gif.setObjectName("accentBtn")
        self.btn_export_gif.setToolTip("Render canvas sequence into an optimized looping GIF")

        self.btn_export_static_svg = QPushButton("📄 Export Clean Static SVG")
        self.btn_export_static_svg.setToolTip("Standard clean vector SVG format")

        v_exp.addWidget(self.btn_export_anim_svg)
        v_exp.addWidget(self.btn_export_gif)
        v_exp.addWidget(self.btn_export_static_svg)

        layout.addWidget(gb_export)
        layout.addStretch()

    def _connect_signals(self):
        self.btn_insert_text.clicked.connect(self._on_insert_typing_text)
        self.btn_create_banner.clicked.connect(self._on_create_banner)
        self.btn_play_pause.clicked.connect(self.toggle_play)
        self.btn_reset.clicked.connect(self.reset_playback)
        self.slider_progress.sliderMoved.connect(self._on_slider_moved)
        self.spin_duration.valueChanged.connect(self._update_timing)

        self.btn_export_anim_svg.clicked.connect(self._export_animated_svg)
        self.btn_export_gif.clicked.connect(self._export_gif)
        self.btn_export_static_svg.clicked.connect(self._export_static_svg)

    def _update_timing(self):
        self.total_duration_ms = int(self.spin_duration.value() * 1000)

    def _get_cursor_char(self) -> str:
        idx = self.combo_cursor.currentIndex()
        if idx == 0:
            return "|"
        elif idx == 1:
            return "_"
        elif idx == 2:
            return "█"
        return "|"

    def _on_insert_typing_text(self):
        text = self.txt_typing_input.toPlainText().strip() or "Typing Animation Text"
        txt_item = TextItem(0, 0, text, "Typing Text")
        txt_item.show_cursor = self.chk_cursor.isChecked()
        txt_item.cursor_char = self._get_cursor_char()
        txt_item.font_family = "Consolas"
        txt_item.font_size = 32.0
        txt_item.fill_color = QColor("#38bdf8")
        txt_item.adjust_size_to_text()

        self.scene.addItem(txt_item)
        self.scene.clearSelection()
        txt_item.setSelected(True)
        self.scene.itemAdded.emit(txt_item)

    def _on_create_banner(self):
        """Create a stylized background card with animated typing text on top."""
        bg = RectangleItem(-300, -100, 600, 200, "Banner Background")
        bg.fill_color = QColor("#0f172a")
        bg.stroke_color = QColor("#38bdf8")
        bg.stroke_width = 2.0
        bg.border_radius = 16.0
        self.scene.addItem(bg)
        self.scene.itemAdded.emit(bg)

        text = self.txt_typing_input.toPlainText().strip() or "Vector Animation with PySide6 & SVG"
        txt_item = TextItem(-270, -20, text, "Banner Text")
        txt_item.font_family = "Consolas"
        txt_item.font_size = 24.0
        txt_item.fill_color = QColor("#38bdf8")
        txt_item.show_cursor = self.chk_cursor.isChecked()
        txt_item.cursor_char = self._get_cursor_char()
        txt_item.adjust_size_to_text()

        self.scene.addItem(txt_item)
        self.scene.itemAdded.emit(txt_item)

        self.scene.clearSelection()
        txt_item.setSelected(True)

    def toggle_play(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        self.is_playing = True
        self.btn_play_pause.setText("⏸ Pause")
        self.total_duration_ms = int(self.spin_duration.value() * 1000)
        self.timer.start()
        self.playStateChanged.emit(True)

    def pause(self):
        self.is_playing = False
        self.btn_play_pause.setText("▶ Play Loop")
        self.timer.stop()
        self.playStateChanged.emit(False)

    def reset_playback(self):
        self.pause()
        self.current_time_ms = 0
        self.set_progress(0.0)

    def _on_tick(self):
        self.current_time_ms += 33
        delay_ms = int(self.spin_delay.value() * 1000)
        cycle_ms = self.total_duration_ms + delay_ms

        if self.current_time_ms >= cycle_ms:
            if self.chk_loop.isChecked():
                self.current_time_ms = 0
            else:
                self.pause()
                self.current_time_ms = cycle_ms

        typing_time = min(self.current_time_ms, self.total_duration_ms)
        progress = typing_time / max(1, self.total_duration_ms)
        self.set_progress(progress, update_slider=True)

    def _on_slider_moved(self, val):
        progress = val / 1000.0
        self.current_time_ms = int(progress * self.total_duration_ms)
        self.set_progress(progress, update_slider=False)

    def set_progress(self, progress: float, update_slider=True):
        progress = max(0.0, min(1.0, progress))
        if update_slider:
            self.slider_progress.blockSignals(True)
            self.slider_progress.setValue(int(progress * 1000))
            self.slider_progress.blockSignals(False)

        self.lbl_progress.setText(f"{int(progress * 100)}%")

        # Update all TextItems on scene with typing progress
        for it in self.scene.items():
            if isinstance(it, TextItem) and it.enable_typing_anim:
                it.typing_progress = progress
                it.update()

        self.seekProgressChanged.emit(progress)

    def _export_animated_svg(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Animated SVG", "typing_animation.svg", "SVG Files (*.svg)")
        if not filepath:
            return

        success, msg = export_animated_svg(
            self.scene,
            filepath,
            duration=self.spin_duration.value(),
            delay=self.spin_delay.value(),
            cursor_char=self._get_cursor_char() if self.chk_cursor.isChecked() else ""
        )
        if success:
            QMessageBox.information(self, "Export Success", f"Animated SVG saved successfully!\nOpen in any browser to see it looping:\n{filepath}")
        else:
            QMessageBox.critical(self, "Export Failed", f"Failed to export animated SVG:\n{msg}")

    def _export_static_svg(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Clean SVG", "design.svg", "SVG Files (*.svg)")
        if not filepath:
            return

        success, msg = export_static_svg(self.scene, filepath)
        if success:
            QMessageBox.information(self, "Export Success", f"Clean SVG saved successfully:\n{filepath}")
        else:
            QMessageBox.critical(self, "Export Failed", f"Failed to export SVG:\n{msg}")

    def _export_gif(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Looping GIF", "animation.gif", "GIF Files (*.gif)")
        if not filepath:
            return

        # Render looping frames
        success, msg = export_looping_gif(
            self.scene,
            filepath,
            duration=self.spin_duration.value(),
            delay=self.spin_delay.value(),
            fps=24,
            panel=self
        )
        if success:
            QMessageBox.information(self, "Export Success", f"Looping GIF saved successfully:\n{filepath}")
        else:
            QMessageBox.critical(self, "Export Failed", f"Failed to export GIF:\n{msg}")
