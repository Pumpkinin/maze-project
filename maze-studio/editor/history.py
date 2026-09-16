"""Undo/redo — командный паттерн."""


class Command:
    def execute(self): pass
    def undo(self): pass
    def redo(self): self.execute()


class UndoStack:
    def __init__(self, limit=200):
        self._undo = []
        self._redo = []
        self._limit = limit

    def push(self, cmd):
        cmd.execute()
        self._undo.append(cmd)
        self._redo.clear()
        if len(self._undo) > self._limit:
            self._undo.pop(0)

    def undo(self):
        if not self._undo:
            return
        c = self._undo.pop()
        c.undo()
        self._redo.append(c)

    def redo(self):
        if not self._redo:
            return
        c = self._redo.pop()
        c.redo()
        self._undo.append(c)

    def clear(self):
        self._undo.clear()
        self._redo.clear()


# ─── конкретные команды ────────────────────────────────────────
class PaintWallV(Command):
    def __init__(self, scene, x, y):
        self.scene, self.x, self.y = scene, x, y
        self.prev = scene.grid.v_walls[y][x] if 0 <= y < scene.h else None

    def execute(self):
        if self.prev is not None and 0 <= self.y < self.scene.h:
            self.scene.grid.v_walls[self.y][self.x] = True

    def undo(self):
        if self.prev is not None and 0 <= self.y < self.scene.h:
            self.scene.grid.v_walls[self.y][self.x] = self.prev


class PaintWallH(Command):
    def __init__(self, scene, x, y):
        self.scene, self.x, self.y = scene, x, y
        self.prev = scene.grid.h_walls[y][x] if 0 <= x < scene.w else None

    def execute(self):
        if self.prev is not None and 0 <= self.x < self.scene.w:
            self.scene.grid.h_walls[self.y][self.x] = True

    def undo(self):
        if self.prev is not None and 0 <= self.x < self.scene.w:
            self.scene.grid.h_walls[self.y][self.x] = self.prev


class EraseAt(Command):
    def __init__(self, scene, cx, cy):
        self.scene, self.cx, self.cy = scene, cx, cy
        self._saved_v = None
        self._saved_h = None

    def execute(self):
        s = self.scene
        if not (0 <= self.cx < s.w and 0 <= self.cy < s.h):
            return
        self._saved_v = [row[:] for row in s.grid.v_walls]
        self._saved_h = [row[:] for row in s.grid.h_walls]
        for x in range(s.w + 1):
            s.grid.v_walls[self.cy][x] = False
        for y in range(s.h + 1):
            s.grid.h_walls[y][self.cx] = False
        for y in range(s.h):
            s.grid.v_walls[y][0] = True
            s.grid.v_walls[y][s.w] = True
        for x in range(s.w):
            s.grid.h_walls[0][x] = True
            s.grid.h_walls[s.h][x] = True

    def undo(self):
        if self._saved_v is None:
            return
        self.scene.grid.v_walls = self._saved_v
        self.scene.grid.h_walls = self._saved_h


class AddEntity(Command):
    def __init__(self, scene, entity):
        self.scene, self.entity = scene, entity

    def execute(self):
        self.scene.add(self.entity)

    def undo(self):
        self.scene.remove(self.entity.id)


class RemoveEntity(Command):
    def __init__(self, scene, entity):
        self.scene, self.entity = scene, entity

    def execute(self):
        self.scene.remove(self.entity.id)

    def undo(self):
        self.scene.add(self.entity)
