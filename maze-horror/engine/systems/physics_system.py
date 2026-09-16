from engine.systems.base import System
from engine.physics.collision import sweep_circle, aabb_vs_grid


class PhysicsSystem(System):
    name = "physics"

    def update(self, scene, dt, input=None):
        for e in list(scene.entities.values()):
            t = e.get("transform")
            c = e.get("collider")
            if not t or not c or c.is_static:
                continue

            dx = dy = 0.0
            rb = e.get("rigidbody")
            if rb:
                dx += rb.vx * dt
                dy += rb.vy * dt
                if rb.damping > 0:
                    k = max(0.0, 1.0 - rb.damping * dt)
                    rb.vx *= k
                    rb.vy *= k

            script = e.get("script")
            if script:
                delta = script.vars.get("_delta")
                if delta:
                    dx += delta[0]
                    dy += delta[1]

            ox, oy = t.world_pos(scene)

            if c.shape == "circle":
                nx, ny, hx, hy = sweep_circle(scene.grid, ox, oy, dx, dy, c.radius)
            else:
                nx, ny, hx, hy = aabb_vs_grid(
                    scene.grid, ox - c.w / 2, oy - c.h / 2,
                    c.w, c.h, dx, dy)
                nx += c.w / 2
                ny += c.h / 2

            if t.parent_id and t.parent_id in scene.entities:
                p = scene.entities[t.parent_id].get("transform")
                if p:
                    px, py = p.world_pos(scene)
                    t.x, t.y = nx - px, ny - py
                else:
                    t.x, t.y = nx, ny
            else:
                t.x, t.y = nx, ny

            if rb:
                if hx: rb.vx = 0.0
                if hy: rb.vy = 0.0
            if hx or hy:
                scene.bus.emit("collision", entity=e, hit_x=hx, hit_y=hy)
