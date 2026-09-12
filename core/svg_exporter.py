"""
Clean and Animated SVG Exporter for Animator.
Supports static vector shapes and standalone looping typewriter animated SVGs.
"""

from PySide6.QtGui import QFontMetricsF
from PySide6.QtCore import QRectF
from ui.canvas.items import ArtboardItem, RectangleItem, EllipseItem, TextItem, PathItem
from core.font_outline import painter_path_to_svg_d
import html


def get_bounding_rect_or_artboard(scene):
    """Find artboard bounds or calculate aggregate bounding box of all items."""
    artboard = None
    for item in scene.items():
        if isinstance(item, ArtboardItem):
            artboard = item
            break

    if artboard:
        return QRectF(artboard.x(), artboard.y(), artboard.w, artboard.h), artboard

    # Fallback to scene bounding rect
    items = [it for it in scene.items() if hasattr(it, "w")]
    if not items:
        return QRectF(0, 0, 800, 600), None

    min_x = min(it.x() for it in items)
    min_y = min(it.y() for it in items)
    max_x = max(it.x() + it.w for it in items)
    max_y = max(it.y() + it.h for it in items)
    return QRectF(min_x - 20, min_y - 20, (max_x - min_x) + 40, (max_y - min_y) + 40), None


def export_static_svg(scene, filepath: str) -> tuple[bool, str]:
    """Export scene elements as clean, standards-compliant static SVG."""
    try:
        bounds, artboard = get_bounding_rect_or_artboard(scene)
        vx, vy, vw, vh = bounds.x(), bounds.y(), bounds.width(), bounds.height()

        svg_lines = [
            f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.1f} {vy:.1f} {vw:.1f} {vh:.1f}" width="{vw:.1f}" height="{vh:.1f}">'
        ]

        # Artboard Background
        if artboard:
            svg_lines.append(
                f'  <!-- Artboard Background -->'
                f'\n  <rect x="{artboard.x():.1f}" y="{artboard.y():.1f}" width="{artboard.w:.1f}" height="{artboard.h:.1f}" '
                f'fill="{artboard.fill_color.name()}" stroke="{artboard.stroke_color.name()}" stroke-width="{artboard.stroke_width:.1f}" />'
            )

        # Sort items back-to-front (Z-value ascending)
        items = [it for it in scene.items() if not isinstance(it, ArtboardItem) and hasattr(it, "w")]
        items.sort(key=lambda it: it.zValue())

        for it in items:
            if not it.isVisible():
                continue

            op = f' opacity="{it.opacity_val:.2f}"' if it.opacity_val < 1.0 else ''
            rot = it.rotation()
            trans = f' transform="rotate({rot:.1f} {it.x() + it.w/2:.1f} {it.y() + it.h/2:.1f})"' if rot != 0 else ''

            if isinstance(it, RectangleItem):
                rx = f' rx="{it.border_radius:.1f}" ry="{it.border_radius:.1f}"' if it.border_radius > 0 else ''
                svg_lines.append(
                    f'  <rect x="{it.x():.1f}" y="{it.y():.1f}" width="{it.w:.1f}" height="{it.h:.1f}"{rx} '
                    f'fill="{it.fill_color.name()}" stroke="{it.stroke_color.name()}" stroke-width="{it.stroke_width:.1f}"{op}{trans} />'
                )
            elif isinstance(it, EllipseItem):
                cx = it.x() + it.w / 2
                cy = it.y() + it.h / 2
                rx = it.w / 2
                ry = it.h / 2
                svg_lines.append(
                    f'  <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
                    f'fill="{it.fill_color.name()}" stroke="{it.stroke_color.name()}" stroke-width="{it.stroke_width:.1f}"{op}{trans} />'
                )
            elif isinstance(it, PathItem):
                d_str = painter_path_to_svg_d(it.path, offset_x=it.x(), offset_y=it.y())
                svg_lines.append(
                    f'  <path d="{d_str}" fill="{it.fill_color.name()}" stroke="{it.stroke_color.name()}" stroke-width="{it.stroke_width:.1f}"{op}{trans} />'
                )
            elif isinstance(it, TextItem):
                fm = QFontMetricsF(it.get_font())
                ty = it.y() + fm.ascent() + 5
                escaped_txt = html.escape(it.text)
                fw = ' font-weight="bold"' if it.font_bold else ''
                fs = ' font-style="italic"' if it.font_italic else ''
                svg_lines.append(
                    f'  <text x="{it.x() + 5:.1f}" y="{ty:.1f}" font-family="{it.font_family}" font-size="{it.font_size:.1f}"{fw}{fs} '
                    f'fill="{it.fill_color.name()}"{op}{trans}>{escaped_txt}</text>'
                )

        svg_lines.append('</svg>')

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(svg_lines))

        return True, "Export successful"
    except Exception as e:
        return False, str(e)


