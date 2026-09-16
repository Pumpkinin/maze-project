import math


def sweep_circle(grid, x, y, dx, dy, radius):
    """Движение круга с раздельным разрешением по осям.
       Возвращает (new_x, new_y, hit_x, hit_y)."""
    hit_x = hit_y = False

    new_x = x + dx
    cx, cy = int(math.floor(x)), int(math.floor(y))
    if dx > 0:
        wx = cx + 1
        if grid.is_v_wall(wx, cy) and new_x + radius > wx:
            new_x = wx - radius
            hit_x = True
    elif dx < 0:
        wx = cx
        if grid.is_v_wall(wx, cy) and new_x - radius < wx:
            new_x = wx + radius
            hit_x = True

    new_y = y + dy
    cx, cy = int(math.floor(new_x)), int(math.floor(y))
    if dy > 0:
        wy = cy + 1
        if grid.is_h_wall(cx, wy) and new_y + radius > wy:
            new_y = wy - radius
            hit_y = True
    elif dy < 0:
        wy = cy
        if grid.is_h_wall(cx, wy) and new_y - radius < wy:
            new_y = wy + radius
            hit_y = True

    return new_x, new_y, hit_x, hit_y


def aabb_vs_grid(grid, x, y, w, h, dx, dy):
    """Простая AABB-коллизия со сеткой. Возвращает (nx, ny, hx, hy)."""
    nx, ny = x + dx, y + dy
    hit_x = hit_y = False
    # по X
    cell_y0 = int(math.floor(y))
    cell_y1 = int(math.floor(y + h - 1e-6))
    if dx > 0:
        cell_x = int(math.floor(nx + w))
        for cy in range(cell_y0, cell_y1 + 1):
            if grid.is_v_wall(cell_x, cy):
                nx = cell_x - w
                hit_x = True
                break
    elif dx < 0:
        cell_x = int(math.floor(nx))
        for cy in range(cell_y0, cell_y1 + 1):
            if grid.is_v_wall(cell_x, cy):
                nx = cell_x + 1.0
                hit_x = True
                break
    # по Y
    cell_x0 = int(math.floor(nx))
    cell_x1 = int(math.floor(nx + w - 1e-6))
    if dy > 0:
        cell_y = int(math.floor(ny + h))
        for cx in range(cell_x0, cell_x1 + 1):
            if grid.is_h_wall(cx, cell_y):
                ny = cell_y - h
                hit_y = True
                break
    elif dy < 0:
        cell_y = int(math.floor(ny))
        for cx in range(cell_x0, cell_x1 + 1):
            if grid.is_h_wall(cx, cell_y):
                ny = cell_y + 1.0
                hit_y = True
                break
    return nx, ny, hit_x, hit_y
