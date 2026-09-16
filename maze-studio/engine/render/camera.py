import math
from engine.render.raycaster import Raycaster
from engine.render.postfx import build_stack


class Camera3D:
    """Собирает Raycaster + стек PostEffect для конкретной камеры."""

    def __init__(self, camera_component, effects_preset):
        self.cam = camera_component
        self.raycaster = Raycaster(camera_component.internal_w,
                                   camera_component.internal_h)
        self.effects = build_stack(effects_preset)
        self.pitch = 0.0
        self.tan_half = math.tan(math.radians(camera_component.fov / 2.0))
        self.proj_dist = (self.raycaster.iw / 2.0) / self.tan_half

    def set_pitch(self, p):
        pmin = math.tan(math.radians(self.cam.pitch_min))
        pmax = math.tan(math.radians(self.cam.pitch_max))
        self.pitch = max(pmin, min(pmax, p))
        return self.pitch

    def _horizon(self):
        return int(self.raycaster.ih // 2 + self.pitch * self.proj_dist)

    def render(self, scene, entity, dt):
        t = entity.get("transform")
        wx, wy = t.world_pos(scene)
        ang = t.world_angle(scene)

        frame = self.raycaster.render(
            scene.grid, wx, wy, ang,
            fov_deg=self.cam.fov,
            pitch=self.pitch,
            camera_height=self.cam.height,
            dt=dt,
        )

        wish_speed = 0.0
        if entity.has("script"):
            wish_speed = entity.get("script").vars.get("_wish_speed", 0.0)

        ctx = {
            "camera": self.cam,
            "scene": scene,
            "entity": entity,
            "raycaster": self.raycaster,
            "wish_speed": wish_speed,
            "horizon": self._horizon(),
            # для fog/darken: те же параметры, что в оригинальном raycaster
            "proj_dist": self.proj_dist,
            "camera_height": self.cam.height,
        }

        for fx in self.effects:
            frame = fx.apply(frame, ctx, dt)
        return frame
