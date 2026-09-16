from core.uid import new_id


class Component:
    type_name = "component"

    def to_dict(self):
        return {}

    @classmethod
    def from_dict(cls, d):
        return cls()


class Entity:
    def __init__(self, id=None, name=""):
        self.id = id or new_id("e")
        self.name = name
        self.components = {}
        self.alive = True

    def add(self, comp):
        self.components[comp.type_name] = comp
        return comp

    def get(self, type_name):
        return self.components.get(type_name)

    def has(self, type_name):
        return type_name in self.components

    def remove(self, type_name):
        self.components.pop(type_name, None)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "components": {k: v.to_dict() for k, v in self.components.items()},
        }
