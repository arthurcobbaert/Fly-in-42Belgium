import pygame
import math
import sys
from src.models.graph import Graph

ZONE_COLORS = {
    "normal": (86, 156, 214),
    "priority": (64, 224, 208),
    "restricted": (240, 140, 60),
    "blocked": (110, 110, 120),
}
BG_TOP = (10, 12, 24)
BG_BOTTOM = (22, 26, 46)
GRID_COLOR = (35, 40, 60)
LINE_COLOR = (90, 96, 120)
TEXT_COLOR = (225, 228, 240)
DRONE_BODY = (255, 210, 60)
DRONE_ROTOR = (255, 240, 190)

PADDING = 90
HUB_RADIUS = 22
GLOW_RADIUS = 34
DRONE_SIZE = 16
WINDOW_SIZE = (1100, 750)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class Visualizer:
    def __init__(
            self,
            graph: Graph,
            events: list[dict],
            drone_ids: list[int],
            seconds_per_turn: float = 0.8
    ):
        pygame.init()
        self.graph = graph
        self.drone_ids = sorted(drone_ids)
        self.seconds_per_turn = seconds_per_turn

        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Fly-in — Drone Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 14)
        self.header_font = pygame.font.SysFont("consolas", 18, bold=True)

        self.positions = self._compute_positions()

        initial = {
            drone_id: self.graph.start_hub for drone_id in self.drone_ids
        }
        self.snapshots = [initial] + events
        self.total_turns = len(self.snapshots) - 1

        self.drone_offsets = self._build_drone_offsets()
        self.drone_icon = self._build_drone_icon()
        self.background = self._build_background()

        self.current_turn = 0
        self.elapsed_in_turn = 0.0
        self.playing = True

    # ---------- setup helpers ----------

    def _compute_positions(self) -> dict[str, tuple[int, int]]:
        xs = [hub.x for hub in self.graph.hubs.values()]
        ys = [hub.y for hub in self.graph.hubs.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        usable_w = WINDOW_SIZE[0] - 2 * PADDING
        usable_h = WINDOW_SIZE[1] - 2 * PADDING

        def scale(x: float, y: float) -> tuple[int, int]:
            nx = 0.5 if max_x == min_x else (x - min_x) / (max_x - min_x)
            ny = 0.5 if max_y == min_y else (y - min_y) / (max_y - min_y)
            ny = 1.0 - ny
            return (int(PADDING + nx * usable_w), int(PADDING + ny * usable_h))

        return {
            name: scale(hub.x, hub.y)
            for name, hub in self.graph.hubs.items()
        }

    def _build_drone_offsets(self) -> dict[int, tuple[float, float]]:
        """Fixed small offset per drone so multiple drones at the same hub
        cluster around its center instead of overlapping."""
        offsets = {}
        n = max(len(self.drone_ids), 1)
        radius = min(12, HUB_RADIUS - 8)
        for i, drone_id in enumerate(self.drone_ids):
            angle = 2 * math.pi * i / n
            offsets[drone_id] = (
                math.cos(angle) * radius, math.sin(angle) * radius
            )
        return offsets

    def _build_drone_icon(self) -> pygame.Surface:
        size = DRONE_SIZE
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        arm = size // 2 - 2
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            end = (cx + dx * arm, cy + dy * arm)
            pygame.draw.line(surf, DRONE_ROTOR, (cx, cy), end, 2)
            pygame.draw.circle(surf, DRONE_ROTOR, end, 3)
        pygame.draw.circle(surf, DRONE_BODY, (cx, cy), 4)
        return surf

    def _build_background(self) -> pygame.Surface:
        bg = pygame.Surface(WINDOW_SIZE)
        for y in range(WINDOW_SIZE[1]):
            t = y / WINDOW_SIZE[1]
            color = (
                int(lerp(BG_TOP[0], BG_BOTTOM[0], t)),
                int(lerp(BG_TOP[1], BG_BOTTOM[1], t)),
                int(lerp(BG_TOP[2], BG_BOTTOM[2], t)),
            )
            pygame.draw.line(bg, color, (0, y), (WINDOW_SIZE[0], y))
        step = 40
        for x in range(0, WINDOW_SIZE[0], step):
            pygame.draw.line(bg, GRID_COLOR, (x, 0), (x, WINDOW_SIZE[1]), 1)
        for y in range(0, WINDOW_SIZE[1], step):
            pygame.draw.line(bg, GRID_COLOR, (0, y), (WINDOW_SIZE[0], y), 1)
        return bg

    # ---------- main loop ----------

    def run(self) -> None:
        while True:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.playing = not self.playing
                    elif event.key == pygame.K_RIGHT:
                        self._advance_turn()
                        self.playing = False
                    elif event.key == pygame.K_LEFT:
                        self.current_turn = max(0, self.current_turn - 1)
                        self.elapsed_in_turn = 0.0
                        self.playing = False
                    elif event.key == pygame.K_UP:
                        self.seconds_per_turn = max(
                            0.1, self.seconds_per_turn - 0.1
                        )
                    elif event.key == pygame.K_DOWN:
                        self.seconds_per_turn += 0.1

            if self.playing and self.current_turn < self.total_turns:
                self.elapsed_in_turn += dt
                if self.elapsed_in_turn >= self.seconds_per_turn:
                    self.elapsed_in_turn = 0.0
                    self._advance_turn()
                    if self.current_turn >= self.total_turns:
                        self.playing = False

            self._draw()
            pygame.display.flip()

    def _advance_turn(self) -> None:
        self.current_turn = min(self.current_turn + 1, self.total_turns)
        self.elapsed_in_turn = 0.0

    # ---------- drawing ----------

    def _draw(self) -> None:
        self.screen.blit(self.background, (0, 0))

        for conn in self.graph.connections:
            p1 = self.positions[conn.hub_a]
            p2 = self.positions[conn.hub_b]
            pygame.draw.line(self.screen, LINE_COLOR, p1, p2, 2)

        for name, hub in self.graph.hubs.items():
            pos = self.positions[name]
            color = ZONE_COLORS.get(hub.zone_type, ZONE_COLORS["normal"])

            glow = pygame.Surface(
                (GLOW_RADIUS * 2, GLOW_RADIUS * 2), pygame.SRCALPHA
            )
            pygame.draw.circle(
                glow, (*color, 60), (GLOW_RADIUS, GLOW_RADIUS), GLOW_RADIUS
            )
            self.screen.blit(
                glow, (pos[0] - GLOW_RADIUS, pos[1] - GLOW_RADIUS)
            )

            pygame.draw.circle(self.screen, color, pos, HUB_RADIUS)
            pygame.draw.circle(
                self.screen, (250, 250, 250), pos, HUB_RADIUS, 2
            )

            label = self.font.render(name, True, TEXT_COLOR)
            label_pos = (
                pos[0] - label.get_width() // 2, pos[1] + HUB_RADIUS + 6
            )
            backing = pygame.Surface(
                (
                    label.get_width() + 6, label.get_height() + 2
                ), pygame.SRCALPHA)
            backing.fill((10, 12, 24, 160))
            self.screen.blit(backing, (label_pos[0] - 3, label_pos[1] - 1))
            self.screen.blit(label, label_pos)

        snapshot = self.snapshots[self.current_turn]
        for drone_id in self.drone_ids:
            hub_name = snapshot[drone_id]
            base = self.positions[hub_name]
            ox, oy = self.drone_offsets[drone_id]
            pos = (int(base[0] + ox), int(base[1] + oy))

            icon_rect = self.drone_icon.get_rect(center=pos)
            self.screen.blit(self.drone_icon, icon_rect)
            id_label = self.font.render(str(drone_id), True, TEXT_COLOR)
            self.screen.blit(
                id_label, (
                    pos[0]-id_label.get_width() // 2, pos[1]+DRONE_SIZE // 2+1
                )
            )

        status = "PLAYING" if self.playing else "PAUSED"
        header = self.header_font.render(
            f"Turn {self.current_turn} / {self.total_turns}   [{status}]   "
            f"{self.seconds_per_turn:.1f}"
            "s/turn   SPACE play/pause | <- -> step | up/down speed",
            True, TEXT_COLOR,
        )
        self.screen.blit(header, (14, 12))

        legend_y = WINDOW_SIZE[1] - 26
        for i, (zone, color) in enumerate(ZONE_COLORS.items()):
            box_x = 14 + i * 150
            pygame.draw.circle(self.screen, color, (box_x, legend_y), 8)
            label = self.font.render(zone, True, TEXT_COLOR)
            self.screen.blit(label, (box_x + 14, legend_y - 8))
