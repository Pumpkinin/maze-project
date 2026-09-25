#!/usr/bin/env bash
# apply_session_1.sh
# Сессия 1: убираем дублирование ядра, добавляем окно компиляции.
set -euo pipefail

# ─── 0. Проверки ─────────────────────────────────────────────
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -d ".git" ]; then
    echo "✗ Это не git-репозиторий. Запусти скрипт из корня проекта."
    exit 1
fi

if [ ! -d "maze-studio" ] || [ ! -d "maze-horror" ]; then
    echo "✗ Не найдены maze-studio/ или maze-horror/. Проверь путь."
    exit 1
fi

BRANCH="session-1"

echo "=== Сессия 1: рефакторинг структуры проекта ==="

# ─── 1. Убедиться, что рабочее дерево чистое ─────────────────
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "⚠ Есть незакоммиченные изменения."
    read -p "Закоммитить их как 'wip before session-1'? [y/N] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        git add -A
        git commit -m "wip before session-1"
    else
        echo "✗ Прерываю, чтобы не потерять изменения."
        exit 1
    fi
fi

# ─── 2. Создать/переключиться на ветку session-1 ─────────────
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "→ Ветка $BRANCH уже существует, переключаюсь."
    git checkout "$BRANCH"
else
    echo "→ Создаю ветку $BRANCH"
    git checkout -b "$BRANCH"
fi

# ─── 3. Удалить дублирующее ядро из maze-horror ──────────────
echo "→ Удаляю maze-horror/engine и maze-horror/core (дубликаты)"
git rm -r --quiet maze-horror/engine 2>/dev/null || rm -rf maze-horror/engine
git rm -r --quiet maze-horror/core   2>/dev/null || rm -rf maze-horror/core

# ─── 4. Переписать maze-horror/main.py ───────────────────────
echo "→ Обновляю maze-horror/main.py"
cat > maze-horror/main.py << 'PYEOF'
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
PYEOF

# ─── 5. Обновить .gitignore ──────────────────────────────────
echo "→ Обновляю .gitignore"
cat > .gitignore << 'GIEOF'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
dist/
*.spec
*.egg-info/
.venv/
venv/
env/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Локальные файлы
apply_session_1.sh
raycast_game.txt
*.bak
*.zip
*.log
GIEOF

# ─── 6. Панель компиляции (build_panel.py) ───────────────────
echo "→ Создаю maze-studio/editor/panels/build_panel.py"
cat > maze-studio/editor/panels/build_panel.py << 'PYEOF'
"""Панель компиляции игры в standalone-сборку через PyInstaller.

Определяет ОС разработчика и собирает бандл под неё.
"""
import os
import platform
import shutil
import subprocess
import sys
import threading

import pygame

from ui import skin


