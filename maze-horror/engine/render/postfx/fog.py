import numpy as np
import pygame
from .base import PostEffect


class FogEffect(PostEffect):
    """Белый шум тумана. Учитывает depth_buffer[x] для стен
       и вертикальный профиль для пола/потолка."""
    name = "fog"
    fog_start = 0.8
    fog_end = 12.0
    fog_max_alpha = 230
    frame_time = 1.0 / 24.0

    def __init__(self):
        self._frames = 6
        self._arrays = None
        self._idx = 0
        self._timer = 0.0

    def _ensure(self, iw, ih):
        if self._arrays is None or self._arrays[0].shape != (ih, iw):
            self._arrays = [np.random.randint(0, 256, (ih, iw), dtype=np.uint8)
                            for _ in range(self._frames)]

    def apply(self, surface, ctx, dt):
        iw, ih = surface.get_size()
        self._ensure(iw, ih)

        self._timer += dt
        if self._timer >= self.frame_time:
            self._timer -= self.frame_time
            self._idx = (self._idx + 1) % self._frames
        noise = self._arrays[self._idx]

        proj = ctx["raycaster"]
        horizon = ctx["horizon"]
        proj_dist = ctx.get("proj_dist", (proj.iw / 2.0))
        cam_h = ctx.get("camera_height", 0.5)

        # вертикальный профиль по строкам
        vert_alpha = np.zeros(ih, dtype=np.uint8)
        for y in range(ih):
            dy_pix = abs(y - horizon)
            if dy_pix < 1:
                d_est = self.fog_end
            else:
                d_est = min((proj_dist * cam_h) / dy_pix, self.fog_end)
            if d_est <= self.fog_start:
                vert_alpha[y] = 0
            elif d_est >= self.fog_end:
                vert_alpha[y] = self.fog_max_alpha
            else:
                t = (d_est - self.fog_start) / (self.fog_end - self.fog_start)
                vert_alpha[y] = int(self.fog_max_alpha * t)

        alpha_map = np.zeros((ih, iw), dtype=np.uint8)
        for x in range(iw):
            alpha_map[:, x] = vert_alpha
            wd = proj.depth_buffer[x]
            if wd <= proj.max_depth:
                line_h = int((proj.iw / 2) / max(wd, 0.001))
                top = max(0, horizon - line_h // 2)
                bot = min(ih - 1, horizon + line_h // 2)
                if wd <= self.fog_start:
                    wa = 0
                elif wd >= self.fog_end:
                    wa = self.fog_max_alpha
                else:
                    t = (wd - self.fog_start) / (self.fog_end - self.fog_start)
                    wa = int(self.fog_max_alpha * t)
                if top <= bot:
                    alpha_map[top:bot + 1, x] = wa

        rgba = np.empty((ih, iw, 4), dtype=np.uint8)
        rgba[..., 0] = noise
        rgba[..., 1] = noise
        rgba[..., 2] = noise
        rgba[..., 3] = alpha_map

        surf = pygame.image.frombuffer(rgba.tobytes(), (iw, ih), "RGBA")
        surface.blit(surf.convert_alpha(), (0, 0))
        return surface
