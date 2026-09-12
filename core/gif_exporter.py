"""
Looping GIF Exporter for Animator
Renders canvas animation sequence frame-by-frame and compiles into an optimized GIF using Pillow.
"""

from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import QRectF, Qt
from PIL import Image
from ui.canvas.items import ArtboardItem, TextItem


def export_looping_gif(scene, filepath: str, duration=3.0, delay=1.0, fps=24, panel=None) -> tuple[bool, str]:
    """
    Renders canvas typing animation into a smooth looping GIF.
    """
    try:
        # 1. Determine export bounds
        artboard = None
        for it in scene.items():
            if isinstance(it, ArtboardItem):
                artboard = it
                break

        if artboard:
            rect = QRectF(artboard.x(), artboard.y(), artboard.w, artboard.h)
        else:
            items = [it for it in scene.items() if hasattr(it, "w")]
            if not items:
                return False, "No items to render"
            min_x = min(it.x() for it in items)
            min_y = min(it.y() for it in items)
            max_x = max(it.x() + it.w for it in items)
            max_y = max(it.y() + it.h for it in items)
            rect = QRectF(min_x - 10, min_y - 10, (max_x - min_x) + 20, (max_y - min_y) + 20)

        w = int(rect.width())
        h = int(rect.height())
        if w <= 0 or h <= 0:
            return False, "Invalid canvas dimensions"

        # Cap max resolution for GIF performance and file size
        max_dim = 960
        scale = 1.0
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            w = int(w * scale)
            h = int(h * scale)

        total_time = duration + delay
        total_frames = max(1, int(total_time * fps))
        typing_frames = max(1, int(duration * fps))
        frame_delay_ms = int(1000 / fps)

        # Cache original typing states
        original_states = {}
        for it in scene.items():
            if isinstance(it, TextItem):
                original_states[it] = (it.typing_progress, it.isSelected())
                it.setSelected(False)  # Don't render selection handles in GIF

        # Hide any artboard selection frame during render
        if artboard:
            artboard.setSelected(False)

        pil_frames = []

        for frame_idx in range(total_frames):
            t_sec = frame_idx / fps
            if t_sec <= duration:
                progress = t_sec / duration
            else:
                progress = 1.0

            # Update text items
            for it in scene.items():
                if isinstance(it, TextItem) and it.enable_typing_anim:
                    it.typing_progress = progress
                    it.update()

            # Render scene rect into QImage
            qimg = QImage(w, h, QImage.Format.Format_RGBA8888)
            qimg.fill(QColor("#16161a"))

            painter = QPainter(qimg)
            painter.setRenderHints(
                QPainter.RenderHint.Antialiasing |
                QPainter.RenderHint.SmoothPixmapTransform |
                QPainter.RenderHint.TextAntialiasing
            )
            painter.scale(scale, scale)
            painter.translate(-rect.x(), -rect.y())

            scene.render(painter, target=QRectF(rect.x(), rect.y(), rect.width(), rect.height()), source=rect)
            painter.end()

            # Convert QImage to PIL Image
            ptr = qimg.bits()
            pil_img = Image.frombytes("RGBA", (w, h), bytes(ptr))
            # Convert to RGB with white/dark background for clean GIF palette
            rgb_img = Image.new("RGB", pil_img.size, (22, 22, 26))
            rgb_img.paste(pil_img, mask=pil_img.split()[3])
            pil_frames.append(rgb_img)

        # Restore original item states
        for it, (prog, sel) in original_states.items():
            it.typing_progress = prog
            it.setSelected(sel)
            it.update()

        if artboard:
            artboard.setSelected(False)

        # Save GIF
        if pil_frames:
            pil_frames[0].save(
                filepath,
                save_all=True,
                append_images=pil_frames[1:],
                duration=frame_delay_ms,
                loop=0,
                optimize=True
            )

        return True, f"Rendered {len(pil_frames)} frames to GIF."
    except Exception as e:
        return False, str(e)
