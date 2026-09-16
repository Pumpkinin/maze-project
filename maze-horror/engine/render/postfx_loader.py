import os
from core.serialize import load_json


def load_effects_preset(path):
    if not os.path.isfile(path):
        return {"effects": []}
    return load_json(path)


def find_preset(root, name):
    p = os.path.join(root, "data", "effects", name + ".json")
    if os.path.isfile(p):
        return load_effects_preset(p)
    return {"effects": []}
