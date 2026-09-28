"""Проект редактора: папка с data/ (уровни, блюпринты, эффекты, ввод).

Проект — это игра (например, maze-horror/), которая использует движок
из maze-studio/. Редактор открывает проект и работает с его data/.
Дефолты движка лежат в maze-studio/data/ и служат шаблонами.
"""
import os
import shutil

DATA_SUBDIRS = ("levels", "blueprints", "effects", "input", "prefabs")


class Project:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.data_root = os.path.join(self.root, "data")

    # ─── валидация ─────────────────────────────────────────
    def is_valid(self):
        return os.path.isdir(self.data_root)

    def ensure_layout(self):
        os.makedirs(self.data_root, exist_ok=True)
        for sub in DATA_SUBDIRS:
            os.makedirs(os.path.join(self.data_root, sub), exist_ok=True)

    # ─── пути ──────────────────────────────────────────────
    def data_dir(self, kind):
        return os.path.join(self.data_root, kind)

    def data_path(self, kind, name):
        if not name.endswith(".json"):
            name += ".json"
        return os.path.join(self.data_dir(kind), name)

    def name(self):
        return os.path.basename(self.root.rstrip(os.sep)) or self.root

    # ─── создание из шаблонов движка ───────────────────────
    @classmethod
    def create_from_templates(cls, target_root, engine_data_root):
        """Копирует дефолты движка в новый проект. Не перезаписывает
        существующие файлы, только докладывает отсутствующие."""
        p = cls(target_root)
        p.ensure_layout()
        if not os.path.isdir(engine_data_root):
            return p
        for sub in DATA_SUBDIRS:
            src = os.path.join(engine_data_root, sub)
            dst = p.data_dir(sub)
            if not os.path.isdir(src):
                continue
            os.makedirs(dst, exist_ok=True)
            for f in os.listdir(src):
                if not f.endswith(".json"):
                    continue
                s = os.path.join(src, f)
                d = os.path.join(dst, f)
                if not os.path.isfile(d):
                    shutil.copy2(s, d)
        return p
