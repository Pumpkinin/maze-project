from core.events import EventBus
from engine.ecs.entity import Entity
from engine.ecs.components import COMPONENT_TYPES
from engine.physics.grid import WallGrid


class Scene:
    def __init__(self, w=16, h=16):
        self.w, self.h = int(w), int(h)
        self.grid = WallGrid(self.w, self.h)
        self.entities = {}
        self.systems = []
        self.bus = EventBus()
        self.time = 0.0
        self.selection = None
        self.meta = {}

    # ─── сущности ────────────────────────────────────────────
    def add(self, entity):
        self.entities[entity.id] = entity
        return entity

    def remove(self, entity_id):
        e = self.entities.pop(entity_id, None)
        if e and e.has("transform"):
            t = e.get("transform")
            if t.parent_id and t.parent_id in self.entities:
                p = self.entities[t.parent_id].get("transform")
                if p and entity_id in p.children:
                    p.children.remove(entity_id)
        return e

    def by_name(self, name):
        for e in self.entities.values():
            n = e.get("name")
            if n and n.text == name:
                return e
        return None

    def by_tag(self, tag):
        return [e for e in self.entities.values()
                if e.has("tags") and tag in e.get("tags").tags]

    def detach(self, entity_id):
        e = self.entities.get(entity_id)
        if not e or not e.has("transform"):
            return
        t = e.get("transform")
        if t.parent_id and t.parent_id in self.entities:
            p = self.entities[t.parent_id].get("transform")
            if p and entity_id in p.children:
                p.children.remove(entity_id)
        t.parent_id = None

    def attach(self, child_id, parent_id):
        c = self.entities.get(child_id)
        p = self.entities.get(parent_id)
        if not c or not p or not c.has("transform") or not p.has("transform"):
            return False
        self.detach(child_id)
        c.get("transform").parent_id = parent_id
        p.get("transform").children.append(child_id)
        return True

    # ─── системы ────────────────────────────────────────────
    def add_system(self, system):
        self.systems.append(system)
        system.on_attach(self)
        return system

    def update(self, dt, input=None):
        self.time += dt
        for s in self.systems:
            s.update(self, dt, input)

    # ─── сериализация ───────────────────────────────────────
    def to_dict(self):
        return {
            "w": self.w, "h": self.h,
            "v_walls": [r[:] for r in self.grid.v_walls],
            "h_walls": [r[:] for r in self.grid.h_walls],
            "entities": [e.to_dict() for e in self.entities.values()],
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, d):
        s = cls(d["w"], d["h"])
        s.grid.v_walls = [r[:] for r in d["v_walls"]]
        s.grid.h_walls = [r[:] for r in d["h_walls"]]
        s.meta = dict(d.get("meta", {}))
        for ed in d.get("entities", []):
            e = Entity(id=ed["id"], name=ed.get("name", ""))
            for cname, cdata in ed.get("components", {}).items():
                ctype = COMPONENT_TYPES.get(cname)
                if ctype:
                    e.add(ctype.from_dict(cdata))
            s.add(e)
        for e in s.entities.values():
            t = e.get("transform")
            if t and t.parent_id and t.parent_id in s.entities:
                p = s.entities[t.parent_id].get("transform")
                if p and e.id not in p.children:
                    p.children.append(e.id)
        return s
