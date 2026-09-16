import os
import pygame
from ui import skin


class AssetBrowser:
    def __init__(self, rect, root):
        self.rect = pygame.Rect(rect)
        self.root = root
        self.kind = "levels"

    def draw(self, surface, skin_obj, ui, on_pick=None):
        pygame.draw.rect(surface, skin.PANEL_BG, self.rect)
        pygame.draw.rect(surface, skin.PANEL_BORDER, self.rect, 1)

        kinds = ["levels", "prefabs", "blueprints", "effects", "input"]
        x = self.rect.x + 8
        for k in kinds:
            w = skin_obj.text_size(k)[0] + 12
            r = pygame.Rect(x, self.rect.y + 6, w, 20)
            active = (k == self.kind)
            pygame.draw.rect(surface, skin.ACCENT if active else (60, 60, 66),
                             r, border_radius=3)
            surface.blit(skin_obj.render(k, skin.TEXT), (r.x + 6, r.y + 3))
            if r.collidepoint(ui.mouse_pos) and ui.mouse_pressed:
                self.kind = k
            x += w + 4

        d = os.path.join(self.root, "data", self.kind)
        y = self.rect.y + 34
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if not f.endswith(".json"):
                    continue
                r = pygame.Rect(self.rect.x + 4, y, self.rect.w - 8, 18)
                hovered = r.collidepoint(ui.mouse_pos)
                if hovered:
                    pygame.draw.rect(surface, (55, 55, 62), r)
                surface.blit(skin_obj.render(f, skin.TEXT), (r.x + 6, y + 2))
                if ui.mouse_pressed and hovered and on_pick:
                    on_pick(self.kind, os.path.join(d, f))
                y += 18
                if y > self.rect.bottom:
                    break
