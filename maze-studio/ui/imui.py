import pygame
from ui import skin


class IMUI:
    """Immediate-mode GUI. Все виджеты — методы класса, состояние — в _frame_*."""

    def __init__(self, skin_obj):
        self.skin = skin_obj
        self.mouse_pos = (0, 0)
        self.mouse_down = False
        self.mouse_pressed = False
        self.mouse_released = False
        self.mouse_wheel = 0
        self.hot_id = None
        self.active_id = None
        self.focus_id = None
        self._clip_stack = []
        self._text_input = ""
        self._enter_pressed = False
        self._escape_pressed = False

    # ─── кадр ───────────────────────────────────────────────
    def begin_frame(self, events):
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_wheel = 0
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.mouse_down = True
                self.mouse_pressed = True
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self.mouse_down = False
                self.mouse_released = True
            elif e.type == pygame.MOUSEWHEEL:
                self.mouse_wheel = e.y
            elif e.type == pygame.KEYDOWN:
                if self.focus_id is not None:
                    if e.key == pygame.K_BACKSPACE:
                        self._text_input = self._text_input[:-1]
                    elif e.key == pygame.K_RETURN:
                        self._enter_pressed = True
                    elif e.key == pygame.K_ESCAPE:
                        self._escape_pressed = True
                    elif e.unicode and e.unicode.isprintable():
                        self._text_input += e.unicode
        self.hot_id = None

    def end_frame(self):
        if self.mouse_pressed and self.hot_id is None:
            self.focus_id = None
        self.mouse_pressed = False
        self.mouse_released = False
        self._enter_pressed = False
        self._escape_pressed = False

    def _in_rect(self, rect):
        return rect.collidepoint(self.mouse_pos)

    def push_clip(self, surface, rect):
        self._clip_stack.append(surface.get_clip())
        surface.set_clip(rect)

    def pop_clip(self, surface):
        if self._clip_stack:
            surface.set_clip(self._clip_stack.pop())

    # ─── виджеты ────────────────────────────────────────────
    def button(self, surface, rect, label, on_click=None, active=False, wid=None):
        rect = pygame.Rect(rect)
        widget_id = wid if wid is not None else (rect.x, rect.y, rect.w, rect.h)
        hovered = self._in_rect(rect)
        if hovered:
            self.hot_id = widget_id
            if self.mouse_pressed:
                self.active_id = widget_id
        clicked = False
        if self.active_id == widget_id and self.mouse_released:
            if hovered and on_click:
                on_click()
                clicked = True
            self.active_id = None
        if active:
            color = skin.ACCENT
        elif hovered:
            color = skin.ACCENT_HOVER
        else:
            color = (60, 60, 66)
        pygame.draw.rect(surface, color, rect, border_radius=4)
        pygame.draw.rect(surface, skin.PANEL_BORDER, rect, 1, border_radius=4)
        txt = self.skin.render(label)
        surface.blit(txt, txt.get_rect(center=rect.center))
        return clicked

    def label(self, surface, pos, text, color=None, bold=False):
        color = color if color is not None else skin.TEXT
        txt = self.skin.render(text, color, bold)
        surface.blit(txt, pos)
        return txt.get_rect(topleft=pos)

    def text_input(self, surface, rect, value, on_change=None,
                   placeholder="", wid=None):
        rect = pygame.Rect(rect)
        widget_id = wid if wid is not None else (rect.x, rect.y, rect.w, rect.h)
        hovered = self._in_rect(rect)
        if hovered:
            self.hot_id = widget_id
            if self.mouse_pressed:
                self.focus_id = widget_id
                self._text_input = value
        focused = (self.focus_id == widget_id)
        bg = (70, 70, 80) if focused else ((55, 55, 62) if hovered else (40, 40, 46))
        pygame.draw.rect(surface, bg, rect)
        pygame.draw.rect(surface, skin.ACCENT if focused else skin.PANEL_BORDER,
                         rect, 1)
        display = self._text_input if focused else value
        color = skin.TEXT if display else skin.TEXT_DIM
        txt = self.skin.render(display or placeholder, color)
        surface.blit(txt, (rect.x + 6,
                           rect.y + (rect.h - txt.get_height()) // 2))
        if focused:
            cx = rect.x + 6 + self.skin.text_size(display)[0] + 1
            pygame.draw.line(surface, skin.TEXT, (cx, rect.y + 4),
                             (cx, rect.bottom - 4), 1)
        result = self._text_input if focused else value
        if focused and self._enter_pressed:
            self.focus_id = None
            if on_change:
                on_change(result)
        if focused and self._escape_pressed:
            self.focus_id = None
            return value
        return result

    def checkbox(self, surface, rect, label, value, wid=None):
        rect = pygame.Rect(rect)
        box = pygame.Rect(rect.x, rect.y + (rect.h - 16) // 2, 16, 16)
        widget_id = wid if wid is not None else (box.x, box.y, box.w, box.h)
        hovered = self._in_rect(box)
        if hovered:
            self.hot_id = widget_id
            if self.mouse_pressed:
                self.active_id = widget_id
        if self.active_id == widget_id and self.mouse_released:
            if hovered:
                value = not value
            self.active_id = None
        pygame.draw.rect(surface, (40, 40, 46), box)
        pygame.draw.rect(surface, skin.PANEL_BORDER, box, 1)
        if value:
            pygame.draw.line(surface, skin.ACCENT,
                             (box.x + 3, box.y + 8), (box.x + 7, box.y + 12), 2)
            pygame.draw.line(surface, skin.ACCENT,
                             (box.x + 7, box.y + 12), (box.x + 13, box.y + 4), 2)
        txt = self.skin.render(label)
        surface.blit(txt, (box.right + 8,
                           rect.y + (rect.h - txt.get_height()) // 2))
        return value

    def slider(self, surface, rect, value, min_v, max_v, label="", wid=None):
        rect = pygame.Rect(rect)
        widget_id = wid if wid is not None else (rect.x, rect.y, rect.w, rect.h)
        hovered = self._in_rect(rect)
        if hovered:
            self.hot_id = widget_id
            if self.mouse_pressed:
                self.active_id = widget_id
        if self.active_id == widget_id:
            if not self.mouse_down:
                self.active_id = None
            else:
                t = (self.mouse_pos[0] - rect.x) / rect.w
                t = max(0.0, min(1.0, t))
                value = min_v + (max_v - min_v) * t
        pygame.draw.rect(surface, (40, 40, 46), rect)
        t = (value - min_v) / (max_v - min_v) if max_v > min_v else 0
        fill = pygame.Rect(rect.x, rect.y, int(rect.w * t), rect.h)
        pygame.draw.rect(surface, skin.ACCENT, fill)
        hx = rect.x + int(rect.w * t)
        pygame.draw.rect(surface, skin.TEXT, (hx - 3, rect.y - 2, 6, rect.h + 4))
        pygame.draw.rect(surface, skin.PANEL_BORDER, rect, 1)
        if label:
            txt = self.skin.render(label, skin.TEXT_DIM)
            surface.blit(txt, (rect.right + 8,
                               rect.y + (rect.h - txt.get_height()) // 2))
        return value

    def float_field(self, surface, rect, value, label, tooltip_text,
                    vmin=None, vmax=None, step=0.1, wid=None):
        rect = pygame.Rect(rect)
        widget_id = wid if wid is not None else (rect.x, rect.y, rect.w, rect.h)
        hovered = self._in_rect(rect)

        if hovered:
            self.hot_id = widget_id
            if self.mouse_pressed and self.focus_id != widget_id:
                self.focus_id = widget_id
                self._text_input = f"{value:g}"

        focused = (self.focus_id == widget_id)

        lbl = self.skin.render(label, skin.TEXT_DIM)
        surface.blit(lbl, (rect.x, rect.y + (rect.h - lbl.get_height()) // 2))

        field_x = rect.x + 150
        field_w = max(70, rect.right - field_x)
        field_rect = pygame.Rect(field_x, rect.y, field_w, rect.h)

        bg = (70, 70, 80) if focused else \
             ((55, 55, 62) if hovered else (40, 40, 46))
        pygame.draw.rect(surface, bg, field_rect)
        pygame.draw.rect(surface,
                         skin.ACCENT if focused else skin.PANEL_BORDER,
                         field_rect, 1)

        txt_str = self._text_input if focused else f"{value:g}"
        txt = self.skin.render(txt_str, skin.TEXT)
        surface.blit(txt, (field_rect.x + 6,
                           field_rect.y + (field_rect.h - txt.get_height()) // 2))

        new_value = value
        if focused:
            if self._enter_pressed:
                try:
                    v = float(self._text_input)
                    if vmin is not None:
                        v = max(vmin, v)
                    if vmax is not None:
                        v = min(vmax, v)
                    new_value = v
                except ValueError:
                    pass
                self.focus_id = None
            elif self._escape_pressed:
                self.focus_id = None

        return new_value, hovered

    def tooltip(self, surface, anchor_rect, text_lines):
        if not text_lines:
            return
        lines = [self.skin.render(s, skin.TEXT) for s in text_lines]
        w = max(l.get_width() for l in lines) + 16
        h = sum(l.get_height() for l in lines) + 10
        x = anchor_rect.right + 8
        y = anchor_rect.y
        if x + w > surface.get_width():
            x = anchor_rect.x - w - 8
        if y + h > surface.get_height():
            y = surface.get_height() - h - 4
        panel = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (24, 24, 30), panel)
        pygame.draw.rect(surface, skin.ACCENT, panel, 1)
        yy = y + 5
        for l in lines:
            surface.blit(l, (x + 8, yy))
            yy += l.get_height()

    # ─── файловый диалог ────────────────────────────────────
    def file_picker(self, surface, rect, title, files, mode="save",
                    filename="level.json"):
        rect = pygame.Rect(rect)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (45, 45, 52), rect)
        pygame.draw.rect(surface, skin.ACCENT, rect, 2)

        title_s = self.skin.render(title, skin.TEXT, bold=True)
        surface.blit(title_s, (rect.x + 14, rect.y + 10))

        action = None
        result_name = filename

        list_rect = pygame.Rect(rect.x + 12, rect.y + 40,
                                rect.w - 24, rect.h - 110)
        pygame.draw.rect(surface, (30, 30, 36), list_rect)
        pygame.draw.rect(surface, skin.PANEL_BORDER, list_rect, 1)

        item_h = 20
        for i, f in enumerate(files[:20]):
            iy = list_rect.y + 4 + i * item_h
            irect = pygame.Rect(list_rect.x + 2, iy, list_rect.w - 4, item_h)
            hovered = irect.collidepoint(self.mouse_pos)
            if hovered:
                pygame.draw.rect(surface, skin.ACCENT_HOVER, irect)
                if self.mouse_pressed:
                    result_name = f
            t = self.skin.render(f, skin.TEXT)
            surface.blit(t, (irect.x + 4, iy + 2))

        input_rect = pygame.Rect(rect.x + 12, rect.bottom - 60, rect.w - 24, 24)
        if mode == "save":
            result_name = self.text_input(surface, input_rect, result_name,
                                          placeholder="имя файла.json",
                                          wid=("filepicker", "name"))
        else:
            pygame.draw.rect(surface, (40, 40, 46), input_rect)
            pygame.draw.rect(surface, skin.PANEL_BORDER, input_rect, 1)
            t = self.skin.render(result_name, skin.TEXT)
            surface.blit(t, (input_rect.x + 6, input_rect.y + 4))

        btn_w, btn_h = 90, 26
        ok_rect = pygame.Rect(rect.right - 200, rect.bottom - 28, btn_w, btn_h)
        cancel_rect = pygame.Rect(rect.right - 104, rect.bottom - 28, btn_w, btn_h)

        hovered_ok = ok_rect.collidepoint(self.mouse_pos)
        hovered_cancel = cancel_rect.collidepoint(self.mouse_pos)

        if self.mouse_pressed and not (
            rect.collidepoint(self.mouse_pos)
            or list_rect.collidepoint(self.mouse_pos)
            or input_rect.collidepoint(self.mouse_pos)
            or ok_rect.collidepoint(self.mouse_pos)
            or cancel_rect.collidepoint(self.mouse_pos)
        ):
            return "cancel", result_name

        pygame.draw.rect(surface, skin.ACCENT if hovered_ok else (60, 60, 66),
                         ok_rect, border_radius=4)
        pygame.draw.rect(surface, skin.PANEL_BORDER, ok_rect, 1, border_radius=4)
        ok_lbl = self.skin.render("OK", skin.TEXT)
        surface.blit(ok_lbl, ok_lbl.get_rect(center=ok_rect.center))

        pygame.draw.rect(surface, skin.ACCENT if hovered_cancel else (60, 60, 66),
                         cancel_rect, border_radius=4)
        pygame.draw.rect(surface, skin.PANEL_BORDER, cancel_rect, 1, border_radius=4)
        cn_lbl = self.skin.render("Отмена", skin.TEXT)
        surface.blit(cn_lbl, cn_lbl.get_rect(center=cancel_rect.center))

        if self.mouse_released:
            if hovered_ok:
                action = "ok"
            elif hovered_cancel:
                action = "cancel"

        return action, result_name
