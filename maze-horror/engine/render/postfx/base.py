class PostEffect:
    """Унифицированный интерфейс пост-эффекта камеры (аналог шейдера)."""
    name = "effect"

    def from_dict(self, d):
        for k, v in d.items():
            if k == "type":
                continue
            setattr(self, k, v)
        return self

    def to_dict(self):
        return {
            "type": self.name,
            **{k: v for k, v in self.__dict__.items()
               if not k.startswith("_")},
        }

    def apply(self, surface, ctx, dt):
        return surface
