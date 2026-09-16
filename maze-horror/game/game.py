import os
import sys
import pygame

from core.serialize import load_json
from engine.ecs.scene import Scene
from engine.input.input import Input
from engine.render.camera import Camera3D
from engine.render.postfx_loader import find_preset
from engine.systems.physics_system import PhysicsSystem
from engine.systems.script_system import ScriptSystem
from engine.systems.input_system import InputSystem

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Game:
    def __init__(self, level_name="level_01", fullscreen=False):
        pygame.init()
        flags = pygame.RESIZABLE | pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((1280, 720), flags)
        pygame.display.set_caption("MazeHorror")
        self.clock = pygame.time.Clock()
        self.running = True

        data = load_json(os.path.join(ROOT, "data", "levels", level_name + ".json"))
        self.scene = Scene.from_dict(data)

        try:
            self.input = Input.load(os.path.join(ROOT, "data", "input", "default.json"))
        except Exception:
            self.input = Input()

        self.scene.add_system(InputSystem(self.input))
        self.scene.add_system(ScriptSystem(self._load_bp))
        self.scene.add_system(PhysicsSystem())

        self.camera = None
        self.camera_entity = None
        for e in self.scene.entities.values():
            if e.has("camera"):
                preset = find_preset(ROOT, e.get("camera").effects_preset)
                self.camera = Camera3D(e.get("camera"), preset)
                self.camera_entity = e
                break

        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        pygame.mouse.get_rel()
        self.input.push_context("gameplay")

    def _load_bp(self, name):
        p = os.path.join(ROOT, "data", "blueprints", name + ".json")
        if not os.path.isfile(p):
            return None
        try:
            return load_json(p)
        except Exception as e:
            print(f"[bp] {name}: {e}")
            return None

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            events = pygame.event.get()
            self.input.begin_frame(events)
            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.running = False
                if e.type == pygame.MOUSEMOTION and self.camera and self.camera_entity:
                    t = self.camera_entity.get("transform")
                    if t:
                        t.angle += e.rel[0] * 0.003
                    self.camera.set_pitch(self.camera.pitch - e.rel[1] * 0.002)

            self.scene.update(dt, self.input)

            if self.camera and self.camera_entity:
                frame = self.camera.render(self.scene, self.camera_entity, dt)
                scaled = pygame.transform.scale(frame, self.screen.get_size())
                self.screen.blit(scaled, (0, 0))
            pygame.display.flip()
        pygame.quit()
        sys.exit()
