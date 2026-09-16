import math
import numpy as np
import pygame
from .base import PostEffect


class VignetteEffect(PostEffect):
    name = "vignette"
    strength = 110

    def __init__(self):
        self._cache = None
        self._size = None

    def _build(self, iw, ih):
        cx, cy = iw / 2.0, ih / 2.0
        max_r = math.hypot(cx, cy)
        yy, xx = np.mgrid[0:ih, 0:iw]
        r = np.hypot(xx - cx, yy - cy) / max_r
        a = np.clip((r - 0.35) / 0.65, 0.0, 1.0) ** 1.6 * self.strength
        rgba = np.empty((ih, iw, 4), dtype=np.uint8)
        rgba[..., 0] = 0
        rgba[..., 1] = 0
        rgba[..., 2] = 0
        rgba[..., 3] = a.astype(np.uint8)
        return pygame.image.frombuffer(rgba.tobytes(), (iw, ih), "RGBA").convert_alpha()

    def apply(self, surface, ctx, dt):
        iw, ih = surface.get_size()
        if self._size != (iw, ih):
            self._size = (iw, ih)
            self._cache = self._build(iw, ih)
        surface.blit(self._cache, (0, 0))
        return surface