def export_animated_svg(scene, filepath: str, duration=3.0, delay=1.0, cursor_char="|") -> tuple[bool, str]:
    """
    Export standalone looping typewriter animated SVG.
    Uses CSS animation & keyframes so it plays natively in any browser/viewer without external scripts.
    """
    try:
        bounds, artboard = get_bounding_rect_or_artboard(scene)
        vx, vy, vw, vh = bounds.x(), bounds.y(), bounds.width(), bounds.height()

        # Find typing text item
        typing_items = [it for it in scene.items() if isinstance(it, TextItem) and it.enable_typing_anim]
        target_text_item = typing_items[0] if typing_items else None
        
        full_text = target_text_item.text if target_text_item else "Typing Animation"
        char_count = len(full_text)
        total_time = duration + delay

        # Style sheet with CSS typewriter effect
        svg_lines = [
            f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.1f} {vy:.1f} {vw:.1f} {vh:.1f}" width="{vw:.1f}" height="{vh:.1f}">',
            '  <defs>',
            '    <style>',
            '      @keyframes typing {',
            f'        0% {{ width: 0ch; }}',
            f'        {int((duration / total_time) * 80)}% {{ width: {char_count}ch; }}',
            f'        {int((duration / total_time) * 100)}% {{ width: {char_count}ch; }}',
            f'        100% {{ width: {char_count}ch; }}',
            '      }',
            '      @keyframes blink {',
            '        50% { border-color: transparent; }',
            '      }',
            '      .typewriter {',
            f'        font-family: {target_text_item.font_family if target_text_item else "Consolas, monospace"};',
            f'        font-size: {target_text_item.font_size if target_text_item else 28}px;',
            f'        color: {target_text_item.fill_color.name() if target_text_item else "#38bdf8"};',
            f'        font-weight: {"bold" if (target_text_item and target_text_item.font_bold) else "normal"};',
            '        overflow: hidden;',
            '        white-space: nowrap;',
            f'        border-right: 3px solid {target_text_item.fill_color.name() if target_text_item else "#38bdf8"};',
            f'        width: 0ch;',
            f'        animation: typing {total_time:.2f}s steps({char_count}, end) infinite, blink 0.75s step-end infinite;',
            '        display: inline-block;',
            '      }',
            '    </style>',
            '  </defs>'
        ]

        # 1. Artboard Background
        if artboard:
            svg_lines.append(
                f'  <rect x="{artboard.x():.1f}" y="{artboard.y():.1f}" width="{artboard.w:.1f}" height="{artboard.h:.1f}" '
                f'fill="{artboard.fill_color.name()}" stroke="{artboard.stroke_color.name()}" stroke-width="{artboard.stroke_width:.1f}" />'
            )

        # 2. Static Background Items
        items = [it for it in scene.items() if not isinstance(it, ArtboardItem) and hasattr(it, "w")]
        items.sort(key=lambda it: it.zValue())

        for it in items:
            if not it.isVisible():
                continue

            if it == target_text_item:
                continue  # Handled separately with animation

            op = f' opacity="{it.opacity_val:.2f}"' if it.opacity_val < 1.0 else ''
            rot = it.rotation()
            trans = f' transform="rotate({rot:.1f} {it.x() + it.w/2:.1f} {it.y() + it.h/2:.1f})"' if rot != 0 else ''

            if isinstance(it, RectangleItem):
                rx = f' rx="{it.border_radius:.1f}" ry="{it.border_radius:.1f}"' if it.border_radius > 0 else ''
                svg_lines.append(
                    f'  <rect x="{it.x():.1f}" y="{it.y():.1f}" width="{it.w:.1f}" height="{it.h:.1f}"{rx} '
                    f'fill="{it.fill_color.name()}" stroke="{it.stroke_color.name()}" stroke-width="{it.stroke_width:.1f}"{op}{trans} />'
                )
            elif isinstance(it, EllipseItem):
                cx = it.x() + it.w / 2
                cy = it.y() + it.h / 2
                svg_lines.append(
                    f'  <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{it.w/2:.1f}" ry="{it.h/2:.1f}" '
                    f'fill="{it.fill_color.name()}" stroke="{it.stroke_color.name()}" stroke-width="{it.stroke_width:.1f}"{op}{trans} />'
                )
            elif isinstance(it, PathItem):
                d_str = painter_path_to_svg_d(it.path, offset_x=it.x(), offset_y=it.y())
                svg_lines.append(
                    f'  <path d="{d_str}" fill="{it.fill_color.name()}" stroke="{it.stroke_color.name()}" stroke-width="{it.stroke_width:.1f}"{op}{trans} />'
                )

        # 3. Animated Typewriter Item using foreignObject
        if target_text_item:
            tx = target_text_item.x()
            ty = target_text_item.y()
            tw = max(100.0, target_text_item.w + 60)
            th = max(40.0, target_text_item.h + 20)
            escaped_txt = html.escape(full_text)

            svg_lines.append(
                f'  <foreignObject x="{tx:.1f}" y="{ty:.1f}" width="{tw:.1f}" height="{th:.1f}">'
                f'\n    <div xmlns="http://www.w3.org/1999/xhtml">'
                f'\n      <div class="typewriter">{escaped_txt}</div>'
                f'\n    </div>'
                f'\n  </foreignObject>'
            )

        svg_lines.append('</svg>')

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(svg_lines))

        return True, "Animated SVG export successful"
    except Exception as e:
        return False, str(e)
