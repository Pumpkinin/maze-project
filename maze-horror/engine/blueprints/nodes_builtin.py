"""Встроенные узлы. Каждый: evaluate(ctx, in_vals) -> {out_pin: value}."""
import math
from engine.blueprints.registry import register


class Node:
    type_name = "Node"
    inputs = {}
    outputs = {}

    def __init__(self, node_id, params=None):
        self.id = node_id
        self.params = dict(params or {})

    def evaluate(self, ctx, in_vals):
        return {}


# ── события ────────────────────────────────────────────────────
@register
class OnTick(Node):
    type_name = "OnTick"
    outputs = {"out": "flow"}

    def evaluate(self, ctx, in_vals):
        return {"out": True}


@register
class OnInput(Node):
    type_name = "OnInput"
    outputs = {"out": "flow", "value": "float"}

    def evaluate(self, ctx, in_vals):
        a = self.params.get("action", "")
        v = ctx.input.axis(a) if ctx.input else 0.0
        return {"out": v > 0.0 or v < 0.0, "value": v}


@register
class OnPressed(Node):
    type_name = "OnPressed"
    outputs = {"out": "flow"}

    def evaluate(self, ctx, in_vals):
        return {"out": bool(ctx.input and ctx.input.pressed(self.params.get("action", "")))}


@register
class OnCollision(Node):
    type_name = "OnCollision"
    outputs = {"out": "flow"}

    def evaluate(self, ctx, in_vals):
        fired = ctx.vars.get("_collision_fired", False)
        ctx.vars["_collision_fired"] = False
        return {"out": fired}


@register
class OnTimer(Node):
    type_name = "OnTimer"
    outputs = {"out": "flow"}

    def evaluate(self, ctx, in_vals):
        period = float(self.params.get("period", 1.0))
        if period <= 0:
            return {"out": False}
        last = ctx.vars.get("_timer_last", 0.0)
        if ctx.time - last >= period:
            ctx.vars["_timer_last"] = ctx.time
            return {"out": True}
        return {"out": False}


# ── логика ─────────────────────────────────────────────────────
@register
class Branch(Node):
    type_name = "Branch"
    inputs = {"cond": "bool"}
    outputs = {"true": "flow", "false": "flow"}

    def evaluate(self, ctx, in_vals):
        c = bool(in_vals.get("cond", False))
        return {"true": c, "false": not c}


@register
class Compare(Node):
    type_name = "Compare"
    inputs = {"a": "any", "b": "any"}
    outputs = {"result": "bool"}

    def evaluate(self, ctx, in_vals):
        op = self.params.get("op", "==")
        a, b = in_vals.get("a"), in_vals.get("b")
        try:
            return {"result": {
                "==": a == b, "!=": a != b,
                "<": a < b, "<=": a <= b,
                ">": a > b, ">=": a >= b,
            }.get(op, False)}
        except TypeError:
            return {"result": False}


@register
class MathOp(Node):
    type_name = "MathOp"
    inputs = {"a": "float", "b": "float"}
    outputs = {"result": "float"}

    def evaluate(self, ctx, in_vals):
        op = self.params.get("op", "+")
        a = float(in_vals.get("a", 0.0))
        b = float(in_vals.get("b", 0.0))
        v = {"+": a + b, "-": a - b, "*": a * b,
             "/": (a / b if b else 0.0),
             "min": min(a, b), "max": max(a, b)}.get(op, 0.0)
        return {"result": v}


@register
class ConstFloat(Node):
    type_name = "ConstFloat"
    outputs = {"v": "float"}

    def evaluate(self, ctx, in_vals):
        return {"v": float(self.params.get("value", 0.0))}


@register
class GetVar(Node):
    type_name = "GetVar"
    outputs = {"v": "any"}

    def evaluate(self, ctx, in_vals):
        return {"v": ctx.vars.get(self.params.get("name", ""), None)}


@register
class SetVar(Node):
    type_name = "SetVar"
    inputs = {"in": "flow", "v": "any"}
    outputs = {"out": "flow"}

    def evaluate(self, ctx, in_vals):
        ctx.vars[self.params.get("name", "")] = in_vals.get("v")
        return {"out": True}


@register
class Log(Node):
    type_name = "Log"
    inputs = {"in": "flow", "v": "any"}
    outputs = {"out": "flow"}

    def evaluate(self, ctx, in_vals):
        if in_vals.get("in"):
            print(f"[bp:{ctx.entity.id}] {self.params.get('msg', '')}: {in_vals.get('v')}")
        return {"out": True}


# ── движение ───────────────────────────────────────────────────
@register
class MoveRelative(Node):
    type_name = "MoveRelative"
    inputs = {"in": "flow", "fwd": "float", "str": "float"}
    outputs = {"out": "flow", "wish_speed": "float"}

    def evaluate(self, ctx, in_vals):
        if not in_vals.get("in"):
            return {"out": False, "wish_speed": 0.0}
        fwd = float(in_vals.get("fwd", 0.0))
        str_ = float(in_vals.get("str", 0.0))
        speed = float(ctx.vars.get(self.params.get("speed_var", "speed"), 2.5))
        t = ctx.entity.get("transform")
        if t is None:
            return {"out": False}
        dt = ctx.dt
        ca, sa = math.cos(t.angle), math.sin(t.angle)
        dx = ca * fwd * speed * dt + sa * str_ * speed * dt
        dy = sa * fwd * speed * dt - ca * str_ * speed * dt
        # сохраняем delta для PhysicsSystem
        ctx.vars["_delta"] = (dx, dy)
        ws = math.hypot(dx, dy) / dt if dt > 0 else 0.0
        ctx.vars["_wish_speed"] = ws
        return {"out": True, "wish_speed": ws}


@register
class Teleport(Node):
    type_name = "Teleport"
    inputs = {"in": "flow", "x": "float", "y": "float"}
    outputs = {"out": "flow"}

    def evaluate(self, ctx, in_vals):
        if not in_vals.get("in"):
            return {"out": False}
        t = ctx.entity.get("transform")
        if t is not None:
            t.x = float(in_vals.get("x", t.x))
            t.y = float(in_vals.get("y", t.y))
        return {"out": True}


@register
class LookYawMouse(Node):
    type_name = "LookYawMouse"
    inputs = {"in": "flow", "dx": "float"}
    outputs = {"out": "flow"}

    def evaluate(self, ctx, in_vals):
        if not in_vals.get("in"):
            return {"out": False}
        dx = float(in_vals.get("dx", 0.0))
        t = ctx.entity.get("transform")
        if t is not None:
            t.angle += dx * float(self.params.get("sensitivity", 0.003))
        return {"out": True}


@register
class SetCameraEffect(Node):
    type_name = "SetCameraEffect"
    inputs = {"in": "flow"}
    outputs = {"out": "flow"}

    def evaluate(self, ctx, in_vals):
        if not in_vals.get("in"):
            return {"out": False}
        cam = ctx.entity.get("camera")
        if cam:
            cam.effects_preset = self.params.get("preset", cam.effects_preset)
        return {"out": True}


@register
class EmitSignal(Node):
    type_name = "EmitSignal"
    inputs = {"in": "flow"}
    outputs = {"out": "flow"}

    def evaluate(self, ctx, in_vals):
        if in_vals.get("in"):
            ctx.scene.bus.emit(self.params.get("name", "signal"),
                               entity=ctx.entity)
        return {"out": True}
