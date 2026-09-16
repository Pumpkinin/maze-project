import pygame
from ui import skin


class HierarchyPanel:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def _roots(self, scene):
        out = []
        for e in scene.entities.values():
            t = e.get("transform")
            if not t or not t.parent_id or t.parent_id not in scene.entities:
                out.append(e)
        return out

    def _children(self, scene, pid):
        p = scene.entities.get(pid)
        if not p or not p.has("transform"):
            return []
        return [scene.entities[c] for c in p.get("transform").children
                if c in scene.entities]

    def draw(self, surface, scene, skin_obj, ui):
        pygame.draw.rect(surface, skin.PANEL_BG, self.rect)
        pygame.draw.rect(surface, skin.PANEL_BORDER, self.rect, 1)
        title = skin_obj.render("Иерархия", skin.TEXT, bold=True)
        surface.blit(title, (self.rect.x + 12, self.rect.y + 10))
        y = self.rect.y + 38
        for e in self._roots(scene):
            y = self._draw_entity(surface, scene, e, y, 0, skin_obj, ui)

    def _draw_entity(self, surface, scene, e, y, depth, skin_obj, ui):
        if y > self.rect.bottom:
            return y
        rect = pygame.Rect(self.rect.x + 4, y, self.rect.w - 8, 18)
        hovered = rect.collidepoint(ui.mouse_pos)
        if e.id == scene.selection:
            pygame.draw.rect(surface, skin.ACCENT, rect)
        elif hovered:
            pygame.draw.rect(surface, (55, 55, 62), rect)
        name = e.get("name").text if e.has("name") else e.id
        t = skin_obj.render(name, skin.TEXT)
        surface.blit(t, (rect.x + 6 + depth * 12, y + 2))
        if ui.mouse_pressed and rect.collidepoint(ui.mouse_pos):
            scene.selection = e.id
        y += 18
        for c in self._children(scene, e.id):
            y = self._draw_entity(surface, scene, c, y, depth + 1, skin_obj, ui)
        return y
