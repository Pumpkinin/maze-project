"""Базовые компоненты. Каждый обязан уметь to_dict/from_dict."""
from engine.ecs.entity import Component


class Transform(Component):
    type_name = "transform"

    def __init__(self, x=0.0, y=0.0, angle=0.0, scale=1.0):
        self.x, self.y = float(x), float(y)
        self.angle, self.scale = float(angle), float(scale)
        self.parent_id = None
        self.children = []

    def to_dict(self):
        return {"x": self.x, "y": self.y, "angle": self.angle,
                "scale": self.scale, "parent_id": self.parent_id}

    @classmethod
    def from_dict(cls, d):
        t = cls(d.get("x", 0), d.get("y", 0),
                d.get("angle", 0), d.get("scale", 1))
        t.parent_id = d.get("parent_id")
        return t

    def world_pos(self, scene):
        if not self.parent_id:
            return (self.x, self.y)
        p = scene.entities.get(self.parent_id)
        if not p or not p.has("transform"):
            return (self.x, self.y)
        px, py = p.get("transform").world_pos(scene)
        return (px + self.x, py + self.y)

    def world_angle(self, scene):
        if not self.parent_id:
            return self.angle
        p = scene.entities.get(self.parent_id)
        if not p or not p.has("transform"):
            return self.angle
        return p.get("transform").world_angle(scene) + self.angle


class Camera(Component):
    type_name = "camera"

    def __init__(self, fov=110.0, effects_preset="default",
                 pitch_min=-30.0, pitch_max=10.0, height=0.5,
                 internal_w=240, internal_h=150):
        self.fov = float(fov)
        self.effects_preset = effects_preset
        self.pitch_min = float(pitch_min)
        self.pitch_max = float(pitch_max)
        self.height = float(height)
        self.internal_w = int(internal_w)
        self.internal_h = int(internal_h)

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class Collider(Component):
    type_name = "collider"

    def __init__(self, shape="circle", radius=0.2, w=0.5, h=0.5,
                 offset_x=0.0, offset_y=0.0, is_static=False):
        self.shape = shape
        self.radius = float(radius)
        self.w, self.h = float(w), float(h)
        self.offset_x, self.offset_y = float(offset_x), float(offset_y)
        self.is_static = bool(is_static)

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class Rigidbody(Component):
    type_name = "rigidbody"

    def __init__(self, vx=0.0, vy=0.0, damping=0.0):
        self.vx, self.vy, self.damping = float(vx), float(vy), float(damping)

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class Sprite2D(Component):
    type_name = "sprite2d"

    def __init__(self, kind="player", color=(240, 80, 80)):
        self.kind = kind
        self.color = tuple(int(c) for c in color)

    def to_dict(self):
        return {"kind": self.kind, "color": list(self.color)}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("kind", "player"), tuple(d.get("color", (240, 80, 80))))


class Script(Component):
    type_name = "script"

    def __init__(self, blueprint="", enabled=True, vars=None):
        self.blueprint = blueprint
        self.enabled = bool(enabled)
        self.vars = dict(vars or {})

    def to_dict(self):
        return {"blueprint": self.blueprint, "enabled": self.enabled,
                "vars": self.vars}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("blueprint", ""), d.get("enabled", True),
                   d.get("vars", {}))


class Name(Component):
    type_name = "name"

    def __init__(self, text=""):
        self.text = text

    def to_dict(self):
        return {"text": self.text}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("text", ""))


class Tags(Component):
    type_name = "tags"

    def __init__(self, tags=None):
        self.tags = set(tags or [])

    def to_dict(self):
        return {"tags": sorted(self.tags)}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("tags", []))


COMPONENT_TYPES = {
    c.type_name: c for c in (
        Transform, Camera, Collider, Rigidbody,
        Sprite2D, Script, Name, Tags,
    )
}
