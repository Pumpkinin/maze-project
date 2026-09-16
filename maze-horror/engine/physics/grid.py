class WallGrid:
    def __init__(self, w, h):
        self.w, self.h = int(w), int(h)
        self.v_walls = [[False] * (self.w + 1) for _ in range(self.h)]
        self.h_walls = [[False] * self.w for _ in range(self.h + 1)]
        for y in range(self.h):
            self.v_walls[y][0] = True
            self.v_walls[y][self.w] = True
        for x in range(self.w):
            self.h_walls[0][x] = True
            self.h_walls[self.h][x] = True

    def is_v_wall(self, x, y):
        if not (0 <= y < self.h):
            return True
        if x < 0 or x > self.w:
            return True
        return self.v_walls[y][x]

    def is_h_wall(self, x, y):
        if not (0 <= x < self.w):
            return True
        if y < 0 or y > self.h:
            return True
        return self.h_walls[y][x]

    def clone(self):
        g = WallGrid(self.w, self.h)
        g.v_walls = [r[:] for r in self.v_walls]
        g.h_walls = [r[:] for r in self.h_walls]
        return g
