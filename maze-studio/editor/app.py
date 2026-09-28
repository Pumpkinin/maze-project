import os
import sys
import math
import pygame

from ui import skin
from ui.imui import IMUI
from core.serialize import save_json, load_json
from engine.ecs.scene import Scene
from engine.input.input import Input
from engine.assets.registry import AssetRegistry
from engine.render.camera import Camera3D
from engine.render.postfx_loader import find_preset
from engine.systems.physics_system import PhysicsSystem
from engine.systems.script_system import ScriptSystem
from engine.systems.input_system import InputSystem
from engine.blueprints.graph import Blueprint
from editor.tools import TOOLS
from editor.history import UndoStack
from editor.panels.toolbar import Toolbar
from editor.panels.viewport import Viewport
from editor.panels.hierarchy import HierarchyPanel
from editor.panels.inspector import InspectorPanel
from editor.panels.asset_browser import AssetBrowser
from editor.panels.blueprint_editor import BlueprintEditor
from editor.file_dialog import FileDialog
from editor.panels.build_panel import BuildPanel
from editor import config as editor_config
from editor.project import Project

ENGINE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class EditorApp:
    def __init__(self):
        pygame.init()
        self.fullscreen = False
        self.win_w, self.win_h = 1280, 720
        self.screen = pygame.display.set_mode(
            (self.win_w, self.win_h),
            pygame.RESIZABLE | pygame.DOUBLEBUF)
        pygame.display.set_caption("MazeEditor")
        self.clock = pygame.time.Clock()
        self.skin = skin.Skin()
        self.ui = IMUI(self.skin)
        self.running = True
        self.status = "Готово"
        self.tool = "select"
        self.history = UndoStack()

        # Корни: движок и проект.
        self.engine_root = ENGINE_ROOT
        self.engine_data_root = os.path.join(self.engine_root, "data")
        self.project = None          # editor.project.Project | None
        self.project_root = None

        # Ввод — создаём ДО систем.
        input_path = os.path.join(self.engine_data_root, "input", "default.json")
        try:
            self.input = Input.load(input_path)
        except Exception as e:
            print(f"[input] не удалось загрузить: {e}")
            self.input = Input()

        # Сцена.
        self.scene = Scene(16, 16)
        self.scene_path = None
        self._attach_default_systems()

        # Реестры ассетов (движка).
        self.assets = AssetRegistry(self.engine_root)
        for k, sub in [("levels", "data/levels"), ("prefabs", "data/prefabs"),
                       ("blueprints", "data/blueprints"),
                       ("effects", "data/effects"),
                       ("input", "data/input")]:
            self.assets.scan(k, sub)

        # Превью.
        self.preview = None
        self.preview_surface = None
        self.preview_rect = pygame.Rect(0, 0, 320, 200)
        self.preview_active = False
        self._recompute_layout()

        # Панели. BuildPanel — до Toolbar (в тулбаре есть кнопка Build).
        self.build_panel = BuildPanel(self.engine_root, self.project_root)
        self.toolbar = Toolbar(self.rect_toolbar, self)
        self.viewport = Viewport(self.rect_view)
        self.hierarchy = HierarchyPanel(self.rect_left)
        self.inspector = InspectorPanel(self.rect_right)
        self.browser = AssetBrowser(self.rect_left_bottom, self.project_root)
        self.bp_editor = BlueprintEditor(self.rect_right_bottom)
        self.dialog = FileDialog()
        # Диалог выбора проекта (отдельный режим).
        self.project_dialog = {"mode": None, "files": [], "filename": ""}

        self.cam_drag = False
        self.cam_drag_start = (0, 0)

        # Восстанавливаем последний проект из конфига.
        self._restore_last_project()

    # ─── проект ───────────────────────────────────────────
    def _restore_last_project(self):
        last = editor_config.get_last_project()
        if last and os.path.isdir(last):
            p = Project(last)
            if p.is_valid():
                self._set_project(p)
                self.status = f"Проект: {p.name()}"
                return
        self.status = "Проект не открыт — New Proj / Project"

    def _set_project(self, project):
        self.project = project
        self.project_root = project.root
        self.browser.set_project(self.project_root)
        self.build_panel.set_project(self.project_root)
        editor_config.remember_project(self.project_root)

    def action_open_project(self):
        # Простейший ввод пути: используем file_picker только как UI,
        # но по факту просим путь текстом в том же диалоге.
        self.project_dialog = {
            "mode": "open_project",
            "files": editor_config.get_recent_projects(),
            "filename": self.project_root or "",
        }

    def action_new_project(self):
        self.project_dialog = {
            "mode": "new_project",
            "files": [],
            "filename": os.path.join(self.engine_root, "..", "new-game"),
        }

    # ─── системы ──────────────────────────────────────────
    def _attach_default_systems(self):
        self.scene.systems = []
        self.scene.add_system(InputSystem(self.input))
        self.scene.add_system(ScriptSystem(self._load_blueprint))
        self.scene.add_system(PhysicsSystem())

    def _load_blueprint(self, name):
        # Сначала — проект, потом — движок (как fallback для шаблонов).
        for base in (self.project_root, self.engine_data_root):
            if not base:
                continue
            p = os.path.join(base, "blueprints", name + ".json")
            if os.path.isfile(p):
                try:
                    return load_json(p)
                except Exception as e:
                    print(f"[bp] {name}: {e}")
        return None

    # ─── layout ───────────────────────────────────────────
    def _recompute_layout(self):
        self.rect_toolbar = pygame.Rect(0, 0, self.win_w, skin.TOOLBAR_H)
        half = (self.win_h - skin.TOOLBAR_H - 22) // 2
        self.rect_left = pygame.Rect(0, skin.TOOLBAR_H, skin.LEFT_W, half)
        self.rect_left_bottom = pygame.Rect(
            0, self.rect_left.bottom, skin.LEFT_W,
            self.win_h - skin.TOOLBAR_H - 22 - half)
        self.rect_right = pygame.Rect(
            self.win_w - skin.RIGHT_W, skin.TOOLBAR_H,
            skin.RIGHT_W, half)
        self.rect_right_bottom = pygame.Rect(
            self.win_w - skin.RIGHT_W, self.rect_right.bottom,
            skin.RIGHT_W,
            self.win_h - skin.TOOLBAR_H - 22 - half)
        self.rect_view = pygame.Rect(
            skin.LEFT_W, skin.TOOLBAR_H,
            self.win_w - skin.LEFT_W - skin.RIGHT_W,
            self.win_h - skin.TOOLBAR_H - 22)
        self.rect_status = pygame.Rect(0, self.win_h - 22, self.win_w, 22)
        self._recompute_preview_rect()

    def _recompute_preview_rect(self):
        pw, ph = 320, 200
        self.preview_rect = pygame.Rect(
            self.rect_view.right - pw - 10,
            self.rect_view.bottom - ph - 10, pw, ph)

    def _on_resize(self, w, h):
        self.win_w, self.win_h = w, h
        self._recompute_layout()
        for name, rect in (("viewport", self.rect_view),
                           ("hierarchy", self.rect_left),
                           ("inspector", self.rect_right),
                           ("browser", self.rect_left_bottom),
                           ("bp_editor", self.rect_right_bottom),
                           ("toolbar", self.rect_toolbar)):
            obj = getattr(self, name, None)
            if obj is not None:
                obj.rect = rect

    # ─── действия ─────────────────────────────────────────
    def set_tool(self, tool):
        self.tool = tool
        for b in self.toolbar.buttons:
            b.active = (b.tool == tool)

    def action_new(self):
        self.scene = Scene(16, 16)
        self._attach_default_systems()
        self.preview = None
        self.history.clear()
        self.scene_path = None
        self.status = "Новый уровень"

    def _project_levels_dir(self):
        if self.project_root:
            return os.path.join(self.project_root, "data", "levels")
        return os.path.join(self.engine_data_root, "levels")

    def action_open(self):
        d = self._project_levels_dir()
        files = sorted(f for f in os.listdir(d)
                       if f.endswith(".json")) if os.path.isdir(d) else []
        self.dialog.open_open(files,
                              os.path.basename(self.scene_path or "demo.json"))

    def action_save(self):
        d = self._project_levels_dir()
        files = sorted(f for f in os.listdir(d)
                       if f.endswith(".json")) if os.path.isdir(d) else []
        self.dialog.open_save(files,
                              os.path.basename(self.scene_path or "level.json"))

    def action_undo(self):
        self.history.undo()
        self.status = "Undo"

    def action_redo(self):
        self.history.redo()
        self.status = "Redo"

    def _do_save(self, name):
        if not self.project_root:
            self.status = "Проект не открыт"
            return
        path = os.path.join(self.project_root, "data", "levels", name)
        save_json(path, self.scene.to_dict())
        self.scene_path = path
        self.status = f"Сохранено: {name}"

    def _do_open(self, name):
        # Сначала ищем в проекте, потом в движке.
        for base in (self.project_root, self.engine_data_root):
            if not base:
                continue
            path = os.path.join(base, "levels", name)
            if os.path.isfile(path):
                try:
                    d = load_json(path)
                    self.scene = Scene.from_dict(d)
                    self._attach_default_systems()
                    self.scene_path = path
                    self.preview = None
                    self.history.clear()
                    self.status = f"Загружено: {name}"
                except Exception as e:
                    self.status = f"Ошибка: {e}"
                return
        self.status = f"Не найдено: {name}"

    def toggle_preview(self):
        self.preview_active = not self.preview_active
        if self.preview_active:
            self.input.push_context("gameplay")
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
            pygame.mouse.get_rel()
            self._rebuild_preview()
            self.status = "Play (F5/Esc — выход)"
        else:
            self.input.pop_context("gameplay")
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            self.status = "Редактор"

    def _rebuild_preview(self):
        for e in self.scene.entities.values():
            if e.has("camera"):
                # effects ищем в проекте, потом в движке.
                preset = None
                name = e.get("camera").effects_preset
                for base in (self.project_root, self.engine_data_root):
                    if not base:
                        continue
                    p = os.path.join(base, "effects", name + ".json")
                    if os.path.isfile(p):
                        preset = find_preset(base, name)
                        break
                self.preview = Camera3D(e.get("camera"), preset or {"effects": []})
                self.preview.set_pitch(0.0)
                return
        self.preview = None

    # ─── события ─────────────────────────────────────────
    def handle_events(self, events):
        self.ui.begin_frame(events)
        self.input.begin_frame(events)

        # Диалог выбора/создания проекта — отдельный, путь вводится текстом.
        if self.project_dialog["mode"]:
            action, name = self.ui.file_picker(
                self.screen,
                pygame.Rect((self.win_w - 560) // 2,
                            (self.win_h - 360) // 2, 560, 360),
                "Открыть проект" if self.project_dialog["mode"] == "open_project"
                else "Новый проект",
                self.project_dialog["files"], mode="save",
                filename=self.project_dialog["filename"])
            if action == "ok" and name:
                name = os.path.expanduser(name)
                if self.project_dialog["mode"] == "open_project":
                    p = Project(name)
                    if p.is_valid():
                        self._set_project(p)
                        self.status = f"Проект: {p.name()}"
                    else:
                        self.status = f"Нет data/ в {name}"
                else:
                    p = Project.create_from_templates(
                        name, self.engine_data_root)
                    self._set_project(p)
                    self.status = f"Создан проект: {p.name()}"
                self.project_dialog = {"mode": None, "files": [], "filename": ""}
            elif action == "cancel":
                self.project_dialog = {"mode": None, "files": [], "filename": ""}
            self.ui.end_frame()
            return

        if self.dialog.mode:
            action, name = self.ui.file_picker(
                self.screen,
                pygame.Rect((self.win_w - 500) // 2,
                            (self.win_h - 340) // 2, 500, 340),
                "Сохранить как" if self.dialog.mode == "save" else "Открыть",
                self.dialog.files, mode=self.dialog.mode,
                filename=self.dialog.filename)
            if action == "ok":
                if not name.endswith(".json"):
                    name += ".json"
                if self.dialog.mode == "save":
                    self._do_save(name)
                else:
                    self._do_open(name)
                self.dialog.close()
            elif action == "cancel":
                self.dialog.close()
            self.ui.end_frame()
            return

        for e in events:
            if self.build_panel.handle_event(e):
                continue
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.VIDEORESIZE:
                self._on_resize(e.w, e.h)
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if self.preview_active:
                        self.toggle_preview()
                    else:
                        self.running = False
                if e.key == pygame.K_F5:
                    self.toggle_preview()
                if e.key == pygame.K_F6:
                    self.build_panel.toggle()
                if e.key == pygame.K_F11:
                    self._toggle_fullscreen()
                if not self.preview_active:
                    if e.key == pygame.K_1: self.set_tool("select")
                    if e.key == pygame.K_2: self.set_tool("wall_v")
                    if e.key == pygame.K_3: self.set_tool("wall_h")
                    if e.key == pygame.K_4: self.set_tool("erase")
                    if e.key == pygame.K_5: self.set_tool("spawn")
                    if e.key == pygame.K_6: self.set_tool("exit")
                    ctrl = bool(e.mod & pygame.KMOD_CTRL)
                    shift = bool(e.mod & pygame.KMOD_SHIFT)
                    if ctrl and e.key == pygame.K_s: self.action_save()
                    if ctrl and e.key == pygame.K_o and not shift: self.action_open()
                    if ctrl and e.key == pygame.K_n: self.action_new()
                    if ctrl and e.key == pygame.K_z: self.action_undo()
                    if ctrl and e.key == pygame.K_y: self.action_redo()
                    if ctrl and shift and e.key == pygame.K_o:
                        self.action_open_project()
                    if ctrl and shift and e.key == pygame.K_n:
                        self.action_new_project()
                    if e.key == pygame.K_DELETE:
                        self.bp_editor.delete_selected()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = e.pos
                if self.preview_active:
                    continue
                if e.button == 1:
                    if self.rect_toolbar.collidepoint(mx, my):
                        for b in self.toolbar.buttons:
                            if b.rect.collidepoint(mx, my):
                                b.on_click()
                                break
                    elif self.rect_view.collidepoint(mx, my):
                        self.apply_tool(mx, my)
                elif e.button in (2, 3):
                    if self.rect_view.collidepoint(mx, my):
                        self.cam_drag = True
                        self.cam_drag_start = (mx, my)
            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button in (2, 3):
                    self.cam_drag = False
            elif e.type == pygame.MOUSEMOTION:
                mx, my = e.pos
                if self.preview_active:
                    t = self._find_camera_transform()
                    if t:
                        t.angle += e.rel[0] * 0.003
                    if self.preview:
                        self.preview.set_pitch(self.preview.pitch - e.rel[1] * 0.002)
                else:
                    if self.cam_drag:
                        self.viewport.pan(mx - self.cam_drag_start[0],
                                          my - self.cam_drag_start[1])
                        self.cam_drag_start = (mx, my)
                    self.viewport.update_hover(mx, my)
            elif e.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if not self.preview_active and self.rect_view.collidepoint(mx, my):
                    self.viewport.zoom_at(mx, my, e.y)

        self.ui.end_frame()

    def _find_camera_transform(self):
        for e in self.scene.entities.values():
            if e.has("camera") and e.has("transform"):
                return e.get("transform")
        return None

    def apply_tool(self, mx, my):
        wx, wy = self.viewport.screen_to_world(mx, my)
        cx, cy = int(math.floor(wx)), int(math.floor(wy))
        t = TOOLS.get(self.tool)
        if t:
            t.apply(self.scene, wx, wy, cx, cy, history=self.history)

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = (pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE) \
            | pygame.DOUBLEBUF
        size = (0, 0) if self.fullscreen else (1280, 720)
        self.screen = pygame.display.set_mode(size, flags)
        self._on_resize(*self.screen.get_size())

    # ─── update / draw ────────────────────────────────────
    def update(self, dt):
        if self.preview_active:
            self.scene.update(dt, self.input)
            if not self.preview:
                self._rebuild_preview()
            if self.preview:
                for e in self.scene.entities.values():
                    if e.has("camera"):
                        self.preview_surface = self.preview.render(self.scene, e, dt)
                        break

    def draw(self):
        self.screen.fill(skin.BG)
        if self.preview_active:
            if self.preview_surface is not None:
                scaled = pygame.transform.scale(self.preview_surface,
                                                (self.win_w, self.win_h))
                self.screen.blit(scaled, (0, 0))
            pygame.display.flip()
            return

        self.viewport.draw(self.screen, self.scene, self.skin)
        self._draw_preview_corner()
        self.toolbar.draw(self.screen, self.skin)
        self.hierarchy.draw(self.screen, self.scene, self.skin, self.ui)
        self.inspector.draw(self.screen, self, self.skin)
        self.browser.draw(self.screen, self.skin, self.ui,
                          on_pick=self._on_asset_pick)

        sel = self.scene.entities.get(self.scene.selection)
        if sel and sel.has("script"):
            bp_data = self._load_blueprint(sel.get("script").blueprint)
            if bp_data:
                bp = Blueprint.from_dict(bp_data)
                self.bp_editor.load(bp, on_change=self._save_blueprint)
        self.bp_editor.draw(self.screen, self.skin, self.ui)
        self._draw_status()

        if self.dialog.mode:
            self.ui.file_picker(
                self.screen,
                pygame.Rect((self.win_w - 500) // 2,
                            (self.win_h - 340) // 2, 500, 340),
                "Сохранить как" if self.dialog.mode == "save" else "Открыть",
                self.dialog.files, mode=self.dialog.mode,
                filename=self.dialog.filename)
        if self.project_dialog["mode"]:
            self.ui.file_picker(
                self.screen,
                pygame.Rect((self.win_w - 560) // 2,
                            (self.win_h - 360) // 2, 560, 360),
                "Открыть проект" if self.project_dialog["mode"] == "open_project"
                else "Новый проект",
                self.project_dialog["files"], mode="save",
                filename=self.project_dialog["filename"])
        self.build_panel.draw(self.screen, self.ui)
        pygame.display.flip()

    def _save_blueprint(self, bp):
        sel = self.scene.entities.get(self.scene.selection)
        if not sel or not sel.has("script"):
            return
        name = sel.get("script").blueprint
        if not name or not self.project_root:
            return
        p = os.path.join(self.project_root, "data", "blueprints", name + ".json")
        save_json(p, bp.to_dict())
        for s in self.scene.systems:
            if s.name == "script":
                s.invalidate(name)

    def _draw_preview_corner(self):
        if not self.preview_surface:
            pygame.draw.rect(self.screen, (30, 30, 34), self.preview_rect)
            pygame.draw.rect(self.screen, skin.PANEL_BORDER, self.preview_rect, 2)
            self.screen.blit(self.skin.render("PLAY [F5]", skin.TEXT_DIM),
                             (self.preview_rect.x + 6, self.preview_rect.y + 6))
            return
        scaled = pygame.transform.scale(
            self.preview_surface, (self.preview_rect.w, self.preview_rect.h))
        self.screen.blit(scaled, self.preview_rect.topleft)
        pygame.draw.rect(self.screen, skin.ACCENT, self.preview_rect, 2)

    def _draw_status(self):
        pygame.draw.rect(self.screen, (28, 28, 32), self.rect_status)
        proj = self.project.name() if self.project else "—"
        text = f"{self.status}    |    Проект: {proj}"
        self.screen.blit(self.skin.render(text, skin.TEXT_DIM),
                         (8, self.rect_status.y + 4))

    def _on_asset_pick(self, kind, path):
        if kind == "levels":
            self._do_open(os.path.basename(path))

    # ─── run ──────────────────────────────────────────────
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            events = pygame.event.get()
            self.handle_events(events)
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()
