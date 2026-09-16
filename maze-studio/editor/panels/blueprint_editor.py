import pygame
from ui import skin
from engine.blueprints.registry import all_types


class BlueprintEditor:
    """Полноценный редактор графа: узлы, связи, палитра, drag, удаление."""

    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.graph = None
        self.on_change = None
        self.drag_node = None
        self.drag_offset = (0, 0)
        self.link_from = None  # (node_id, pin_name)
        self.hover_pin = None
        self.selected_node = None

    def load(self, graph, on_change=None):
        self.graph = graph
        self.on_change = on_change

    def _notify(self):
        if self.on_change and self.graph:
            self.on_change(self.graph)

    # ─── отрисовка ─────────────────────────────────────────
    def draw(self, surface, skin_obj, ui):
        pygame.draw.rect(surface, (28, 28, 32), self.rect)
        pygame.draw.rect(surface, skin.PANEL_BORDER, self.rect, 1)
        if not self.graph:
            surface.blit(skin_obj.render("Нет блюпринта", skin.TEXT_DIM),
                         (self.rect.x + 12, self.rect.y + 12))
            return

        self._draw_edges(surface, skin_obj)
        self._draw_nodes(surface, skin_obj, ui)
        self._draw_palette(surface, skin_obj, ui)

        if self.link_from:
            a = self._pin_pos(*self.link_from)
            pygame.draw.line(surface, skin.ACCENT_HOVER, a, ui.mouse_pos, 2)

    def _pin_pos(self, node_id, pin_name):
        for n in self.graph.nodes:
            if n["id"] != node_id:
                continue
            x, y = n.get("pos", [self.rect.x + 40, self.rect.y + 40])
            # вход сверху, выход снизу
            return (x + 70, y + 36)
        return (self.rect.x, self.rect.y)

    def _draw_edges(self, surface, skin_obj):
        pos = {n["id"]: n.get("pos", [self.rect.x + 40, self.rect.y + 40])
               for n in self.graph.nodes}
        for e in self.graph.edges:
            a = pos.get(e["from_id"])
            b = pos.get(e["to_id"])
            if not a or not b:
                continue
            p1 = (a[0] + 70, a[1] + 36)
            p2 = (b[0] + 70, b[1])
            pygame.draw.line(surface, skin.ACCENT, p1, p2, 2)

    def _draw_nodes(self, surface, skin_obj, ui):
        for n in self.graph.nodes:
            x, y = n.get("pos", [self.rect.x + 40, self.rect.y + 40])
            rect = pygame.Rect(x, y, 140, 36)
            hovered = rect.collidepoint(ui.mouse_pos)
            selected = (n is self.selected_node)
            bg = (70, 70, 80) if selected else ((60, 60, 70) if hovered else (50, 50, 58))
            pygame.draw.rect(surface, bg, rect, border_radius=4)
            pygame.draw.rect(surface, skin.ACCENT if selected else skin.PANEL_BORDER,
                             rect, 1, border_radius=4)
            surface.blit(skin_obj.render(n["type"], skin.TEXT, bold=True),
                         (x + 8, y + 4))
            params = n.get("params", {})
            if params:
                s = ", ".join(f"{k}={v}" for k, v in params.items())[:22]
                surface.blit(skin_obj.render(s, skin.TEXT_DIM), (x + 8, y + 20))
            # клик — drag/select
            if ui.mouse_pressed and rect.collidepoint(ui.mouse_pos):
                self.drag_node = n
                self.drag_offset = (ui.mouse_pos[0] - x, ui.mouse_pos[1] - y)
                self.selected_node = n
            # drag с зажатой ЛКМ
            if self.drag_node is n and ui.mouse_down:
                nx = ui.mouse_pos[0] - self.drag_offset[0]
                ny = ui.mouse_pos[1] - self.drag_offset[1]
                n["pos"] = [nx, ny]
            if ui.mouse_released and self.drag_node is n:
                self.drag_node = None
                self._notify()

    def _draw_palette(self, surface, skin_obj, ui):
        """Слева вертикальный список всех доступных типов узлов."""
        palette_w = 140
        palette_rect = pygame.Rect(self.rect.x, self.rect.y, palette_w,
                                   self.rect.h)
        pygame.draw.rect(surface, (38, 38, 44), palette_rect)
        pygame.draw.line(surface, skin.PANEL_BORDER,
                         (palette_rect.right - 1, palette_rect.y),
                         (palette_rect.right - 1, palette_rect.bottom))
        surface.blit(skin_obj.render("Узлы", skin.TEXT, bold=True),
                     (palette_rect.x + 8, palette_rect.y + 6))
        y = palette_rect.y + 28
        for type_name in sorted(all_types().keys()):
            r = pygame.Rect(palette_rect.x + 4, y, palette_w - 8, 18)
            hovered = r.collidepoint(ui.mouse_pos)
            if hovered:
                pygame.draw.rect(surface, skin.ACCENT_HOVER, r)
            surface.blit(skin_obj.render(type_name, skin.TEXT), (r.x + 4, y + 2))
            if hovered and ui.mouse_pressed:
                self._add_node(type_name)
            y += 18
            if y > palette_rect.bottom:
                break

    def _add_node(self, type_name):
        if not self.graph:
            return
        import uuid
        nid = f"n_{uuid.uuid4().hex[:6]}"
        self.graph.nodes.append({
            "id": nid, "type": type_name, "params": {},
            "pos": [self.rect.x + 200, self.rect.y + 60],
        })
        self._notify()

    # ─── действия ──────────────────────────────────────────
    def delete_selected(self):
        if not self.graph or not self.selected_node:
            return
        nid = self.selected_node["id"]
        self.graph.nodes = [n for n in self.graph.nodes if n["id"] != nid]
        self.graph.edges = [e for e in self.graph.edges
                            if e["from_id"] != nid and e["to_id"] != nid]
        self.selected_node = None
        self._notify()

    def set_params(self, node, **params):
        if not self.graph:
            return
        node.setdefault("params", {}).update(params)
        self._notify()
