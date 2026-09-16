import math
import pygame


class RenderSystem2D:
    """Top-down рендер сцены для редактора."""

    def draw(self, surface, scene, cam):
        pygame.draw.rect(surface, (24, 24, 28), cam.rect)
        surface.set_clip(cam.rect)

        x0, y0 = cam.world_to_screen(0, 0)
        x1, y1 = cam.world_to_screen(scene.w, scene.h)

        gx = x0
        while gx <= x1:
            pygame.draw.line(surface, (50, 50, 58), (gx, y0), (gx, y1), 1)
            gx += cam.zoom
        gy = y0
        while gy <= y1:
            pygame.draw.line(surface, (50, 50, 58), (x0, gy), (x1, gy), 1)
            gy += cam.zoom

        th = max(2, int(cam.zoom * 0.12))
        g = scene.grid
        for y in range(g.h):
            for x in range(g.w + 1):
                if g.v_walls[y][x]:
                    a = cam.world_to_screen(x, y)
                    b = cam.world_to_screen(x, y + 1)
                    pygame.draw.line(surface, (200, 200, 210), a, b, th)
        for y in range(g.h + 1):
            for x in range(g.w):
                if g.h_walls[y][x]:
                    a = cam.world_to_screen(x, y)
                    b = cam.world_to_screen(x + 1, y)
                    pygame.draw.line(surface, (200, 200, 210), a, b, th)

        for e in scene.entities.values():
            t = e.get("transform")
            sp = e.get("sprite2d")
            if not t or not sp:
                continue
            wx, wy = t.world_pos(scene)
            sx, sy = cam.world_to_screen(wx, wy)
            col = tuple(sp.color)
            if e.id == scene.selection:
                pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), 11, 2)
            if sp.kind == "camera":
                pygame.draw.circle(surface, col, (int(sx), int(sy)), 7)
                pygame.draw.circle(surface, (60, 20, 20), (int(sx), int(sy)), 7, 2)
                dir_len = max(12, cam.zoom * 0.5)
                ang = t.world_angle(scene)
                ex = sx + math.cos(ang) * dir_len
                ey = sy + math.sin(ang) * dir_len
                pygame.draw.line(surface, col, (sx, sy), (ex, ey), 2)
            else:
                pygame.draw.rect(surface, col,
                                 pygame.Rect(int(sx - 6), int(sy - 6), 12, 12))

        surface.set_clip(None)
