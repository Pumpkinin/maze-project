import os
import pygame

FONT_CANDIDATES = [
    os.path.expanduser("~/Library/Fonts/BigBlueTerm437NerdFont-Regular.ttf"),
    os.path.expanduser("~/Library/Fonts/BigBlueTermPlusNerdFont-Regular.ttf"),
    "/Library/Fonts/BigBlueTerm437NerdFont-Regular.ttf",
    "/Library/Fonts/BigBlueTermPlusNerdFont-Regular.ttf",
    os.path.expanduser("~/.local/share/fonts/BigBlueTerm437NerdFont-Regular.ttf"),
    "/usr/share/fonts/TTF/BigBlueTerm437NerdFont-Regular.ttf",
    "/usr/share/fonts/truetype/BigBlueTerm437NerdFont-Regular.ttf",
    os.path.expandvars(
        r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\BigBlueTerm437NerdFont-Regular.ttf"),
    os.path.join(os.path.dirname(__file__), "..", "assets", "fonts",
                 "BigBlueTerm437NerdFont-Regular.ttf"),
]
FONT_FALLBACKS = ["BigBlueTerm437 Nerd Font", "BigBlueTermPlus Nerd Font",
                  "BigBlue Terminal", "BigBlueTerm437"]

BG = (32, 32, 36)
PANEL_BG = (45, 45, 50)
PANEL_BORDER = (70, 70, 78)
TEXT = (220, 220, 220)
TEXT_DIM = (140, 140, 150)
ACCENT = (80, 140, 220)
ACCENT_HOVER = (110, 170, 250)
GRID_COLOR = (50, 50, 58)
WALL_COLOR = (200, 200, 210)

TOOLBAR_H = 40
LEFT_W = 240
RIGHT_W = 300
FONT_SIZE = 14
FONT_SIZE_BOLD = 14


def find_font_path():
    for p in FONT_CANDIDATES:
        if os.path.isfile(p):
            return p
    return None


def load_font(size):
    p = find_font_path()
    if p:
        try:
            return pygame.font.Font(p, size)
        except Exception:
            pass
    for n in FONT_FALLBACKS:
        try:
            return pygame.font.SysFont(n, size)
        except Exception:
            continue
    return pygame.font.SysFont("monospace", size)


class Skin:
    def __init__(self):
        self.font = load_font(FONT_SIZE)
        self.font_bold = load_font(FONT_SIZE_BOLD)
        self.antialias = False

    def render(self, text, color=TEXT, bold=False):
        f = self.font_bold if bold else self.font
        return f.render(str(text), self.antialias, color)

    def text_size(self, text, bold=False):
        f = self.font_bold if bold else self.font
        return f.size(str(text))
