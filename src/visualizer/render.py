"""Low-level drawing primitives: anti-aliased shapes, glows, the drone
sprite and the pre-rendered background."""
import math
import pygame
from pygame import gfxdraw

from src.visualizer.theme import RGB, RGBA, ARM, BG, GRID_DOT, mix, rgba

Point = tuple[float, float]


def _i(v: float) -> int:
    return int(round(v))


def aa_circle(
        surf: pygame.Surface, color: RGB | RGBA, center: Point, radius: float
) -> None:
    """Filled, anti-aliased circle (alpha in `color` is blended)."""
    r = max(1, _i(radius))
    x, y = _i(center[0]), _i(center[1])
    gfxdraw.aacircle(surf, x, y, r, color)
    gfxdraw.filled_circle(surf, x, y, r, color)


def ring(
        surf: pygame.Surface, color: RGB, center: Point,
        radius: float, width: int
) -> None:
    """Opaque ring with anti-aliased inner and outer edges."""
    x, y = _i(center[0]), _i(center[1])
    r = _i(radius)
    pygame.draw.circle(surf, color, (x, y), r, width)
    gfxdraw.aacircle(surf, x, y, r, color)
    if r - width + 1 > 0:
        gfxdraw.aacircle(surf, x, y, r - width + 1, color)


def dashed_ring(
        surf: pygame.Surface, color: RGB, center: Point, radius: float,
        width: int, dashes: int = 10, phase: float = 0.0
) -> None:
    rect = pygame.Rect(0, 0, _i(radius * 2), _i(radius * 2))
    rect.center = (_i(center[0]), _i(center[1]))
    step = 2 * math.pi / dashes
    for k in range(dashes):
        a = phase + k * step
        pygame.draw.arc(surf, color, rect, a, a + step * 0.55, width)


def thick_line(
        surf: pygame.Surface, color: RGB | RGBA, p1: Point, p2: Point,
        width: float, caps: bool = True
) -> None:
    """Anti-aliased line of arbitrary width (alpha in `color` is blended)."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 0.01:
        return
    if width <= 1.2:
        pygame.draw.aaline(surf, color[:3], p1, p2)
        return
    nx, ny = -dy / length * width / 2, dx / length * width / 2
    pts = [
        (_i(p1[0] + nx), _i(p1[1] + ny)),
        (_i(p2[0] + nx), _i(p2[1] + ny)),
        (_i(p2[0] - nx), _i(p2[1] - ny)),
        (_i(p1[0] - nx), _i(p1[1] - ny)),
    ]
    gfxdraw.aapolygon(surf, pts, color)
    gfxdraw.filled_polygon(surf, pts, color)
    if caps and len(color) == 3:
        aa_circle(surf, color, p1, width / 2 - 0.5)
        aa_circle(surf, color, p2, width / 2 - 0.5)


def radial_glow(radius: int, color: RGB, max_alpha: int,
                falloff: float = 2.0) -> pygame.Surface:
    """Soft radial gradient sprite, transparent at the edge."""
    radius = max(2, radius)
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        a = max_alpha * (1 - r / radius) ** falloff
        pygame.draw.circle(surf, rgba(color, int(a)), (radius, radius), r)
    return surf


def blit_center(
        surf: pygame.Surface, sprite: pygame.Surface, center: Point
) -> None:
    surf.blit(sprite, sprite.get_rect(center=(_i(center[0]), _i(center[1]))))


def panel(
        surf: pygame.Surface, rect: pygame.Rect, fill: RGBA,
        border: RGBA | None = None, radius: int = 14
) -> None:
    """Translucent rounded rectangle."""
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    local = layer.get_rect()
    pygame.draw.rect(layer, fill, local, border_radius=radius)
    if border is not None:
        pygame.draw.rect(layer, border, local, 1, border_radius=radius)
    surf.blit(layer, rect.topleft)


# ---------- drone ----------

def draw_drone(
        surf: pygame.Surface, pos: Point, heading: float, size: float,
        color: RGB, spin: float, altitude: float,
        glow: pygame.Surface | None = None
) -> None:
    """
    Top-down quadcopter. `size` is the arm length, `altitude` (0..1) makes
    the drone bigger and pushes its shadow away to give a sense of height.
    """
    x, y = pos
    s = size * (0.82 + 0.3 * altitude)

    # shadow on the ground
    off = s * 0.3 + altitude * size * 1.1
    gfxdraw.filled_ellipse(
        surf, _i(x + off), _i(y + off * 1.3),
        max(2, _i(s * 1.3)), max(2, _i(s * 1.0)),
        (0, 0, 0, _i(85 - 35 * altitude)),
    )
    if glow is not None and altitude > 0.02:
        blit_center(surf, glow, pos)

    # arms + rotors (X configuration relative to heading)
    arm_w = max(2.0, s * 0.24)
    rotor_r = s * 0.56
    for k in range(4):
        a = heading + math.pi / 4 + k * math.pi / 2
        rx, ry = x + math.cos(a) * s, y + math.sin(a) * s
        thick_line(surf, ARM, (x, y), (rx, ry), arm_w)
        aa_circle(surf, (205, 215, 240, 38), (rx, ry), rotor_r)
        gfxdraw.aacircle(
            surf, _i(rx), _i(ry), max(1, _i(rotor_r)), (205, 215, 240, 90)
        )
        # two-blade props, neighbouring rotors counter-rotate
        b = spin * (1 if k % 2 == 0 else -1) + k
        bx, by = math.cos(b) * rotor_r * 0.92, math.sin(b) * rotor_r * 0.92
        thick_line(
            surf, (235, 240, 252, 190),
            (rx - bx, ry - by), (rx + bx, ry + by), max(1.5, s * 0.1),
            caps=False,
        )
        aa_circle(surf, (70, 78, 104), (rx, ry), max(1.0, s * 0.13))

    # body
    rb = s * 0.46
    aa_circle(surf, (16, 20, 34), pos, rb + 1.5)
    aa_circle(surf, color, pos, rb)
    aa_circle(
        surf, mix(color, (255, 255, 255), 0.5),
        (x - rb * 0.28, y - rb * 0.28), rb * 0.42,
    )
    # navigation lights: white nose, red tail
    hx, hy = math.cos(heading), math.sin(heading)
    aa_circle(surf, (255, 255, 255), (x + hx * rb, y + hy * rb),
              max(1.4, s * 0.15))
    aa_circle(surf, (255, 80, 90), (x - hx * rb, y - hy * rb),
              max(1.1, s * 0.11))


# ---------- background ----------

def build_background(size: tuple[int, int],
                     scale: float = 1.0) -> pygame.Surface:
    """Flat dark background with a faint dot grid."""
    w, h = size
    bg = pygame.Surface(size)
    bg.fill(BG)
    step = max(8, round(32 * scale))
    dot = max(1, round(scale))
    for gx in range(step // 2, w, step):
        for gy in range(step // 2, h, step):
            bg.fill(GRID_DOT, (gx, gy, dot, dot))
    return bg
