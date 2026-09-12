"""
Font and Typography Utilities for Animator.
Handles font fallback chains (Korean/English glyphs), system font scanning,
and unicode script detection.
"""

import re
from PySide6.QtGui import QFont, QFontDatabase


# Standard fallback font list prioritising modern Korean system fonts
KOREAN_FALLBACK_FONTS = [
    "Malgun Gothic",      # Windows standard
    "맑은 고딕",
    "Pretendard",         # Popular modern Korean font
    "Noto Sans KR",       # Google Noto
    "Apple SD Gothic Neo",# macOS
    "NanumGothic",        # Naver Nanum
    "Batang",
    "Gulim",
    "Segoe UI",
]

_korean_regex = re.compile(r"[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]")


def contains_korean(text: str) -> bool:
    """Returns True if the text contains any Korean Hangul characters."""
    return bool(_korean_regex.search(text))


def font_supports_korean(family: str) -> bool:
    """Check if a font family natively provides Korean glyphs."""
    try:
        writing_systems = QFontDatabase.writingSystems(family)
        return QFontDatabase.WritingSystem.Korean in writing_systems
    except Exception:
        return False


def get_smart_font(family: str, size: float, bold=False, italic=False, text: str = "") -> QFont:
    """
    Constructs a QFont with intelligent Korean fallback.
    If the text contains Korean characters and the selected font is an English-only font,
    it automatically configures the font fallback chain so Korean glyphs render beautifully.
    """
    font = QFont(family)
    safe_size = max(1.0, float(size))
    font.setPointSizeF(safe_size)
    font.setBold(bold)
    font.setItalic(italic)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)

    # If text contains Korean
    if text and contains_korean(text):
        if not font_supports_korean(family):
            # Selected font is English-only: prepend family and fallback to Korean system fonts
            font.setFamilies([family] + KOREAN_FALLBACK_FONTS)
        else:
            font.setFamilies([family] + KOREAN_FALLBACK_FONTS)
    else:
        font.setFamilies([family] + KOREAN_FALLBACK_FONTS)

    return font
