"""
Font Picker Dialog / Modal for Animator
A rich Figma/Adobe-style typography browser with live canvas preview,
Korean/English glyph support filtering, and custom text preview playground.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QCheckBox, QSlider, QTextEdit,
    QFrame, QStyledItemDelegate, QStyle
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QFontDatabase, QColor, QPainter

from core.font_utils import font_supports_korean, get_smart_font


class FontListItemDelegate(QStyledItemDelegate):
    """Renders font item with its own font family and Korean badge."""
    def paint(self, painter: QPainter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        family = index.data(Qt.ItemDataRole.DisplayRole)
        has_korean = index.data(Qt.ItemDataRole.UserRole)  # bool

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if is_selected:
            painter.fillRect(option.rect, QColor("#0d99ff"))
            text_color = QColor("#ffffff")
        else:
            bg_color = QColor("#22222a") if (index.row() % 2 == 0) else QColor("#1c1c23")
            painter.fillRect(option.rect, bg_color)
            text_color = QColor("#f1f5f9")

        # Font family label with its own font
        item_font = QFont(family)
        item_font.setPointSize(12)
        painter.setFont(item_font)
        painter.setPen(text_color)

        rect = option.rect.adjusted(12, 0, -12, 0)
        painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, family)

        # Korean badge
        badge_rect = option.rect.adjusted(option.rect.width() - 65, 6, -10, -6)
        if has_korean:
            painter.setBrush(QColor("#059669") if is_selected else QColor("#065f46"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge_rect, 4, 4)
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.setPen(QColor("#34d399"))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "한글 지원")
        else:
            painter.setBrush(QColor("#334155") if is_selected else QColor("#1e293b"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge_rect, 4, 4)
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "영문 전용")

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(220, 36)


class FontPickerDialog(QDialog):
    fontSelected = Signal(str)  # Real-time preview signal

    def __init__(self, initial_family="Segoe UI", target_item=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Typography Browser & Font Picker")
        self.resize(850, 580)
        self.setMinimumSize(700, 450)

        self.initial_family = initial_family
        self.current_family = initial_family
        self.target_item = target_item
        self.all_families = []

        self._init_ui()
        self._load_system_fonts()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # 1. Search & Filter Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Search fonts by name...")
        self.txt_search.setClearButtonEnabled(True)
        top_bar.addWidget(self.txt_search, 1)

        self.chk_korean_only = QCheckBox("한글 지원 폰트만 보기 (Korean Only)")
        top_bar.addWidget(self.chk_korean_only)

        self.lbl_count = QLabel("0 fonts")
        self.lbl_count.setStyleSheet("color: #94a3b8; font-size: 11px;")
        top_bar.addWidget(self.lbl_count)

        main_layout.addLayout(top_bar)

        # 2. Main Splitter (Left: Font List, Right: Large Preview Playground)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Font List
        left_widget = QFrame()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.font_list = QListWidget()
        self.font_list.setItemDelegate(FontListItemDelegate(self.font_list))
        left_layout.addWidget(self.font_list)
        splitter.addWidget(left_widget)

        # Right: Rich Typography Playground
        right_widget = QFrame()
        right_widget.setStyleSheet("background-color: #18181f; border-radius: 8px; padding: 10px;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)

        # Selected Font Name & Badges
        font_header = QHBoxLayout()
        self.lbl_font_name = QLabel(self.current_family)
        self.lbl_font_name.setStyleSheet("font-size: 18px; font-weight: 800; color: #38bdf8;")
        self.lbl_badge = QLabel("한글 지원")
        self.lbl_badge.setStyleSheet("background: #065f46; color: #34d399; font-size: 11px; padding: 3px 8px; border-radius: 4px;")
        font_header.addWidget(self.lbl_font_name)
        font_header.addWidget(self.lbl_badge)
        font_header.addStretch()
        right_layout.addLayout(font_header)

        # Preview Size Slider
        h_size = QHBoxLayout()
        h_size.addWidget(QLabel("Preview Size:"))
        self.slider_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_size.setRange(12, 72)
        self.slider_size.setValue(24)
        self.lbl_size_val = QLabel("24 pt")
        h_size.addWidget(self.slider_size)
        h_size.addWidget(self.lbl_size_val)
        right_layout.addLayout(h_size)

        # Custom Editable Playground
        right_layout.addWidget(QLabel("Interactive Playground (Type to test):"))
        self.txt_preview = QTextEdit()
        self.txt_preview.setText(
            "다람쥐 헌 쳇바퀴에 타고파 (The quick brown fox jumps over the lazy dog)\n"
            "0123456789 !@#$%^&*()_+\n"
            "동해물과 백두산이 마르고 닳도록 Vector Animation with Animator"
        )
        self.txt_preview.setStyleSheet("background-color: #141418; border: 1px solid #2d2d38; border-radius: 6px; padding: 10px; color: #f1f5f9;")
        right_layout.addWidget(self.txt_preview)

        splitter.addWidget(right_widget)
        splitter.setSizes([320, 530])
        main_layout.addWidget(splitter, 1)

        # 3. Action Buttons
        btn_bar = QHBoxLayout()
        lbl_hint = QLabel("💡 폰트를 클릭하면 캔버스의 텍스트가 실시간으로 미리보기됩니다.")
        lbl_hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
        btn_bar.addWidget(lbl_hint)
        btn_bar.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_apply = QPushButton("Select Font (적용)")
        self.btn_apply.setObjectName("primaryBtn")
        btn_bar.addWidget(self.btn_cancel)
        btn_bar.addWidget(self.btn_apply)
        main_layout.addLayout(btn_bar)

        # Signals
        self.txt_search.textChanged.connect(self._filter_fonts)
        self.chk_korean_only.toggled.connect(self._filter_fonts)
        self.font_list.currentItemChanged.connect(self._on_font_item_changed)
        self.slider_size.valueChanged.connect(self._update_preview_size)
        self.btn_apply.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def _load_system_fonts(self):
        raw_families = QFontDatabase.families()
        # Sort and deduplicate
        seen = set()
        clean = []
        for f in raw_families:
            if f and not f.startswith("@") and f not in seen:
                seen.add(f)
                clean.append(f)
        clean.sort()
        self.all_families = clean
        self._filter_fonts()

        # Select initial font
        for i in range(self.font_list.count()):
            item = self.font_list.item(i)
            if item.text() == self.initial_family:
                self.font_list.setCurrentItem(item)
                self.font_list.scrollToItem(item)
                break

    def _filter_fonts(self):
        query = self.txt_search.text().strip().lower()
        korean_only = self.chk_korean_only.isChecked()

        self.font_list.clear()
        matching_count = 0

        for family in self.all_families:
            has_korean = font_supports_korean(family)

            if korean_only and not has_korean:
                continue
            if query and query not in family.lower():
                continue

            item = QListWidgetItem(family)
            item.setData(Qt.ItemDataRole.UserRole, has_korean)
            self.font_list.addItem(item)
            matching_count += 1

        self.lbl_count.setText(f"{matching_count} fonts")

    def _on_font_item_changed(self, current, previous):
        if not current:
            return

        family = current.text()
        has_korean = current.data(Qt.ItemDataRole.UserRole)
        self.current_family = family

        # Update right preview panel
        self.lbl_font_name.setText(family)
        if has_korean:
            self.lbl_badge.setText("한글 지원")
            self.lbl_badge.setStyleSheet("background: #065f46; color: #34d399; font-size: 11px; padding: 3px 8px; border-radius: 4px;")
        else:
            self.lbl_badge.setText("영문 전용 (한글은 시스템 기본폰트로 대체)")
            self.lbl_badge.setStyleSheet("background: #334155; color: #94a3b8; font-size: 11px; padding: 3px 8px; border-radius: 4px;")

        self._update_preview_size(self.slider_size.value())

        # Live Preview on target Canvas Item
        if self.target_item and hasattr(self.target_item, "font_family"):
            self.target_item.font_family = family
            if hasattr(self.target_item, "adjust_size_to_text"):
                self.target_item.adjust_size_to_text()
            self.target_item.update()
            if self.target_item.scene():
                self.target_item.scene().update()
                self.target_item.scene().itemModified.emit(self.target_item)

        self.fontSelected.emit(family)

    def _update_preview_size(self, size_val):
        self.lbl_size_val.setText(f"{size_val} pt")
        sample_font = get_smart_font(self.current_family, size_val, text=self.txt_preview.toPlainText())
        self.txt_preview.setFont(sample_font)

    def reject(self):
        """Restore initial font when user cancels."""
        if self.target_item and hasattr(self.target_item, "font_family"):
            self.target_item.font_family = self.initial_family
            if hasattr(self.target_item, "adjust_size_to_text"):
                self.target_item.adjust_size_to_text()
            self.target_item.update()
            if self.target_item.scene():
                self.target_item.scene().update()
                self.target_item.scene().itemModified.emit(self.target_item)
        super().reject()
