"""
Automated unit verification for Animator core features.
Tests:
1. Scene & Item creation
2. Alt+Drag duplication
3. Create Outlines (Text -> PathItem vectorization)
4. Static & Animated SVG export
5. Looping GIF export
"""

import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

# Headless Qt App
app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas.canvas_scene import CanvasScene
from ui.canvas.items import RectangleItem, TextItem, ArtboardItem
from core.svg_exporter import export_static_svg, export_animated_svg
from core.gif_exporter import export_looping_gif


def run_tests():
    print("--- Starting Animator Verification ---")
    scene = CanvasScene()
    scene.set_default_artboard(800, 500)

    # 1. Add background shape & text
    bg = RectangleItem(-300, -100, 600, 200, "Card")
    scene.addItem(bg)

    text_item = TextItem(-200, -20, "Test Vector Typing", "Text 1")
    scene.addItem(text_item)
    print("[OK] Items added to scene")

    # 2. Test Alt+Drag duplicate
    dup_item = scene.duplicate_item(text_item, offset=QPointF(30, 30))
    assert dup_item is not None, "Duplicate failed"
    assert dup_item.text == "Test Vector Typing", "Duplicate text mismatch"
    print("[OK] Alt+Drag / Item Duplication verified")

    # 3. Test Create Outlines (Text -> PathItem)
    path_item = scene.create_outline_for_item(dup_item)
    assert path_item is not None, "Create Outlines failed"
    assert path_item.name == "Text 1 Copy Outline", "Outline name mismatch"
    print(f"[OK] Create Outlines verified! Converted text to PathItem with bounds {path_item.w}x{path_item.h}")

    # 4. Test SVG export
    os.makedirs("output_test", exist_ok=True)
    svg_static_path = "output_test/test_static.svg"
    ok, msg = export_static_svg(scene, svg_static_path)
    assert ok, f"Static SVG export failed: {msg}"
    assert os.path.exists(svg_static_path) and os.path.getsize(svg_static_path) > 0
    print(f"[OK] Clean Static SVG exported ({os.path.getsize(svg_static_path)} bytes)")

    svg_anim_path = "output_test/test_animated.svg"
    ok, msg = export_animated_svg(scene, svg_anim_path, duration=2.0, delay=1.0)
    assert ok, f"Animated SVG export failed: {msg}"
    assert os.path.exists(svg_anim_path) and os.path.getsize(svg_anim_path) > 0
    print(f"[OK] Looping Animated SVG exported ({os.path.getsize(svg_anim_path)} bytes)")

    # 5. Test Looping GIF export
    gif_path = "output_test/test_animation.gif"
    ok, msg = export_looping_gif(scene, gif_path, duration=1.0, delay=0.5, fps=12)
    assert ok, f"GIF export failed: {msg}"
    assert os.path.exists(gif_path) and os.path.getsize(gif_path) > 0
    print(f"[OK] Looping GIF exported ({os.path.getsize(gif_path)} bytes)")

    # 6. Test Undo / Redo
    init_count = len(scene.items())
    temp_box = RectangleItem(10, 10, 50, 50, "TempBox")
    scene.addItem(temp_box)
    from core.undo_manager import AddItemCommand
    scene.undo_manager.push(AddItemCommand(scene, temp_box))
    assert len(scene.items()) == init_count + 1, "Item add failed"
    scene.undo_manager.undo()
    assert len(scene.items()) == init_count, "Undo add item failed"
    scene.undo_manager.redo()
    assert len(scene.items()) == init_count + 1, "Redo add item failed"
    scene.undo_manager.undo()
    print("[OK] Undo (Ctrl+Z) and Redo (Ctrl+Shift+Z) system verified")

    print("\n--- ALL TESTS PASSED SUCCESSFULLY! ---")


if __name__ == "__main__":
    run_tests()
