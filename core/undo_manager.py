"""
Undo / Redo Manager for Animator
Supports undoing and redoing element additions, deletions, geometry transforms,
and property modifications with Ctrl+Z and Ctrl+Shift+Z.
"""

from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtGui import QColor


class Command:
    def undo(self):
        raise NotImplementedError

    def redo(self):
        raise NotImplementedError


class AddItemCommand(Command):
    def __init__(self, scene, item):
        self.scene = scene
        self.item = item

    def undo(self):
        self.scene.removeItem(self.item)
        self.scene.itemRemoved.emit(self.item)
        self.scene.update()

    def redo(self):
        self.scene.addItem(self.item)
        self.scene.itemAdded.emit(self.item)
        self.scene.clearSelection()
        self.item.setSelected(True)
        self.scene.update()


class RemoveItemCommand(Command):
    def __init__(self, scene, items):
        self.scene = scene
        self.items = list(items)

    def undo(self):
        for it in self.items:
            self.scene.addItem(it)
            self.scene.itemAdded.emit(it)
        self.scene.clearSelection()
        for it in self.items:
            it.setSelected(True)
        self.scene.update()

    def redo(self):
        for it in self.items:
            self.scene.removeItem(it)
            self.scene.itemRemoved.emit(it)
        self.scene.clearSelection()
        self.scene.update()


class TransformCommand(Command):
    def __init__(self, item, old_x, old_y, old_w, old_h, old_rot, new_x, new_y, new_w, new_h, new_rot):
        self.item = item
        self.old_geom = (old_x, old_y, old_w, old_h, old_rot)
        self.new_geom = (new_x, new_y, new_w, new_h, new_rot)

    def undo(self):
        x, y, w, h, rot = self.old_geom
        self.item.setPos(x, y)
        self.item.prepareGeometryChange()
        self.item.w = w
        self.item.h = h
        self.item.setRotation(rot)
        self.item.update()
        if self.item.scene():
            self.item.scene().itemModified.emit(self.item)

    def redo(self):
        x, y, w, h, rot = self.new_geom
        self.item.setPos(x, y)
        self.item.prepareGeometryChange()
        self.item.w = w
        self.item.h = h
        self.item.setRotation(rot)
        self.item.update()
        if self.item.scene():
            self.item.scene().itemModified.emit(self.item)


class PropertyChangeCommand(Command):
    def __init__(self, item, prop_name, old_val, new_val):
        self.item = item
        self.prop_name = prop_name
        self.old_val = old_val
        self.new_val = new_val

    def undo(self):
        self._apply_val(self.old_val)

    def redo(self):
        self._apply_val(self.new_val)

    def _apply_val(self, val):
        if hasattr(self.item, self.prop_name):
            setattr(self.item, self.prop_name, val)
            if hasattr(self.item, "adjust_size_to_text"):
                self.item.adjust_size_to_text()
            self.item.update()
            if self.item.scene():
                self.item.scene().itemModified.emit(self.item)


class ReplaceItemCommand(Command):
    """Used for operations like Create Outlines (replaces TextItem with PathItem)."""
    def __init__(self, scene, old_item, new_item):
        self.scene = scene
        self.old_item = old_item
        self.new_item = new_item

    def undo(self):
        self.scene.removeItem(self.new_item)
        self.scene.itemRemoved.emit(self.new_item)
        self.scene.addItem(self.old_item)
        self.scene.itemAdded.emit(self.old_item)
        self.scene.clearSelection()
        self.old_item.setSelected(True)
        self.scene.update()

    def redo(self):
        self.scene.removeItem(self.old_item)
        self.scene.itemRemoved.emit(self.old_item)
        self.scene.addItem(self.new_item)
        self.scene.itemAdded.emit(self.new_item)
        self.scene.clearSelection()
        self.new_item.setSelected(True)
        self.scene.update()


class UndoManager(QObject):
    canUndoChanged = Signal(bool)
    canRedoChanged = Signal(bool)

    def __init__(self):
        super().__init__()
        self._undo_stack = []
        self._redo_stack = []

    def push(self, command: Command):
        self._undo_stack.append(command)
        self._redo_stack.clear()
        self._notify()

    def undo(self):
        if not self._undo_stack:
            return
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        self._notify()

    def redo(self):
        if not self._redo_stack:
            return
        cmd = self._redo_stack.pop()
        cmd.redo()
        self._undo_stack.append(cmd)
        self._notify()

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def _notify(self):
        self.canUndoChanged.emit(self.can_undo())
        self.canRedoChanged.emit(self.can_redo())
