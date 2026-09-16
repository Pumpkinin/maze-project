import math
import pygame
from ui import skin
from engine.systems.render_system import RenderSystem2D


class Viewport:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.zoom = 40.0
        self.hover_cell = None
        self.renderer = RenderSystem2D()

    def world_to_screen(self, wx, wy):
        return (self.rect.x + (wx - self.cam_x) * self.zoom + self.rect.w / 2,
                self.rect.y + (wy - self.cam_y) * self.zoom + self.rect.h / 2)

    def screen_to_world(self, sx, sy):
        return ((sx - self.rect.x - self.rect.w / 2) / self.zoom + self.cam_x,
                (sy - self.rect.y - self.rect.h / 2) / self.zoom + self.cam_y)

    def update_hover(self, mx, my):
        if self.rect.collidepoint(mx, my):
            wx, wy = self.screen_to_world(mx, my)
            self.hover_cell = (int(math.floor(wx)), int(math.floor(wy)))
        else:
            self.hover_cell = None

    def zoom_at(self, mx, my, delta):
        f = 1.1 if delta > 0 else 1 / 1.1
        wx, wy = self.screen_to_world(mx, my)
        self.zoom = max(8.0, min(160.0, self.zoom * f))
        wx2, wy2 = self.screen_to_world(mx, my)
        self.cam_x += wx - wx2
        self.cam_y += wy - wy2

    def pan(self, dx, dy):
        self.cam_x -= dx / self.zoom
        self.cam_y -= dy / self.zoom

    def draw(self, surface, scene, skin_obj):
        self.renderer.draw(surface, scene, self)
        pygame.draw.rect(surface, skin.PANEL_BORDER, self.rect, 1)
        if self.hover_cell:
            hx, hy = self.hover_cell
            if 0 <= hx < scene.w and 0 <= hy < scene.h:
                sx, sy = self.world_to_screen(hx, hy)
                pygame.draw.rect(surface, (255, 255, 255),
                                 pygame.Rect(int(sx), int(sy),
                                             int(self.zoom), int(self.zoom)), 2)
