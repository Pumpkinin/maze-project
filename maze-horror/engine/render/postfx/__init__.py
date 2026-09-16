from .base import PostEffect
from .fog import FogEffect
from .scanlines import ScanlinesEffect
from .vignette import VignetteEffect
from .darken import DarkenEffect
from .bob import HeadBobEffect

EFFECT_TYPES = {
    "fog": FogEffect,
    "scanlines": ScanlinesEffect,
    "vignette": VignetteEffect,
    "darken": DarkenEffect,
    "bob": HeadBobEffect,
}


def build_stack(preset_dict):
    stack = []
    for d in preset_dict.get("effects", []):
        cls = EFFECT_TYPES.get(d.get("type"))
        if not cls:
            continue
        fx = cls()
        fx.from_dict(d)
        stack.append(fx)
    return stack
