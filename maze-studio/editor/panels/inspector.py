import pygame
from ui import skin


class InspectorPanel:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw(self, surface, app, skin_obj):
        scene = app.scene
        pygame.draw.rect(surface, skin.PANEL_BG, self.rect)
        pygame.draw.rect(surface, skin.PANEL_BORDER, self.rect, 1)
        title = skin_obj.render("Inspector", skin.TEXT, bold=True)
        surface.blit(title, (self.rect.x + 12, self.rect.y + 10))

        sel = scene.entities.get(scene.selection) if scene.selection else None
        y = self.rect.y + 38
        if not sel:
            t = skin_obj.render("Ничего не выбрано", skin.TEXT_DIM)
            surface.blit(t, (self.rect.x + 12, y))
            return

        y = self._scalar(surface, skin_obj, app, sel, "name", "text", y,
                         is_text=True)
        for cname, comp in list(sel.components.items()):
            y = self._section(surface, skin_obj, cname, y)
            y = self._component_fields(surface, skin_obj, app, comp, cname, y)

    def _section(self, surface, skin_obj, name, y):
        t = skin_obj.render(name, skin.TEXT, bold=True)
        surface.blit(t, (self.rect.x + 12, y))
        pygame.draw.line(surface, skin.PANEL_BORDER,
                         (self.rect.x + 12, y + 16),
                         (self.rect.right - 12, y + 16))
        return y + 22

    def _component_fields(self, surface, skin_obj, app, comp, cname, y):
        simple = {
            "transform": ("x", "y", "angle", "scale", "parent_id"),
            "camera": ("fov", "pitch_min", "pitch_max", "height",
                       "effects_preset", "internal_w", "internal_h"),
            "collider": ("shape", "radius", "w", "h", "is_static"),
            "rigidbody": ("vx", "vy", "damping"),
            "sprite2d": ("kind",),
            "script": ("blueprint", "enabled"),
            "name": ("text",),
        }.get(cname, ())
        for attr in simple:
            if not hasattr(comp, attr):
                continue
            v = getattr(comp, attr)
            if isinstance(v, bool):
                y = self._bool(surface, skin_obj, app, comp, attr, y)
            elif isinstance(v, (int, float)):
                y = self._scalar(surface, skin_obj, app, comp, attr, y)
            else:
                y = self._scalar(surface, skin_obj, app, comp, attr, y, is_text=True)
        if cname == "script":
            for k, v in list(comp.vars.items()):
                if k.startswith("_"):
                    continue
                y = self._kv(surface, skin_obj, app, comp, k, y)
        return y

    def _scalar(self, surface, skin_obj, app, comp, attr, y,
                is_text=False):
        rect = pygame.Rect(self.rect.x + 12, y, self.rect.w - 24, 20)
        v = getattr(comp, attr, "")
        if is_text:
            new = app.ui.text_input(surface, rect, str(v),
                                    wid=("insp_txt", id(comp), attr))
            if new != str(v):
                setattr(comp, attr, new)
        else:
            new, _ = app.ui.float_field(surface, rect, float(v), attr, "",
                                        wid=("insp", id(comp), attr))
            if new != float(v):
                setattr(comp, attr, new)
        return y + 22

    def _bool(self, surface, skin_obj, app, comp, attr, y):
        rect = pygame.Rect(self.rect.x + 12, y, self.rect.w - 24, 20)
        v = bool(getattr(comp, attr, False))
        new = app.ui.checkbox(surface, rect, attr, v, wid=("insp_b", id(comp), attr))
        if new != v:
            setattr(comp, attr, new)
        return y + 22

    def _kv(self, surface, skin_obj, app, comp, key, y):
        rect = pygame.Rect(self.rect.x + 12, y, self.rect.w - 24, 20)
        v = comp.vars.get(key, 0.0)
        try:
            fv = float(v)
        except (TypeError, ValueError):
            fv = 0.0
        new, _ = app.ui.float_field(surface, rect, fv, key, "",
                                    wid=("insp_kv", id(comp), key))
        if new != fv:
            comp.vars[key] = new
        return y + 22
