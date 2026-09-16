from engine.systems.base import System


class InputSystem(System):
    name = "input"

    def __init__(self, input_obj):
        self.input = input_obj

    def update(self, scene, dt, input=None):
        scene.meta["input"] = self.input
