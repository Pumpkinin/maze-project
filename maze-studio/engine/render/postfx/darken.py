import numpy as np
import pygame
from .base import PostEffect


class DarkenEffect(PostEffect):
    """Затемнение по дальности. Стены — по depth_buffer[x],
       пол/потолок — по вертикальному профилю."""
    name = "darken"
    darken_start = 3.0
    darken_end = 30.0
    darken_max = 1.0

    def apply(self, surface, ctx, dt):
        if self.darken_max <= 0.0:
            return surface

        iw, ih = surface.get_size()
        proj = ctx["raycaster"]
        horizon = ctx["horizon"]
        proj_dist = ctx.get("proj_dist", (proj.iw / 2.0))
        cam_h = ctx.get("camera_height", 0.5)

        vert_alpha = np.zeros(ih, dtype=np.uint8)
        for y in range(ih):
            dy_pix = abs(y - horizon)
            if dy_pix < 1:
                d_est = self.darken_end
            else:
                d_est = min((proj_dist * cam_h) / dy_pix, self.darken_end)
            if d_est <= self.darken_start:
                vert_alpha[y] = 0
            elif d_est >= self.darken_end:
                vert_alpha[y] = int(255 * self.darken_max)
            else:
                t = (d_est - self.darken_start) / (self.darken_end - self.darken_start)
                vert_alpha[y] = int(255 * self.darken_max * t)

        alpha_map = np.zeros((ih, iw), dtype=np.uint8)
        for x in range(iw):
            alpha_map[:, x] = vert_alpha
            wd = proj.depth_buffer[x]
            if wd <= proj.max_depth:
                line_h = int((proj.iw / 2) / max(wd, 0.001))
                top = max(0, horizon - line_h // 2)
                bot = min(ih - 1, horizon + line_h // 2)
                if wd <= self.darken_start:
                    a = 0
                elif wd >= self.darken_end:
                    a = int(255 * self.darken_max)
                else:
                    t = (wd - self.darken_start) / (self.darken_end - self.darken_start)
                    a = int(255 * self.darken_max * t)
                if top <= bot:
                    alpha_map[top:bot + 1, x] = a

        rgba = np.zeros((ih, iw, 4), dtype=np.uint8)
        rgba[..., 3] = alpha_map
        surf = pygame.image.frombuffer(rgba.tobytes(), (iw, ih), "RGBA")
        surface.blit(surf.convert_alpha(), (0, 0))
        return surface
