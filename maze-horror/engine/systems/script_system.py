import hashlib
import json
from engine.systems.base import System
from engine.blueprints.compiler import compile_blueprint, ScriptContext


class ScriptSystem(System):
    name = "script"

    def __init__(self, loader):
        self.loader = loader
        self._cache = {}

    def invalidate(self, blueprint_name=None):
        if blueprint_name is None:
            self._cache.clear()
        else:
            for k in list(self._cache.keys()):
                if k[1] == blueprint_name:
                    del self._cache[k]

    def _signature(self, graph):
        if graph is None:
            return "none"
        return hashlib.md5(
            json.dumps(graph, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def _get(self, entity):
        s = entity.get("script")
        if not s or not s.enabled:
            return None
        graph = self.loader(s.blueprint)
        sig = self._signature(graph)
        key = (entity.id, s.blueprint, sig)
        if key not in self._cache:
            self._cache[key] = compile_blueprint(graph) if graph else None
        return self._cache[key]

    def update(self, scene, dt, input=None):
        for e in list(scene.entities.values()):
            fn = self._get(e)
            if not fn:
                continue
            script = e.get("script")
            ctx = ScriptContext(
                scene=scene, entity=e, input=input,
                time=scene.time, dt=dt, vars=script.vars,
            )
            fn(ctx)
