import json
import pygame
from engine.input.action_map import ActionMap


class Input:
    def __init__(self):
        self.contexts = {}
        self.context_stack = []
        self.default_context = "gameplay"
        self._raw_pressed_scans = set()
        self._raw_down_scans = set()
        self._raw_mouse_buttons = set()
        self._raw_mouse_pressed = set()
        self._raw_joy_buttons = {}
        self._raw_joy_axes = {}
        self._capture_callback = None

    # ─── контексты ──────────────────────────────────────────
    def add_context(self, m):
        self.contexts[m.name] = m

    def push_context(self, name):
        if name in self.contexts and name not in self.context_stack:
            self.context_stack.append(name)

    def pop_context(self, name=None):
        if not self.context_stack:
            return
        if name is None:
            self.context_stack.pop()
        elif name in self.context_stack:
            self.context_stack.remove(name)

    # ─── json ───────────────────────────────────────────────
    def to_dict(self):
        return {
            "contexts": {n: m.to_dict() for n, m in self.contexts.items()},
            "context_stack": list(self.context_stack),
            "default_context": self.default_context,
        }

    @staticmethod
    def from_dict(d):
        inp = Input()
        for n, cd in d.get("contexts", {}).items():
            inp.add_context(ActionMap.from_dict(n, cd))
        inp.context_stack = list(d.get("context_stack", []))
        inp.default_context = d.get("default_context", "gameplay")
        return inp

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def load(path):
        from core.serialize import load_json
        return Input.from_dict(load_json(path))
    # ─── кадр ───────────────────────────────────────────────
    def begin_frame(self, events):
        self._raw_pressed_scans.clear()
        self._raw_mouse_pressed.clear()
        for e in events:
            if e.type == pygame.KEYDOWN:
                self._raw_pressed_scans.add(e.scancode)
                self._raw_down_scans.add(e.scancode)
                if self._capture_callback:
                    self._capture_callback(f"scan:{e.scancode}")
                    self._capture_callback = None
            elif e.type == pygame.KEYUP:
                self._raw_down_scans.discard(e.scancode)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self._raw_mouse_buttons.add(e.button)
                self._raw_mouse_pressed.add(e.button)
                if self._capture_callback:
                    self._capture_callback(f"mouse:{e.button}")
                    self._capture_callback = None
            elif e.type == pygame.MOUSEBUTTONUP:
                self._raw_mouse_buttons.discard(e.button)
            elif e.type == pygame.JOYBUTTONDOWN:
                self._raw_joy_buttons[(e.joy, e.button)] = True
                if self._capture_callback:
                    self._capture_callback(f"joy{e.joy}:btn{e.button}")
                    self._capture_callback = None
            elif e.type == pygame.JOYBUTTONUP:
                self._raw_joy_buttons[(e.joy, e.button)] = False
            elif e.type == pygame.JOYAXISMOTION:
                self._raw_joy_axes[(e.joy, e.axis)] = e.value

        for cn in self.context_stack:
            ctx = self.contexts.get(cn)
            if not ctx:
                continue
            for a in ctx.actions.values():
                self._update_action(a)

    def _binding_value(self, b):
        if b.startswith("scan:"):
            return 1.0 if int(b.split(":")[1]) in self._raw_down_scans else 0.0
        if b.startswith("mouse:"):
            return 1.0 if int(b.split(":")[1]) in self._raw_mouse_buttons else 0.0
        if b.startswith("joy"):
            try:
                rest = b[3:]
                joy_s, name = rest.split(":", 1)
                j = int(joy_s)
                if name.startswith("btn"):
                    return 1.0 if self._raw_joy_buttons.get(
                        (j, int(name[3:])), False) else 0.0
                if name.startswith("axis"):
                    tail = name[4:]
                    sgn = 1.0
                    if tail.endswith("+"):
                        tail = tail[:-1]
                    elif tail.endswith("-"):
                        tail = tail[:-1]
                        sgn = -1.0
                    return max(0.0, self._raw_joy_axes.get((j, int(tail)), 0.0) * sgn)
            except Exception:
                return 0.0
        return 0.0

    def _update_action(self, a):
        v = 0.0
        for b in a.bindings:
            v = max(v, self._binding_value(b))
        a.value = v
        a.held = v > 0.5
        a.pressed = a.held and a._prev <= 0.5
        a.released = (not a.held) and a._prev > 0.5
        a._prev = v

    # ─── публичный API ──────────────────────────────────────
    def _find_action(self, name):
        for cn in reversed(self.context_stack):
            ctx = self.contexts.get(cn)
            if ctx and name in ctx.actions:
                return ctx.actions[name]
        return None

    def held(self, name):
        a = self._find_action(name)
        return a.held if a else False

    def pressed(self, name):
        a = self._find_action(name)
        return a.pressed if a else False

    def released(self, name):
        a = self._find_action(name)
        return a.released if a else False

    def axis(self, name):
        a = self._find_action(name)
        return a.value if a else 0.0

    def capture_next_binding(self, cb):
        self._capture_callback = cb
