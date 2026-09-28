"""Точка входа игры.

Игра использует движок и core из maze-studio, чтобы не дублировать код.
Запускается либо из корня проекта, либо из собранного бандла (PyInstaller).
"""
import os
import sys


def _bootstrap_path():
    """Добавляет в sys.path пути к maze-studio и maze-horror.

    В режиме разработки (запуск из репозитория) — относительно __file__.
    В режиме PyInstaller — из sys._MEIPASS.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
        candidates = [
            os.path.join(base, "maze-studio"),
            os.path.join(base, "maze-horror"),
        ]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(here)
        candidates = [
            os.path.join(repo_root, "maze-studio"),
            here,
        ]
    for p in candidates:
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)


_bootstrap_path()

from game.game import Game  # noqa: E402


if __name__ == "__main__":
    level = sys.argv[1] if len(sys.argv) > 1 else "level_01"
    Game(level_name=level).run()
