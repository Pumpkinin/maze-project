import pygame

SCAN_NAMES = {
    4: "A", 5: "B", 6: "C", 7: "D", 8: "E", 9: "F", 10: "G", 11: "H",
    12: "I", 13: "J", 14: "K", 15: "L", 16: "M", 17: "N", 18: "O",
    19: "P", 20: "Q", 21: "R", 22: "S", 23: "T", 24: "U", 25: "V",
    26: "W", 27: "X", 28: "Y", 29: "Z",
    30: "1", 31: "2", 32: "3", 33: "4", 34: "5", 35: "6", 36: "7",
    37: "8", 38: "9", 39: "0",
    40: "Enter", 41: "Esc", 42: "Backspace", 43: "Tab", 44: "Space",
    79: "→", 80: "←", 81: "↓", 82: "↑",
    224: "LCtrl", 225: "LShift", 226: "LAlt",
    228: "RCtrl", 229: "RShift", 230: "RAlt",
    59: "F1", 60: "F2", 61: "F3", 62: "F4", 63: "F5", 64: "F6",
    65: "F7", 66: "F8", 67: "F9", 68: "F10", 69: "F11", 70: "F12",
}


def binding_to_string(b):
    if b.startswith("scan:"):
        sc = int(b.split(":")[1])
        return SCAN_NAMES.get(sc, f"scan{sc}")
    if b.startswith("mouse:"):
        btn = int(b.split(":")[1])
        return {1: "ЛКМ", 2: "СКМ", 3: "ПКМ"}.get(btn, f"Мышь {btn}")
    if b.startswith("joy"):
        return b.replace("joy", "Joy ")
    return b


class Action:
    def __init__(self, name, label="", atype="button", bindings=None):
        self.name = name
        self.label = label or name
        self.type = atype
        self.bindings = list(bindings or [])
        self.value = 0.0
        self.pressed = False
        self.released = False
        self.held = False
        self._prev = 0.0


class ActionMap:
    def __init__(self, name):
        self.name = name
        self.actions = {}

    def add_action(self, name, label="", atype="button", bindings=None):
        a = Action(name, label, atype, bindings)
        self.actions[name] = a
        return a

    def to_dict(self):
        return {"actions": {
            n: {"label": a.label, "type": a.type, "bindings": a.bindings}
            for n, a in self.actions.items()
        }}

    @classmethod
    def from_dict(cls, name, d):
        m = cls(name)
        for n, ad in d.get("actions", {}).items():
            m.add_action(n, ad.get("label", n), ad.get("type", "button"),
                         ad.get("bindings", []))
        return m
