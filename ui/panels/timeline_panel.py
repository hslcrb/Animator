"""
Timeline Panel for Animator
Video editing style timeline (like Premiere / After Effects) with tracks,
ruler, scrubbing playhead, and timecode display.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QMouseEvent, QPolygonF
from ui.canvas.items import TextItem, ResizableItem


class TimelineRulerAndTracks(QWidget):
    timeChanged = Signal(float)  # current time in seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_duration = 4.0  # seconds
        self.current_time = 0.0    # seconds
        self.px_per_sec = 160.0
        self.header_width = 160
        self.ruler_height = 28
        self.track_height = 36
        self.tracks = [
            {"name": "🔤 Typing Text Track", "color": "#0284c7"},
            {"name": "🖼️ Background Artboard", "color": "#475569"},
            {"name": "📐 Vector Shape Elements", "color": "#9333ea"},
        ]
        self.setMinimumHeight(self.ruler_height + len(self.tracks) * self.track_height + 10)
        self.setMouseTracking(True)
        self._dragging_playhead = False

    def set_duration(self, sec: float):
        self.total_duration = max(0.5, sec)
        self.updateGeometry()
        self.update()

    def set_current_time(self, sec: float):
        self.current_time = max(0.0, min(self.total_duration, sec))
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging_playhead = True
            self._seek_from_mouse(event.pos().x())
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging_playhead:
            self._seek_from_mouse(event.pos().x())
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging_playhead = False
            event.accept()

    def _seek_from_mouse(self, mouse_x: float):
        track_x = mouse_x - self.header_width
        t = track_x / self.px_per_sec
        t = max(0.0, min(self.total_duration, t))
        self.current_time = t
        self.timeChanged.emit(t)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        ruler_h = self.ruler_height
        hw = self.header_width

        # 1. Backgrounds
        # Track Header background (darker)
        painter.fillRect(0, 0, hw, h, QColor("#1a1a20"))
        # Track Body background
        painter.fillRect(hw, 0, w - hw, h, QColor("#141418"))
        # Ruler background
        painter.fillRect(0, 0, w, ruler_h, QColor("#1e1e24"))

        # Separator line
        painter.setPen(QPen(QColor("#2d2d38"), 1))
        painter.drawLine(hw, 0, hw, h)
        painter.drawLine(0, ruler_h, w, ruler_h)

        # 2. Ruler ticks and timestamps
        painter.setFont(QFont("Segoe UI", 9))
        step_sec = 0.5
        total_steps = int(self.total_duration / step_sec) + 1
        for i in range(total_steps):
            t = i * step_sec
            x = hw + int(t * self.px_per_sec)
            if x > w:
                break
            # Tick mark
            is_major = (i % 2 == 0)
            tick_len = 10 if is_major else 5
            painter.setPen(QPen(QColor("#64748b" if is_major else "#3f3f4e"), 1))
            painter.drawLine(x, ruler_h - tick_len, x, ruler_h)
            if is_major:
                painter.setPen(QColor("#94a3b8"))
                painter.drawText(x + 3, ruler_h - 8, f"{t:.1f}s")

        # 3. Track Rows
        curr_y = ruler_h
        for idx, track in enumerate(self.tracks):
            # Track header label
            painter.setPen(QPen(QColor("#cbd5e1"), 1))
            painter.drawText(12, curr_y + 22, track["name"])

            # Track lane border
            painter.setPen(QPen(QColor("#24242c"), 1))
            painter.drawLine(0, curr_y + self.track_height, w, curr_y + self.track_height)

            # Sequence Clip block
            clip_start_x = hw + 10
            clip_len_sec = self.total_duration - (0.5 if idx == 0 else 0)
            clip_w = max(20, int(clip_len_sec * self.px_per_sec))

            clip_rect = QRectF(clip_start_x, curr_y + 4, clip_w, self.track_height - 8)
            painter.setBrush(QBrush(QColor(track["color"])))
            painter.setPen(QPen(QColor(track["color"]).lighter(130), 1))
            painter.drawRoundedRect(clip_rect, 4, 4)

            # Clip title
            painter.setPen(QColor("#ffffff"))
            clip_title = "Typing Animation Keyframes" if idx == 0 else ("Canvas Background" if idx == 1 else "Shapes & Paths")
            painter.drawText(clip_rect.adjusted(8, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, clip_title)

            curr_y += self.track_height

        # 4. Red Playhead Scrubber (Premiere Style)
        playhead_x = hw + (self.current_time * self.px_per_sec)
        
        # Vertical line
        painter.setPen(QPen(QColor("#f43f5e"), 1.5))
        painter.drawLine(playhead_x, 0, playhead_x, h)

        # Scrubber head inverted triangle
        head_poly = QPolygonF([
            QPointF(playhead_x - 7, 0),
            QPointF(playhead_x + 7, 0),
            QPointF(playhead_x + 7, ruler_h - 10),
            QPointF(playhead_x, ruler_h - 2),
            QPointF(playhead_x - 7, ruler_h - 10),
        ])
        painter.setBrush(QBrush(QColor("#f43f5e")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(head_poly)


class TimelinePanel(QWidget):
    playToggled = Signal(bool)
    seekChanged = Signal(float)  # 0.0 to 1.0

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.duration_sec = 3.0
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(4)

        # Control Bar (Top of timeline)
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setSpacing(8)

        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(30, 24)
        self.btn_play.setToolTip("Play / Pause (Space)")

        self.btn_stop = QPushButton("■")
        self.btn_stop.setFixedSize(30, 24)
        self.btn_stop.setToolTip("Stop & Reset")

        self.lbl_timecode = QLabel("00:00:00 / 00:00:03")
        self.lbl_timecode.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11px; color: #38bdf8; font-weight: bold;")

        ctrl_bar.addWidget(self.btn_play)
        ctrl_bar.addWidget(self.btn_stop)
        ctrl_bar.addWidget(self.lbl_timecode)
        ctrl_bar.addStretch()

        lbl_zoom = QLabel("Zoom:")
        lbl_zoom.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.slider_zoom = QSlider(Qt.Orientation.Horizontal)
        self.slider_zoom.setRange(80, 400)
        self.slider_zoom.setValue(160)
        self.slider_zoom.setFixedWidth(100)
        ctrl_bar.addWidget(lbl_zoom)
        ctrl_bar.addWidget(self.slider_zoom)

        layout.addLayout(ctrl_bar)

        # Tracks Area with Ruler
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.tracks_widget = TimelineRulerAndTracks()
        scroll.setWidget(self.tracks_widget)
        layout.addWidget(scroll)

        # Connections
        self.tracks_widget.timeChanged.connect(self._on_track_time_changed)
        self.slider_zoom.valueChanged.connect(self._on_zoom_changed)
        self.btn_play.clicked.connect(self._on_play_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)

    def set_duration(self, sec: float):
        self.duration_sec = max(0.5, sec)
        self.tracks_widget.set_duration(self.duration_sec)
        self._update_timecode(self.tracks_widget.current_time)

    def set_progress(self, progress: float):
        sec = progress * self.duration_sec
        self.tracks_widget.set_current_time(sec)
        self._update_timecode(sec)

    def set_playing(self, is_playing: bool):
        self.btn_play.setText("⏸" if is_playing else "▶")

    def _on_track_time_changed(self, sec: float):
        progress = sec / self.duration_sec
        self._update_timecode(sec)
        self.seekChanged.emit(progress)

    def _update_timecode(self, sec: float):
        m = int(sec // 60)
        s = int(sec % 60)
        f = int((sec % 1) * 30)  # 30 fps
        total_m = int(self.duration_sec // 60)
        total_s = int(self.duration_sec % 60)
        total_f = int((self.duration_sec % 1) * 30)
        self.lbl_timecode.setText(f"{m:02d}:{s:02d}:{f:02d} / {total_m:02d}:{total_s:02d}:{total_f:02d}")

    def _on_zoom_changed(self, val):
        self.tracks_widget.px_per_sec = float(val)
        self.tracks_widget.update()

    def _on_play_clicked(self):
        is_now_playing = (self.btn_play.text() == "▶")
        self.btn_play.setText("⏸" if is_now_playing else "▶")
        self.playToggled.emit(is_now_playing)

    def _on_stop_clicked(self):
        self.btn_play.setText("▶")
        self.set_progress(0.0)
        self.playToggled.emit(False)
        self.seekChanged.emit(0.0)
