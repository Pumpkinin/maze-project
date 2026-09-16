import math
from editor.tools.base import Tool


class SelectTool(Tool):
    name = "select"
    label = "Select"

    def apply(self, scene, wx, wy, cx, cy, history=None):
        best = None
        bd = 1e9
        for e in scene.entities.values():
            t = e.get("transform")
            if not t:
                continue
            ex, ey = t.world_pos(scene)
            d = math.hypot(ex - wx, ey - wy)
            if d < 0.5 and d < bd:
                bd = d
                best = e
        scene.selection = best.id if best else None
