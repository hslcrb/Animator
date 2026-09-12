"""
Dark Theme and Style Definitions for Animator
Figma & Premiere-inspired modern dark theme.
"""

DARK_THEME_QSS = """
* {
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 12px;
    color: #e2e8f0;
    outline: none;
}

QMainWindow, QWidget#centralWidget {
    background-color: #16161a;
}

/* ToolBar & Menus */
QToolBar {
    background-color: #1e1e24;
    border-bottom: 1px solid #2e2e38;
    padding: 4px 8px;
    spacing: 6px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 5px 8px;
    color: #cbd5e1;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #2c2c36;
    border-color: #3b3b48;
    color: #ffffff;
}

QToolButton:checked, QToolButton:pressed {
    background-color: #383848;
    border-color: #0d99ff;
    color: #0d99ff;
}

QMenuBar {
    background-color: #1e1e24;
    border-bottom: 1px solid #2a2a34;
    color: #cbd5e1;
    padding: 2px 6px;
}

QMenuBar::item {
    background: transparent;
    padding: 4px 10px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #2d2d38;
    color: #ffffff;
}

QMenu {
    background-color: #22222a;
    border: 1px solid #363644;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #0d99ff;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #32323e;
    margin: 4px 8px;
}

/* Dock Widgets & Panels */
QDockWidget {
    titlebar-close-icon: url(none);
    titlebar-normal-icon: url(none);
    border: none;
}

QDockWidget::title {
    text-align: left;
    background-color: #1e1e24;
    padding: 6px 12px;
    border-bottom: 1px solid #2d2d38;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.5px;
    color: #94a3b8;
    text-transform: uppercase;
}

/* Scroll Area & Lists */
QScrollArea, QFrame#panelFrame {
    background-color: #1a1a20;
    border: none;
}

QScrollBar:vertical {
    border: none;
    background: #18181f;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #333342;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #4a4a5e;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #18181f;
    height: 8px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #333342;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #4a4a5e;
}

/* Tab Widgets (Vertical & Horizontal) */
QTabWidget::pane {
    border: 1px solid #2a2a34;
    background-color: #1a1a20;
}

QTabBar::tab {
    background-color: #1e1e24;
    color: #94a3b8;
    padding: 8px 14px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #1a1a20;
    color: #ffffff;
    border-bottom: 2px solid #0d99ff;
}

QTabBar::tab:hover:!selected {
    background-color: #262630;
    color: #cbd5e1;
}

/* Tree & List Views (Layers, Assets) */
QTreeWidget, QListWidget {
    background-color: #1a1a20;
    border: none;
    color: #e2e8f0;
    padding: 4px;
    show-decoration-selected: 1;
}

QTreeWidget::item, QListWidget::item {
    height: 28px;
    border-radius: 4px;
    padding: 2px 6px;
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #2b3a55;
    color: #ffffff;
}

QTreeWidget::item:hover:!selected, QListWidget::item:hover:!selected {
    background-color: #252530;
}

/* Input Fields, Buttons, Combos */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #24242e;
    border: 1px solid #363644;
    border-radius: 5px;
    padding: 5px 8px;
    color: #f1f5f9;
    selection-background-color: #0d99ff;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #0d99ff;
    background-color: #282834;
}

QPushButton {
    background-color: #2b2b36;
    border: 1px solid #3a3a48;
    border-radius: 5px;
    padding: 6px 12px;
    color: #f1f5f9;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #383848;
    border-color: #4a4a5c;
}

QPushButton:pressed {
    background-color: #202028;
}

QPushButton#primaryBtn {
    background-color: #0d99ff;
    border: 1px solid #0d82d8;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#primaryBtn:hover {
    background-color: #28a7ff;
}

QPushButton#accentBtn {
    background-color: #7c3aed;
    border: 1px solid #6d28d9;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#accentBtn:hover {
    background-color: #8b5cf6;
}

QComboBox {
    background-color: #24242e;
    border: 1px solid #363644;
    border-radius: 5px;
    padding: 4px 10px;
    color: #f1f5f9;
}

QComboBox:hover {
    border-color: #4a4a5c;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #22222c;
    border: 1px solid #363644;
    selection-background-color: #0d99ff;
    color: #e2e8f0;
    padding: 4px;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 4px;
    background: #333342;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #0d99ff;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #0d99ff;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #e0f2fe;
}

/* Group Box */
QGroupBox {
    border: 1px solid #2d2d38;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 600;
    font-size: 11px;
    color: #94a3b8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

/* Status Bar */
QStatusBar {
    background-color: #16161b;
    border-top: 1px solid #262630;
    color: #71717a;
    font-size: 11px;
}
"""
