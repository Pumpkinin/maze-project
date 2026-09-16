import math
import numpy as np
import pygame

MAX_DEPTH = 12.0
FLOOR_TILE_SIZE = 0.5
FLOOR_LIGHT = 190
FLOOR_DARK = 130
FLOOR_SHADE_MAX = 0.85


class Raycaster:
    """Геометрия стен/пола. Пост-эффекты — отдельно, в postfx/."""

    def __init__(self, iw, ih, max_depth=MAX_DEPTH):
        self.iw, self.ih = int(iw), int(ih)
        self.max_depth = float(max_depth)
        self.frame = pygame.Surface((self.iw, self.ih))
        self.depth_buffer = [self.max_depth + 1.0] * self.iw
        self.side_buffer = [-1] * self.iw
        self.wall_top = [0] * self.iw
        self.wall_bot = [0] * self.iw

    def render(self, grid, px, py, angle, fov_deg, pitch, camera_height,
               dt=0.0):
        iw, ih = self.iw, self.ih
        self.frame.fill((0, 0, 0))

        tan_half = math.tan(math.radians(fov_deg / 2.0))
        proj_dist = (iw / 2.0) / tan_half
        horizon = int(ih // 2 + pitch * proj_dist)

        self._draw_floor(px, py, angle, tan_half, proj_dist,
                         horizon, camera_height)
        self._draw_walls(grid, px, py, angle, tan_half, proj_dist,
                         horizon, camera_height)
        return self.frame

    # ─── пол ─────────────────────────────────────────────────
    def _draw_floor(self, px, py, angle, tan_half, proj_dist,
                    horizon, camera_height):
        iw, ih = self.iw, self.ih
        if horizon >= ih - 1:
            return

        xs = np.arange(iw, dtype=np.float32)
        cam_x = 2.0 * xs / iw - 1.0
        ray_off = np.arctan(cam_x * tan_half).astype(np.float32)
        cos_r = np.cos(angle + ray_off).astype(np.float32)
        sin_r = np.sin(angle + ray_off).astype(np.float32)

        floor_rgba = np.zeros((ih, iw, 4), dtype=np.uint8)
        for y in range(max(0, horizon + 1), ih):
            dy = y - horizon
            t = (proj_dist * camera_height) / dy
            if t > self.max_depth:
                continue
            wx = px + cos_r * t
            wy = py + sin_r * t
            cx = np.floor(wx / FLOOR_TILE_SIZE).astype(np.int32)
            cy = np.floor(wy / FLOOR_TILE_SIZE).astype(np.int32)
            checker = (cx + cy) & 1
            base = np.where(checker == 0, FLOOR_LIGHT, FLOOR_DARK).astype(np.float32)
            factor = 1.0 - (1.0 - FLOOR_SHADE_MAX) * min(t / self.max_depth, 1.0)
            shade = (base * factor).astype(np.uint8)
            floor_rgba[y, :, 0] = shade
            floor_rgba[y, :, 1] = shade
            floor_rgba[y, :, 2] = shade
            floor_rgba[y, :, 3] = 255

        surf = pygame.image.frombuffer(floor_rgba.tobytes(), (iw, ih), "RGBA")
        self.frame.blit(surf.convert_alpha(), (0, 0))

    # ─── стены ───────────────────────────────────────────────
    def _draw_walls(self, grid, px, py, angle, tan_half, proj_dist,
                    horizon, camera_height):
        iw, ih = self.iw, self.ih
        self.depth_buffer = [self.max_depth + 1.0] * iw
        self.side_buffer = [-1] * iw
        self.wall_top = [0] * iw
        self.wall_bot = [0] * iw

        for x in range(iw):
            cam_x = 2.0 * x / iw - 1.0
            ray_angle = angle + math.atan(cam_x * tan_half)
            sin_a, cos_a = math.sin(ray_angle), math.cos(ray_angle)
            delta_x = abs(1 / cos_a) if cos_a else float('inf')
            delta_y = abs(1 / sin_a) if sin_a else float('inf')

            mx, my = int(math.floor(px)), int(math.floor(py))
            if cos_a < 0:
                step_x, side_x = -1, (px - mx) * delta_x
            else:
                step_x, side_x = 1, (mx + 1.0 - px) * delta_x
            if sin_a < 0:
                step_y, side_y = -1, (py - my) * delta_y
            else:
                step_y, side_y = 1, (my + 1.0 - py) * delta_y

            hit = False
            side = 0
            d = self.max_depth + 1.0
            while not hit:
                if side_x < side_y:
                    side_x += delta_x
                    mx += step_x
                    side = 0
                else:
                    side_y += delta_y
                    my += step_y
                    side = 1

                if side == 0:
                    wx = mx if step_x == 1 else mx + 1
                    if not (0 <= my < grid.h) or not (0 <= wx <= grid.w):
                        hit = True
                    elif grid.v_walls[my][wx]:
                        hit = True
                else:
                    wy = my if step_y == 1 else my + 1
                    if not (0 <= wy <= grid.h) or not (0 <= mx < grid.w):
                        hit = True
                    elif grid.h_walls[wy][mx]:
                        hit = True

                if side == 0:
                    d = abs((mx - px + (1 - step_x) / 2) / cos_a) if cos_a else float('inf')
                else:
                    d = abs((my - py + (1 - step_y) / 2) / sin_a) if sin_a else float('inf')
                if d > self.max_depth:
                    hit = True
                    d = self.max_depth + 1.0

            if d > self.max_depth:
                continue

            self.depth_buffer[x] = d
            self.side_buffer[x] = side

            line_h = int(proj_dist / max(d, 0.001))
            base = 200 if side == 0 else 150
            factor = max(0.0, 1.0 - d / self.max_depth)
            shade = max(0, min(255, int(base * factor)))

            top = horizon - line_h // 2
            bot = horizon + line_h // 2
            self.wall_top[x] = top
            self.wall_bot[x] = bot

            y0 = max(0, top)
            y1 = min(ih - 1, bot)
            if y0 > y1:
                continue
            for y in range(y0, y1 + 1):
                self.frame.set_at((x, y), (shade, shade, shade))
