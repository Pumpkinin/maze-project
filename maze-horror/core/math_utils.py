"""Чистая математика. Никаких зависимостей от pygame/engine."""
import math


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def sign(x):
    if x > 0: return 1.0
    if x < 0: return -1.0
    return 0.0


class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x=0.0, y=0.0):
        self.x, self.y = float(x), float(y)

    def __add__(self, o): return Vec2(self.x + o.x, self.y + o.y)
    def __sub__(self, o): return Vec2(self.x - o.x, self.y - o.y)
    def __mul__(self, s): return Vec2(self.x * s, self.y * s)
    def __repr__(self):  return f"Vec2({self.x:.3f},{self.y:.3f})"
    def length(self):    return math.hypot(self.x, self.y)

    def normalize(self):
        l = self.length()
        return Vec2(self.x / l, self.y / l) if l > 1e-9 else Vec2()

    def as_tuple(self):
        return (self.x, self.y)


class AABB:
    __slots__ = ("x0", "y0", "x1", "y1")

    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1

    def intersects(self, o):
        return not (self.x1 < o.x0 or self.x0 > o.x1 or self.y1 < o.y0 or self.y0 > o.y1)
