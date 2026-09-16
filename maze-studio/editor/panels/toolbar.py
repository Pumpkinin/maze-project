import pygame
from ui import skin


class ToolbarButton:
    def __init__(self, label, rect, on_click, tool=None):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.on_click = on_click
        self.tool = tool
        self.active = False
        self.hovered = False

    def draw(self, surface, skin_obj):
        color = (skin.ACCENT if self.active
                 else (skin.ACCENT_HOVER if self.hovered else (60, 60, 66)))
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, skin.PANEL_BORDER, self.rect, 1, border_radius=4)
        t = skin_obj.render(self.label)
        surface.blit(t, t.get_rect(center=self.rect.center))


class Toolbar:
    def __init__(self, rect, app):
        self.rect = pygame.Rect(rect)
        self.app = app
        self.buttons = []
        self._build()

    def _build(self):
        x, y, h = 10, 6, 28

        def add(label, action, tool=None):
            nonlocal x
            w = self.app.skin.text_size(label, bold=True)[0] + 20
            self.buttons.append(
                ToolbarButton(label, pygame.Rect(x, y, w, h), action, tool))
            x += w + 6

        add("New", self.app.action_new)
        add("Open", self.app.action_open)
        add("Save", self.app.action_save)
        x += 10
        add("Undo", self.app.action_undo)
        add("Redo", self.app.action_redo)
        x += 10
        add("Select", lambda: self.app.set_tool("select"), "select")
        add("Wall V", lambda: self.app.set_tool("wall_v"), "wall_v")
        add("Wall H", lambda: self.app.set_tool("wall_h"), "wall_h")
        add("Erase",  lambda: self.app.set_tool("erase"),  "erase")
        add("Player", lambda: self.app.set_tool("spawn"),  "spawn")
        add("Exit",   lambda: self.app.set_tool("exit"),   "exit")
        x += 10
        add("Play", self.app.toggle_preview)

        for b in self.buttons:
            b.active = (b.tool == self.app.tool)

    def draw(self, surface, skin_obj):
        pygame.draw.rect(surface, skin.PANEL_BG, self.rect)
        pygame.draw.line(surface, skin.PANEL_BORDER,
                         (0, self.rect.bottom - 1),
                         (self.rect.w, self.rect.bottom - 1))
        mx, my = pygame.mouse.get_pos()
        for b in self.buttons:
            b.hovered = b.rect.collidepoint(mx, my)
            b.draw(surface, skin_obj)
