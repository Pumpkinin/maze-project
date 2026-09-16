from engine.ecs.entity import Entity
from engine.ecs.components import COMPONENT_TYPES


class Prefab:
    def __init__(self, name, components=None):
        self.name = name
        self.components = dict(components or {})

    def instantiate(self, scene=None):
        e = Entity(name=self.name)
        for cname, comp in self.components.items():
            new = COMPONENT_TYPES[cname].from_dict(comp.to_dict())
            e.add(new)
        if scene is not None:
            scene.add(e)
        return e

    def to_dict(self):
        return {"name": self.name,
                "components": {k: v.to_dict() for k, v in self.components.items()}}

    @classmethod
    def from_dict(cls, d):
        p = cls(d["name"])
        for cname, cdata in d.get("components", {}).items():
            ctype = COMPONENT_TYPES.get(cname)
            if ctype:
                p.components[cname] = ctype.from_dict(cdata)
        return p
