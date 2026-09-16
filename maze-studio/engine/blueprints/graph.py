from core.serialize import save_json, load_json


class Blueprint:
    def __init__(self, id="", nodes=None, edges=None, vars=None):
        self.id = id
        self.nodes = list(nodes or [])
        self.edges = list(edges or [])
        self.vars = dict(vars or {})

    def to_dict(self):
        return {"id": self.id, "nodes": self.nodes,
                "edges": self.edges, "vars": self.vars}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("id", ""), d.get("nodes"), d.get("edges"), d.get("vars"))

    def save(self, path):
        save_json(path, self.to_dict())

    @classmethod
    def load(cls, path):
        return cls.from_dict(load_json(path))
