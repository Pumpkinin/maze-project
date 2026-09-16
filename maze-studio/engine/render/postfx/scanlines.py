import numpy as np
import pygame
from .base import PostEffect


class ScanlinesEffect(PostEffect):
    name = "scanlines"
    min_alpha = 8
    max_alpha = 28
    frame_time = 1.0 / 30.0

    def __init__(self):
        self._frames = 8
        self._arrays = None
        self._idx = 0
        self._timer = 0.0

    def _ensure(self, ih):
        if self._arrays is None or self._arrays[0].shape != (ih, 1):
            self._arrays = [
                np.random.randint(self.min_alpha, self.max_alpha,
                                  (ih, 1), dtype=np.uint8)
                for _ in range(self._frames)
            ]

    def apply(self, surface, ctx, dt):
        iw, ih = surface.get_size()
        self._ensure(ih)

        self._timer += dt
        if self._timer >= self.frame_time:
            self._timer -= self.frame_time
            self._idx = (self._idx + 1) % self._frames
        scan = self._arrays[self._idx]

        rgba = np.empty((ih, iw, 4), dtype=np.uint8)
        rgba[..., 0] = 255
        rgba[..., 1] = 255
        rgba[..., 2] = 255
        rgba[..., 3] = np.broadcast_to(scan, (ih, iw))

        surf = pygame.image.frombuffer(rgba.tobytes(), (iw, ih), "RGBA")
        surface.blit(surf.convert_alpha(), (0, 0))
        return surface
