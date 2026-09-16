from editor.tools.base import Tool
from editor.history import AddEntity, Command
from engine.ecs.entity import Entity
from engine.ecs.components import (Transform, Collider, Camera,
                                   Sprite2D, Script, Name)


class SpawnPlayerTool(Tool):
    name = "spawn"
    label = "Player"

    def apply(self, scene, wx, wy, cx, cy, history=None):
        e = Entity(name="Player")
        e.add(Name("Player"))
        e.add(Transform(x=wx, y=wy))
        e.add(Collider(shape="circle", radius=0.2))
        e.add(Camera(fov=110, effects_preset="default"))
        e.add(Sprite2D(kind="camera", color=(240, 80, 80)))
        e.add(Script(blueprint="player_controller", vars={"speed": 2.5}))
        cmd = AddEntity(scene, e)
        (history.push if history else cmd.execute)(cmd)
        scene.selection = e.id


class PlaceExitTool(Tool):
    name = "exit"
    label = "Exit"

    class _SetExit(Command):
        def __init__(self, scene, new_cell):
            self.scene = scene
            self.new_cell = new_cell
            self.prev_cell = None

        def execute(self):
            self.prev_cell = self.scene.meta.get("exit_cell")
            self.scene.meta["exit_cell"] = self.new_cell

        def undo(self):
            self.scene.meta["exit_cell"] = self.prev_cell

    def apply(self, scene, wx, wy, cx, cy, history=None):
        if not (0 <= cx < scene.w and 0 <= cy < scene.h):
            return
        cmd = self._SetExit(scene, (cx, cy))
        (history.push if history else cmd.execute)(cmd)
