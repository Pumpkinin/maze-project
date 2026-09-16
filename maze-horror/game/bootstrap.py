"""Точка расширения игры: регистрация кастомных узлов блюпринтов,
подписка на события движка и т.п.

Пример:

    from engine.blueprints.registry import register
    from engine.blueprints.nodes_builtin import Node

    @register
    class PlaySound(Node):
        type_name = "PlaySound"
        inputs = {"in": "flow"}
        outputs = {"out": "flow"}
        def evaluate(self, ctx, in_vals):
            if in_vals.get("in"):
                # pygame.mixer.Sound(...).play()
                pass
            return {"out": True}
"""
