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
