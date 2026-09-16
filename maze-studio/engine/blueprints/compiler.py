"""Компилятор графа в callable(ctx). Топологический обход от событийных узлов."""
from engine.blueprints.registry import get as get_node_type
from engine.blueprints import nodes_builtin  # noqa: F401  (регистрация узлов)


class ScriptContext:
    def __init__(self, scene, entity, input, time, dt, vars):
        self.scene = scene
        self.entity = entity
        self.input = input
        self.time = time
        self.dt = dt
        self.vars = vars


def compile_blueprint(graph_dict):
    if not graph_dict:
        return None

    nodes = {n["id"]: n for n in graph_dict.get("nodes", [])}
    edges = graph_dict.get("edges", [])

    out_map = {}
    for e in edges:
        out_map.setdefault(e["from_id"], []).append(
            (e["from_pin"], e["to_id"], e["to_pin"]))

    insts = {}
    for nid, nd in nodes.items():
        cls = get_node_type(nd["type"])
        if cls:
            insts[nid] = cls(nid, nd.get("params", {}))

    event_ids = [nid for nid, inst in insts.items()
                 if inst.type_name.startswith("On")]

    def eval_node(ctx, nid, in_vals, visited):
        if nid in visited or nid not in insts:
            return {}
        visited.add(nid)
        outs = insts[nid].evaluate(ctx, in_vals)
        for from_pin, to_id, to_pin in out_map.get(nid, []):
            if from_pin in outs and outs[from_pin]:
                eval_node(ctx, to_id, {to_pin: outs[from_pin]}, visited)
        return outs

    def run(ctx):
        ctx.vars.pop("_delta", None)
        for eid in event_ids:
            inst = insts[eid]
            outs = inst.evaluate(ctx, {})
            for from_pin, to_id, to_pin in out_map.get(eid, []):
                if from_pin in outs and outs[from_pin]:
                    eval_node(ctx, to_id, {to_pin: outs[from_pin]}, set())

    return run
