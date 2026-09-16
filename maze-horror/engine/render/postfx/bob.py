import math
import pygame
from .base import PostEffect


class HeadBobEffect(PostEffect):
    name = "bob"
    freq = 9.0
    amp_x = 1.0
    amp_y = 3.0
    speed_threshold = 0.05
    ref_speed = 2.5

    def __init__(self):
        self._phase = 0.0
        self._bx = 0.0
        self._by = 0.0
        # Переиспользуемый surface для сдвига. Создаётся в apply()
        # при первом вызове или при смене размера кадра.
        self._shifted = None
        self._shifted_size = (0, 0)

    def update(self, dt, wish_speed):
        moving = wish_speed > self.speed_threshold
        if moving:
            self._phase += self.freq * dt * (wish_speed / max(0.01, self.ref_speed))
        rx = math.sin(self._phase) * self.amp_x
        ry = abs(math.sin(self._phase)) * self.amp_y
        tgt = 1.0 if moving else 0.0
        l = 1.0 - math.exp(-8.0 * dt)
        self._bx += (rx * tgt - self._bx) * l
        self._by += (ry * tgt - self._by) * l

    def apply(self, surface, ctx, dt):
        wish = ctx.get("wish_speed", 0.0)
        self.update(dt, wish)
        dx, dy = int(round(self._bx)), int(round(self._by))
        if dx == 0 and dy == 0:
            return surface
        iw, ih = surface.get_size()
        if self._shifted is None or self._shifted_size != (iw, ih):
            self._shifted = pygame.Surface((iw, ih), pygame.SRCALPHA)
            self._shifted_size = (iw, ih)
        self._shifted.fill((0, 0, 0, 0))
        self._shifted.blit(surface, (dx, dy))
        return self._shifted