class BuildPanel:
    """Окно компиляции. Открывается по кнопке 'Build' в тулбаре (или F6)."""

    def __init__(self, root):
        self.root = root
        self.visible = False
        self.rect = pygame.Rect(0, 0, 560, 320)
        self.log = []
        self.running = False
        self._thread = None
        self.status = "Готово к сборке"

    # ─── публичное API ──────────────────────────────────────
    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self._recenter()
            self._detect_env()

    def _recenter(self):
        info = pygame.display.Info()
        self.rect.center = (info.current_w // 2, info.current_h // 2)

    def _detect_env(self):
        system = platform.system()
        self.log = [
            f"ОС: {system} ({platform.release()})",
            f"Python: {sys.version.split()[0]}",
            f"PyInstaller: {'найден' if shutil.which('pyinstaller') else 'НЕ найден'}",
            "",
        ]
        if not shutil.which("pyinstaller"):
            self.status = "PyInstaller не установлен: pip install pyinstaller"
        else:
            self.status = "Готово к сборке"

    # ─── сборка ─────────────────────────────────────────────
    def start_build(self):
        if self.running:
            return
        if not shutil.which("pyinstaller"):
            self._log("✗ pyinstaller не найден. Установи: pip install pyinstaller")
            return
        self.running = True
        self._log("→ Запуск сборки...")
        self.status = "Сборка..."
        self._thread = threading.Thread(target=self._build_worker, daemon=True)
        self._thread.start()

    def _build_worker(self):
        try:
            studio = os.path.join(self.root, "maze-studio")
            horror = os.path.join(self.root, "maze-horror")
            entry = os.path.join(horror, "main.py")
            if not os.path.isfile(entry):
                self._log("✗ Не найден maze-horror/main.py")
                return

            sep = ";" if platform.system() == "Windows" else ":"

            cmd = [
                "pyinstaller",
                "--noconfirm",
                "--clean",
                "--windowed",
                "--name", "MazeHorror",
                "--distpath", os.path.join(horror, "dist"),
                "--workpath", os.path.join(horror, "build"),
                "--specpath", os.path.join(horror, "build"),
                "--add-data", f"{os.path.join(studio, 'engine')}{sep}engine",
                "--add-data", f"{os.path.join(studio, 'core')}{sep}core",
                "--add-data", f"{os.path.join(horror, 'data')}{sep}data",
                "--add-data", f"{os.path.join(horror, 'game')}{sep}game",
                "--paths", studio,
                "--paths", horror,
                entry,
            ]

            self._log("$ " + " ".join(cmd))
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                self._log(line.rstrip())
            proc.wait()
            if proc.returncode == 0:
                out = os.path.join(horror, "dist", "MazeHorror")
                self._log(f"✓ Готово: {out}")
                self.status = "Сборка завершена"
            else:
                self._log(f"✗ Ошибка, код {proc.returncode}")
                self.status = "Ошибка сборки"
        except Exception as e:
            self._log(f"✗ Исключение: {e}")
            self.status = "Ошибка сборки"
        finally:
            self.running = False

    def _log(self, line):
        self.log.append(line)
        if len(self.log) > 200:
            self.log = self.log[-200:]

    # ─── обработка событий (вызывается из EditorApp.handle_events) ──
    def handle_event(self, e):
        """Возвращает True, если событие поглощено панелью."""
        if not self.visible:
            return False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.visible = False
            return True
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.on_click(e.pos):
                return True
        return False

    def on_click(self, pos):
        """Обработка клика. Возвращает True, если клик поглощён."""
        if not self.visible:
            return False
        btn_w, btn_h = 120, 28
        build_rect = pygame.Rect(self.rect.right - 270,
                                 self.rect.bottom - 40, btn_w, btn_h)
        close_rect = pygame.Rect(self.rect.right - 140,
                                 self.rect.bottom - 40, btn_w, btn_h)
        if build_rect.collidepoint(pos) and not self.running:
            self.start_build()
            return True
        if close_rect.collidepoint(pos):
            self.visible = False
            return True
        if self.rect.collidepoint(pos):
            return True
        return False

    def _close(self):
        self.visible = False

    # ─── отрисовка ──────────────────────────────────────────
    def draw(self, surface, ui):
        if not self.visible:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (45, 45, 52), self.rect)
        pygame.draw.rect(surface, skin.ACCENT, self.rect, 2)

        title = ui.skin.render("Компиляция игры", skin.TEXT, bold=True)
        surface.blit(title, (self.rect.x + 14, self.rect.y + 10))

        status = ui.skin.render(self.status, skin.TEXT_DIM)
        surface.blit(status, (self.rect.x + 14, self.rect.y + 32))

        # лог
        log_rect = pygame.Rect(self.rect.x + 12, self.rect.y + 56,
                               self.rect.w - 24, self.rect.h - 110)
        pygame.draw.rect(surface, (28, 28, 34), log_rect)
        pygame.draw.rect(surface, skin.PANEL_BORDER, log_rect, 1)
        y = log_rect.y + 4
        for line in self.log[-14:]:
            t = ui.skin.render(line[:90], skin.TEXT)
            surface.blit(t, (log_rect.x + 6, y))
            y += 14
            if y > log_rect.bottom - 14:
                break

        # кнопки
        btn_w, btn_h = 120, 28
        build_rect = pygame.Rect(self.rect.right - 270,
                                 self.rect.bottom - 40, btn_w, btn_h)
        close_rect = pygame.Rect(self.rect.right - 140,
                                 self.rect.bottom - 40, btn_w, btn_h)

        hover_build = build_rect.collidepoint(ui.mouse_pos)
        hover_close = close_rect.collidepoint(ui.mouse_pos)

        color_build = (skin.ACCENT_HOVER if (hover_build and not self.running)
                       else (skin.ACCENT if not self.running else (70, 70, 78)))
        pygame.draw.rect(surface, color_build, build_rect, border_radius=4)
        pygame.draw.rect(surface, skin.PANEL_BORDER, build_rect, 1, border_radius=4)
        label = "Сборка..." if self.running else "Собрать"
        t = ui.skin.render(label, skin.TEXT)
        surface.blit(t, t.get_rect(center=build_rect.center))

        pygame.draw.rect(surface, skin.ACCENT if hover_close else (60, 60, 66),
                         close_rect, border_radius=4)
        pygame.draw.rect(surface, skin.PANEL_BORDER, close_rect, 1, border_radius=4)
        t2 = ui.skin.render("Закрыть", skin.TEXT)
        surface.blit(t2, t2.get_rect(center=close_rect.center))
PYEOF

# ─── 7. Патчим editor/app.py ─────────────────────────────────
echo "→ Встраиваю BuildPanel в editor/app.py"
python3 - << 'PYEOF'
import pathlib

p = pathlib.Path("maze-studio/editor/app.py")
src = p.read_text(encoding="utf-8")

# 7.1 импорт
if "from editor.panels.build_panel import BuildPanel" not in src:
    src = src.replace(
        "from editor.file_dialog import FileDialog",
        "from editor.file_dialog import FileDialog\n"
        "from editor.panels.build_panel import BuildPanel",
    )

