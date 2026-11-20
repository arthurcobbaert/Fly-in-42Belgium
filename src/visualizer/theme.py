"""Colors, fonts and small color helpers shared by the visualizer."""
import colorsys
import pygame

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

# ---------- background ----------
BG: RGB = (12, 15, 23)
GRID_DOT: RGB = (26, 31, 45)

# ---------- UI ----------
BAR_FILL: RGB = (17, 21, 32)
DIVIDER: RGB = (32, 38, 54)
PANEL_FILL: RGBA = (20, 25, 38, 240)
PANEL_BORDER: RGBA = (255, 255, 255, 22)
TEXT: RGB = (230, 234, 242)
TEXT_MUTED: RGB = (156, 164, 184)
TEXT_DIM: RGB = (112, 120, 142)
ACCENT: RGB = (94, 200, 250)
SUCCESS: RGB = (74, 222, 128)
WARNING: RGB = (251, 191, 36)
GOAL: RGB = (250, 204, 21)

# ---------- graph ----------
EDGE: RGB = (38, 45, 63)
EDGE_ROUTE: RGB = (60, 70, 96)
EDGE_ACTIVE: RGB = (110, 150, 190)
HUB_BASE: RGB = (14, 18, 28)
ARM: RGB = (44, 50, 68)

ZONE_COLORS: dict[str, RGB] = {
    "normal": (148, 163, 200),
    "priority": (52, 211, 153),
    "restricted": (251, 146, 60),
    "blocked": (100, 108, 128),
}
ZONE_LABELS: dict[str, str] = {
    "normal": "Normal",
    "priority": "Priority",
    "restricted": "Restricted",
    "blocked": "Blocked",
}

FONT_STACK = "avenirnext,helveticaneue,segoeui,ubuntu,dejavusans,arial"


def mix(a: RGB, b: RGB, t: float) -> RGB:
    """Linear blend between two colors (t=0 -> a, t=1 -> b)."""
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def rgba(c: RGB, alpha: int) -> RGBA:
    return (c[0], c[1], c[2], max(0, min(255, alpha)))


def hsv(h: float, s: float, v: float) -> RGB:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def drone_color(index: int) -> RGB:
    """Distinct, vivid color per drone (golden-ratio hue spacing)."""
    return hsv(0.13 + index * 0.618034, 0.62, 1.0)


def resolve_color(name: str | None, fallback: RGB, t: float = 0.0) -> RGB:
    """
    Resolve a map-provided color word to RGB. 'rainbow' cycles through hues
    over time. Unknown words get a stable pseudo-color derived from the word
    so that any single-word color in a map never crashes the visualizer.
    """
    if not name:
        return fallback
    if name.lower() == "rainbow":
        return hsv(t * 0.12, 0.7, 1.0)
    try:
        c = pygame.Color(name)
        return (c.r, c.g, c.b)
    except ValueError:
        h = sum(ord(ch) * (i + 1) for i, ch in enumerate(name.lower()))
        return hsv((h % 360) / 360.0, 0.55, 0.9)


class Fonts:
    """Lazy, cached access to system fonts and rendered text. Sizes are
    given in points and multiplied by `scale` (pixels per point)."""

    def __init__(self, scale: float = 1.0) -> None:
        self.scale = scale
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}
        self._text: dict[tuple[str, int, bool, RGB], pygame.Surface] = {}

    def set_scale(self, scale: float) -> None:
        if scale != self.scale:
            self.scale = scale
            self._fonts.clear()
            self._text.clear()

    def get(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont(
                FONT_STACK, max(1, round(size * self.scale)), bold
            )
        return self._fonts[key]

    def render(
            self, text: str, size: int, color: RGB, bold: bool = False
    ) -> pygame.Surface:
        key = (text, size, bold, color)
        surf = self._text.get(key)
        if surf is None:
            if len(self._text) > 2000:
                self._text.clear()
            surf = self.get(size, bold).render(text, True, color)
            self._text[key] = surf
        return surf
