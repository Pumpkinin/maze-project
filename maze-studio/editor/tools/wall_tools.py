from core.math_utils import clamp
from editor.tools.base import Tool
from editor.history import PaintWallV, PaintWallH, EraseAt


class WallVTool(Tool):
    name = "wall_v"
    label = "Wall V"

    def apply(self, scene, wx, wy, cx, cy, history=None):
        fx = wx - cx
        ex = cx if fx < 0.5 else cx + 1
        ex = clamp(ex, 0, scene.w)
        if not (0 <= cy < scene.h):
            return
        if scene.grid.v_walls[cy][ex]:
            return
        cmd = PaintWallV(scene, ex, cy)
        (history.push if history else cmd.execute)(cmd)


class WallHTool(Tool):
    name = "wall_h"
    label = "Wall H"

    def apply(self, scene, wx, wy, cx, cy, history=None):
        fy = wy - cy
        ey = cy if fy < 0.5 else cy + 1
        ey = clamp(ey, 0, scene.h)
        if not (0 <= cx < scene.w):
            return
        if scene.grid.h_walls[ey][cx]:
            return
        cmd = PaintWallH(scene, cx, ey)
        (history.push if history else cmd.execute)(cmd)


class EraseTool(Tool):
    name = "erase"
    label = "Erase"

    def apply(self, scene, wx, wy, cx, cy, history=None):
        if not (0 <= cx < scene.w and 0 <= cy < scene.h):
            return
        cmd = EraseAt(scene, cx, cy)
        (history.push if history else cmd.execute)(cmd)