# 7.2 создание build_panel ДО Toolbar (иначе AttributeError)
#     сначала убираем возможное старое создание после dialog
src = src.replace(
    "        self.dialog = FileDialog()\n"
    "        self.build_panel = BuildPanel(ROOT)\n",
    "        self.dialog = FileDialog()\n",
)
src = src.replace(
    "        self.dialog = FileDialog()\n"
    "        self.build_panel = BuildPanel(ROOT)\n",
    "        self.dialog = FileDialog()\n",
)
#     теперь вставляем перед Toolbar
if "self.build_panel = BuildPanel(ROOT)" not in src:
    src = src.replace(
        "        # Панели\n"
        "        self.toolbar = Toolbar(self.rect_toolbar, self)\n",
        "        # Панели\n"
        "        self.build_panel = BuildPanel(ROOT)\n"
        "        self.toolbar = Toolbar(self.rect_toolbar, self)\n",
    )

# 7.3 F6 — открыть панель сборки
if "pygame.K_F6" not in src:
    src = src.replace(
        "                if e.key == pygame.K_F5:\n"
        "                    self.toggle_preview()\n",
        "                if e.key == pygame.K_F5:\n"
        "                    self.toggle_preview()\n"
        "                if e.key == pygame.K_F6:\n"
        "                    self.build_panel.toggle()\n",
    )

# 7.4 обработка событий панели в начале цикла for e in events
needle = "        for e in events:\n            if e.type == pygame.QUIT:\n"
repl = ("        for e in events:\n"
        "            if self.build_panel.handle_event(e):\n"
        "                continue\n"
        "            if e.type == pygame.QUIT:\n")
if "self.build_panel.handle_event(e)" not in src and needle in src:
    src = src.replace(needle, repl, 1)

# 7.5 отрисовка панели поверх всего
if "self.build_panel.draw(self.screen, self.ui)" not in src:
    src = src.replace(
        "        pygame.display.flip()\n\n"
        "    def _save_blueprint",
        "        self.build_panel.draw(self.screen, self.ui)\n"
        "        pygame.display.flip()\n\n"
        "    def _save_blueprint",
    )

p.write_text(src, encoding="utf-8")
print("  ✓ app.py обновлён")
PYEOF

# ─── 8. Кнопка Build в тулбаре ───────────────────────────────
echo "→ Добавляю кнопку Build в тулбар"
python3 - << 'PYEOF'
import pathlib

p = pathlib.Path("maze-studio/editor/panels/toolbar.py")
src = p.read_text(encoding="utf-8")

if 'add("Build"' not in src:
    src = src.replace(
        '        add("Play", self.app.toggle_preview)\n',
        '        add("Play", self.app.toggle_preview)\n'
        '        x += 10\n'
        '        add("Build", self.app.build_panel.toggle)\n',
    )
    p.write_text(src, encoding="utf-8")
    print("  ✓ toolbar.py обновлён")
else:
    print("  • кнопка Build уже есть")
PYEOF

# ─── 9. Обновить maze-horror/run_game.sh ─────────────────────
echo "→ Обновляю maze-horror/run_game.sh"
cat > maze-horror/run_game.sh << 'SHEOF'
#!/usr/bin/env bash
# Запуск игры из корня репозитория (использует движок из maze-studio).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/maze-horror"
python3 main.py "${1:-level_01}"
SHEOF
chmod +x maze-horror/run_game.sh

# ─── 10. Удалить sync.sh (больше не нужен) ───────────────────
if [ -f "sync.sh" ]; then
    echo "→ Удаляю sync.sh (дублирование больше не нужно)"
    git rm --quiet sync.sh 2>/dev/null || rm -f sync.sh
fi

# ─── 11. Подчистить пустые папки и __pycache__ ───────────────
echo "→ Чищу пустые папки и __pycache__"
find maze-horror -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find maze-horror -type d -empty -delete 2>/dev/null || true

# ─── 12. Коммит ──────────────────────────────────────────────
echo "→ Коммичу изменения"
git add -A
git commit -m "session-1: убрано дублирование ядра, добавлена сборка через редактор

- maze-horror теперь использует engine/ и core/ из maze-studio
- удалены maze-horror/engine и maze-horror/core
- main.py игры настраивает sys.path под dev и PyInstaller
- в редактор добавлена панель компиляции (F6 / кнопка Build)
- сборка под текущую ОС через PyInstaller
- BuildPanel создаётся до Toolbar (иначе AttributeError)
- кнопки панели обрабатываются в handle_events, а не в draw
- обновлён .gitignore
- удалён sync.sh"

# ─── 13. Push ────────────────────────────────────────────────
echo "→ Пушу ветку $BRANCH в origin"
git push -u origin "$BRANCH"

echo ""
echo "=== Готово ==="
echo "Ветка: $BRANCH"
echo "Открыть PR: https://github.com/Pumpkinin/maze-project/pull/new/$BRANCH"
