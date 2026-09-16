import math


def cast_ray(grid, ox, oy, angle, max_depth):
    """DDA-луч. Возвращает (distance, side, map_x, map_y)."""
    sin_a, cos_a = math.sin(angle), math.cos(angle)
    delta_x = abs(1 / cos_a) if cos_a else float('inf')
    delta_y = abs(1 / sin_a) if sin_a else float('inf')

    map_x, map_y = int(math.floor(ox)), int(math.floor(oy))

    if cos_a < 0:
        step_x, side_x = -1, (ox - map_x) * delta_x
    else:
        step_x, side_x = 1, (map_x + 1.0 - ox) * delta_x
    if sin_a < 0:
        step_y, side_y = -1, (oy - map_y) * delta_y
    else:
        step_y, side_y = 1, (map_y + 1.0 - oy) * delta_y

    side = -1
    while True:
        if side_x < side_y:
            side_x += delta_x
            map_x += step_x
            side = 0
        else:
            side_y += delta_y
            map_y += step_y
            side = 1

        if side == 0:
            wx = map_x if step_x == 1 else map_x + 1
            if not (0 <= map_y < grid.h) or not (0 <= wx <= grid.w):
                return max_depth + 1, -1, map_x, map_y
            if grid.v_walls[map_y][wx]:
                break
        else:
            wy = map_y if step_y == 1 else map_y + 1
            if not (0 <= wy <= grid.h) or not (0 <= map_x < grid.w):
                return max_depth + 1, -1, map_x, map_y
            if grid.h_walls[wy][map_x]:
                break

        d = abs((map_x - ox + (1 - step_x) / 2) / cos_a) if side == 0 \
            else abs((map_y - oy + (1 - step_y) / 2) / sin_a)
        if d > max_depth:
            return max_depth + 1, -1, map_x, map_y

    perp = (map_x - ox + (1 - step_x) / 2) / cos_a if side == 0 \
        else (map_y - oy + (1 - step_y) / 2) / sin_a
    return max(perp, 0.001), side, map_x, map_y
