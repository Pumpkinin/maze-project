"""Панель компиляции игры в standalone-сборку через PyInstaller.

Собирает ТЕКУЩИЙ проект (project_root), используя движок из engine_root
(maze-studio/). Перед сборкой чистит __pycache__, чтобы PyInstaller
не тянул устаревшие .pyc. Лог пишется в <project>/build/last_build.log.
"""
import os
import platform
import shutil
import subprocess
import sys
import threading

import pygame

from ui import skin


def _clean_pycache(root):
    """Удаляет все __pycache__ и *.pyc под root. Возвращает число удалённых."""
    removed = 0
    for dirpath, dirnames, filenames in os.walk(root):
        if "__pycache__" in dirnames:
            d = os.path.join(dirpath, "__pycache__")
            try:
                shutil.rmtree(d)
                removed += 1
            except Exception:
                pass
            dirnames.remove("__pycache__")
        for f in filenames:
            if f.endswith((".pyc", ".pyo")):
                try:
                    os.remove(os.path.join(dirpath, f))
                    removed += 1
                except Exception:
                    pass
    return removed


class BuildPanel:
    def __init__(self, engine_root, project_root=None):
        self.engine_root = os.path.abspath(engine_root)
        self.project_root = os.path.abspath(project_root) if project_root else None
        self.visible = False
        self.rect = pygame.Rect(0, 0, 560, 340)
        self.log = []
        self.running = False
        self._thread = None
        self.status = "Готово к сборке"

    # ─── публичное API ──────────────────────────────────────
    def set_project(self, project_root):
        self.project_root = os.path.abspath(project_root) if project_root else None
        if self.visible:
            self._detect_env()

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
            f"engine_root: {self.engine_root}",
            f"project_root: {self.project_root or '— не открыт —'}",
        ]
        if self.project_root:
            main_py = os.path.join(self.project_root, "main.py")
            self.log.append(
                f"main.py игры: {'OK' if os.path.isfile(main_py) else 'НЕ НАЙДЕН'}")
        self.log.append("")
        if not shutil.which("pyinstaller"):
            self.status = "PyInstaller не установлен: pip install pyinstaller"
        elif not self.project_root:
            self.status = "Проект не открыт"
        else:
            self.status = "Готово к сборке"

    # ─── сборка ─────────────────────────────────────────────
    def start_build(self):
        if self.running:
            return
        if not shutil.which("pyinstaller"):
            self._log("✗ pyinstaller не найден. Установи: pip install pyinstaller")
            return
        if not self.project_root:
            self._log("✗ Проект не открыт. Открой проект (Ctrl+Shift+O).")
            return
        self.running = True
        self._log("→ Запуск сборки...")
        self.status = "Сборка..."
        self._thread = threading.Thread(target=self._build_worker, daemon=True)
        self._thread.start()

    def _build_worker(self):
        try:
            studio = self.engine_root
            project = self.project_root
            entry = os.path.join(project, "main.py")
            if not os.path.isfile(entry):
                self._log(f"✗ Не найден {entry}")
                self.status = "Ошибка сборки"
                return

            # Чистим кеши движка и проекта, чтобы PyInstaller не тянул старое.
            n1 = _clean_pycache(studio)
            n2 = _clean_pycache(project)
            self._log(f"→ Очищено __pycache__/*.pyc: engine={n1}, project={n2}")

            sep = ";" if platform.system() == "Windows" else ":"
            data_dir = os.path.join(project, "data")
            game_dir = os.path.join(project, "game")
            proj_name = os.path.basename(project.rstrip(os.sep)) or "game"

            cmd = [
                "pyinstaller",
                "--noconfirm",
                "--clean",
                "--windowed",
                "--name", "MazeGame",
                "--distpath", os.path.join(project, "dist"),
                "--workpath", os.path.join(project, "build"),
                "--specpath", os.path.join(project, "build"),
                "--add-data", f"{os.path.join(studio, 'engine')}{sep}engine",
                "--add-data", f"{os.path.join(studio, 'core')}{sep}core",
                "--paths", studio,
                "--paths", project,
                "--hidden-import", "pkg_resources._vendor.jaraco",
                "--hidden-import", "pkg_resources._vendor.jaraco.text",
            ]
            if os.path.isdir(data_dir):
                cmd += ["--add-data", f"{data_dir}{sep}data"]
            if os.path.isdir(game_dir):
                cmd += ["--add-data", f"{game_dir}{sep}game"]
            cmd.append(entry)

            self._log("$ " + " ".join(cmd))
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                self._log(line.rstrip())
            proc.wait()

            log_path = os.path.join(project, "build", "last_build.log")
            try:
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.log))
                self._log(f"→ Лог: {log_path}")
            except Exception as e:
                self._log(f"! Не удалось записать лог: {e}")

            if proc.returncode == 0:
                out = os.path.join(project, "dist", "MazeGame")
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
        if len(self.log) > 400:
            self.log = self.log[-400:]

    # ─── события ───────────────────────────────────────────
    def handle_event(self, e):
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

        log_rect = pygame.Rect(self.rect.x + 12, self.rect.y + 56,
                               self.rect.w - 24, self.rect.h - 110)
        pygame.draw.rect(surface, (28, 28, 34), log_rect)
        pygame.draw.rect(surface, skin.PANEL_BORDER, log_rect, 1)
        y = log_rect.y + 4
        for line in self.log[-16:]:
            t = ui.skin.render(line[:96], skin.TEXT)
            surface.blit(t, (log_rect.x + 6, y))
            y += 14
            if y > log_rect.bottom - 14:
                break

        btn_w, btn_h = 120, 28
        build_rect = pygame.Rect(self.rect.right - 270,
                                 self.rect.bottom - 40, btn_w, btn_h)
        close_rect = pygame.Rect(self.rect.right - 140,
                                 self.rect.bottom - 40, btn_w, btn_h)

        hover_build = build_rect.collidepoint(ui.mouse_pos)
        hover_close = close_rect.collidepoint(ui.mouse_pos)

        can_build = (not self.running) and bool(self.project_root)
        color_build = (skin.ACCENT_HOVER if (hover_build and can_build)
                       else (skin.ACCENT if can_build else (70, 70, 78)))
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
