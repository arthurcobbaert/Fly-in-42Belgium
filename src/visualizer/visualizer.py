"""Pygame visualizer for the Fly-in drone simulation.

All layout constants are written in points; `self.k` (pixels per point)
converts them so the window stays sharp on high-DPI screens."""
import math
import sys
import pygame

from src.models.graph import Graph
from src.models.hubs import Hub
from src.visualizer.hidpi import Display
from src.visualizer.render import (
    Point, aa_circle, blit_center, build_background, dashed_ring,
    draw_drone, panel, ring, thick_line,
)
from src.visualizer.theme import (
    RGB, ACCENT, BAR_FILL, BG, DIVIDER, EDGE, EDGE_ACTIVE, EDGE_ROUTE,
    GOAL, HUB_BASE, PANEL_BORDER, PANEL_FILL, SUCCESS, TEXT, TEXT_DIM,
    TEXT_MUTED, WARNING, ZONE_COLORS, ZONE_LABELS, Fonts, drone_color,
    mix, resolve_color, rgba,
)
from src.visualizer.timeline import DroneState, Flight, Timeline

TOPBAR_H = 52
MIN_SIZE = (820, 560)
DEFAULT_SIZE = (1280, 820)

CONTROLS: list[tuple[str, str]] = [
    ("Space", "Play / pause"),
    ("Left/Right", "Step one turn"),
    ("Up/Down", "Speed"),
    ("R", "Restart"),
    ("L", "Toggle labels"),
    ("H", "Toggle this help"),
    ("Esc", "Quit"),
]


class Visualizer:
    def __init__(
            self,
            graph: Graph,
            events: list[dict[int, str]],
            drone_ids: list[int],
            seconds_per_turn: float = 0.8,
            map_name: str = "",
    ) -> None:
        pygame.init()
        self.graph = graph
        self.map_name = map_name
        self.drone_ids = sorted(drone_ids)
        self.seconds_per_turn = seconds_per_turn

        initial = {d: graph.start_hub for d in self.drone_ids}
        self.timeline = Timeline(graph, [initial] + events, self.drone_ids)
        self.total_turns = self.timeline.total_turns
        self.route_edges = self.timeline.route_edges()
        self.colors = {d: drone_color(i) for i, d in enumerate(self.drone_ids)}

        self.display = Display("Fly-in", self._initial_size(), MIN_SIZE)
        self.clock = pygame.time.Clock()
        self.fonts = Fonts()

        self.time = 0.0             # simulation time, in turns
        self.anim = 0.0             # wall-clock seconds, for idle animation
        self.playing = True
        self.show_labels = True
        self.show_help = False
        self.dragging = False
        self.mouse: tuple[int, int] = (-1, -1)
        self.headings: dict[int, float] = {}
        self._layout()
        for d in self.drone_ids:
            self.headings[d] = self._initial_heading(d)

    # ------------------------------------------------------------ setup

    def _initial_size(self) -> tuple[int, int]:
        try:
            dw, dh = pygame.display.get_desktop_sizes()[0]
        except (pygame.error, IndexError):
            return DEFAULT_SIZE
        return (
            max(MIN_SIZE[0], min(DEFAULT_SIZE[0], int(dw * 0.9))),
            max(MIN_SIZE[1], min(DEFAULT_SIZE[1], int(dh * 0.88))),
        )

    def px(self, v: float) -> int:
        """Points -> whole pixels."""
        return round(v * self.k)

    def _layout(self) -> None:
        """(Re)compute everything that depends on the window size."""
        self.screen = self.display.surface
        self.k = self.display.scale
        self.fonts.set_scale(self.k)
        w, h = self.screen.get_size()
        bar_h = self.px(TOPBAR_H)
        self.canvas = pygame.Rect(0, bar_h, w, h - bar_h)
        self.progress_rect = pygame.Rect(0, bar_h - self.px(3), w,
                                         self.px(3))
        self.positions = self._compute_positions()

        min_dist = self._min_hub_distance() / self.k
        self.hub_r = max(6.0, min(15.0, min_dist * 0.2)) * self.k
        self.drone_size = max(5.0, min(11.0, self.hub_r / self.k * 0.7)) \
            * self.k
        self.line_w = max(1, self.px(2))
        self.background = build_background((w, h), self.k)

    def _compute_positions(self) -> dict[str, Point]:
        hubs = self.graph.hubs.values()
        xs = [hub.x for hub in hubs]
        ys = [hub.y for hub in hubs]
        min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
        span_x, span_y = max_x - min_x, max_y - min_y

        area = self.canvas.inflate(-self.px(140), -self.px(120))
        sx = area.w / span_x if span_x else math.inf
        sy = area.h / span_y if span_y else math.inf
        base = min(sx, sy)
        if base == math.inf:
            base = 0.0
        # allow a little stretching to use the space, but keep the shape
        sx, sy = min(sx, base * 2.0), min(sy, base * 2.0)
        cx, cy = (min_x + max_x) / 2, (min_y + max_y) / 2
        return {
            name: (
                area.centerx + (hub.x - cx) * sx,
                area.centery - (hub.y - cy) * sy,   # world y points up
            )
            for name, hub in self.graph.hubs.items()
        }

    def _min_hub_distance(self) -> float:
        pts = list(self.positions.values())
        best = 120.0 * self.k
        for i, a in enumerate(pts):
            for b in pts[i + 1:]:
                best = min(best, math.hypot(a[0] - b[0], a[1] - b[1]))
        return best

    def _hub_color(self, hub: Hub) -> RGB:
        if hub.name == self.graph.start_hub:
            return SUCCESS
        if hub.name == self.graph.end_hub:
            return GOAL
        zone = ZONE_COLORS.get(hub.zone_type, ZONE_COLORS["normal"])
        if hub.zone_type == "blocked":
            return zone
        # soften raw map colors (pure blue/red...) to fit the palette
        return mix(resolve_color(hub.color, zone, self.anim),
                   (225, 230, 240), 0.22)

    def _initial_heading(self, drone_id: int) -> float:
        f = self.timeline.next_flight(drone_id, 0.0)
        if f is None:
            return -math.pi / 2
        a, b = self.positions[f.src], self.positions[f.dst]
        return math.atan2(b[1] - a[1], b[0] - a[0])

    # ------------------------------------------------------------ loop

    def run(self) -> None:
        while True:
            dt = min(self.clock.tick(60) / 1000.0, 0.1)
            self.anim += dt
            self._handle_events()
            if self.display.sync_size():
                self._layout()
            if self.playing and not self.dragging:
                self.time += dt / self.seconds_per_turn
                if self.time >= self.total_turns:
                    self.time = float(self.total_turns)
                    self.playing = False
            self._draw(dt)
            self.display.present()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
            elif event.type == pygame.VIDEORESIZE:
                self.display.resized(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEMOTION:
                self.mouse = self.display.to_pixels(event.pos)
                if self.dragging:
                    self._seek(self.mouse[0])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self.display.to_pixels(event.pos)
                if self._progress_hit().collidepoint(pos):
                    self.dragging = True
                    self._seek(pos[0])
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False

    def _handle_key(self, key: int) -> None:
        if key in (pygame.K_ESCAPE, pygame.K_q):
            self._quit()
        elif key == pygame.K_SPACE:
            if self.time >= self.total_turns:
                self.time = 0.0
                self.playing = True
            else:
                self.playing = not self.playing
        elif key == pygame.K_RIGHT:
            self.time = min(float(self.total_turns),
                            math.floor(self.time + 1e-6) + 1.0)
            self.playing = False
        elif key == pygame.K_LEFT:
            self.time = max(0.0, math.ceil(self.time - 1e-6) - 1.0)
            self.playing = False
        elif key == pygame.K_UP:
            self.seconds_per_turn = max(0.1, self.seconds_per_turn / 1.25)
        elif key == pygame.K_DOWN:
            self.seconds_per_turn = min(4.0, self.seconds_per_turn * 1.25)
        elif key == pygame.K_r:
            self.time = 0.0
            self.playing = True
        elif key == pygame.K_l:
            self.show_labels = not self.show_labels
        elif key == pygame.K_h:
            self.show_help = not self.show_help

    def _progress_hit(self) -> pygame.Rect:
        """Generous click area around the thin progress line."""
        return self.progress_rect.inflate(0, self.px(16))

    def _seek(self, mouse_x: int) -> None:
        r = self.progress_rect
        if r.w <= 0:
            return
        frac = max(0.0, min(1.0, (mouse_x - r.x) / r.w))
        self.time = frac * self.total_turns

    @staticmethod
    def _quit() -> None:
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------ geometry

    def _flight_point(self, f: Flight, p: float) -> Point:
        a, b = self.positions[f.src], self.positions[f.dst]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        lateral = f.lane * self.drone_size * 2.4 * math.sin(math.pi * p)
        return (a[0] + dx * p + nx * lateral, a[1] + dy * p + ny * lateral)

    def _parked_offsets(self, n: int) -> list[Point]:
        """Sunflower layout so any number of drones fit around a hub."""
        if n == 1:
            return [(0.0, 0.0)]
        c = self.drone_size * 1.35
        golden = math.pi * (3 - math.sqrt(5))
        return [
            (c * math.sqrt(k + 0.6) * math.cos(k * golden - math.pi / 2),
             c * math.sqrt(k + 0.6) * math.sin(k * golden - math.pi / 2))
            for k in range(n)
        ]

    def _cluster_extent(self, n: int) -> float:
        if n <= 1:
            return 0.0
        return max(0.0, self.drone_size * 1.35 * math.sqrt(n) - self.hub_r)

    # ------------------------------------------------------------ drawing

    def _draw(self, dt: float) -> None:
        self.screen.blit(self.background, (0, 0))

        states = {d: self.timeline.state(d, self.time)
                  for d in self.drone_ids}
        parked: dict[str, list[int]] = {}
        for d, st in states.items():
            if st.hub is not None:
                parked.setdefault(st.hub, []).append(d)

        hovered = self._hovered_hub()
        self._draw_edges(states)
        self._draw_trails(states)
        self._draw_hubs(parked, hovered)
        self._draw_drones(states, parked, dt)
        if hovered is not None:
            self._draw_tooltip(hovered, len(parked.get(hovered, [])))
        if self.show_help:
            self._draw_help()
        self._draw_topbar(states)

    def _draw_edges(self, states: dict[int, DroneState]) -> None:
        active = {
            frozenset((st.flight.src, st.flight.dst))
            for st in states.values() if st.flight is not None
        }
        for conn in self.graph.connections:
            key = frozenset((conn.hub_a, conn.hub_b))
            p1, p2 = self.positions[conn.hub_a], self.positions[conn.hub_b]
            if key in active:
                color = EDGE_ACTIVE
            elif key in self.route_edges:
                color = EDGE_ROUTE
            else:
                color = EDGE
            width = (2.5 if conn.max_link_capacity > 1 else 1.6) * self.k
            thick_line(self.screen, color, p1, p2, width)

            length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            if conn.max_link_capacity > 1 and length > self.hub_r * 6:
                mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                txt = self.fonts.render(
                    f"×{conn.max_link_capacity}", 10, TEXT_DIM, True
                )
                box = txt.get_rect(center=(int(mid[0]), int(mid[1])))
                pygame.draw.rect(self.screen, BG,
                                 box.inflate(self.px(6), self.px(2)),
                                 border_radius=self.px(4))
                blit_center(self.screen, txt, mid)

    def _draw_trails(self, states: dict[int, DroneState]) -> None:
        for d, st in states.items():
            f = st.flight
            if f is None:
                continue
            color = self.colors[d]
            p_end = st.progress
            p_start = max(0.0, p_end - 0.3)
            steps = 10
            prev = self._flight_point(f, p_start)
            for i in range(1, steps + 1):
                t = i / steps
                cur = self._flight_point(f, p_start + (p_end - p_start) * t)
                thick_line(self.screen, rgba(color, int(110 * t * t)),
                           prev, cur,
                           1.5 * self.k + self.drone_size * 0.2 * t,
                           caps=False)
                prev = cur

    def _draw_hubs(self, parked: dict[str, list[int]],
                   hovered: str | None) -> None:
        r = self.hub_r
        lw = self.line_w
        for name, hub in self.graph.hubs.items():
            pos = self.positions[name]
            color = self._hub_color(hub)
            endpoint = name in (self.graph.start_hub, self.graph.end_hub)

            if name == hovered:
                aa_circle(self.screen, rgba(color, 40), pos,
                          r + self.px(6))

            if endpoint:
                aa_circle(self.screen, mix(HUB_BASE, color, 0.25), pos, r)
                ring(self.screen, color, pos, r, lw)
                aa_circle(self.screen, color, pos, r * 0.38)
            elif hub.zone_type == "blocked":
                dim = mix(HUB_BASE, color, 0.7)
                aa_circle(self.screen, HUB_BASE, pos, r)
                ring(self.screen, dim, pos, r, lw)
                k = r * 0.42
                thick_line(self.screen, dim, (pos[0] - k, pos[1] + k),
                           (pos[0] + k, pos[1] - k), lw)
            else:
                aa_circle(self.screen, HUB_BASE, pos, r)
                if hub.zone_type == "restricted":
                    dashed_ring(self.screen, color, pos, r, lw, 10)
                else:
                    ring(self.screen, color, pos, r, lw)
                if hub.zone_type == "priority":
                    aa_circle(self.screen, color, pos, r * 0.3)

        if self.show_labels:
            self._draw_hub_labels(parked)

    def _draw_hub_labels(self, parked: dict[str, list[int]]) -> None:
        """Hub names under each hub. Labels that would overlap another
        label or hub are skipped (hover a hub to see its details)."""
        r = self.hub_r
        pad = self.px(3)
        taken = [
            pygame.Rect(int(x - r - pad), int(y - r - pad),
                        int(2 * (r + pad)), int(2 * (r + pad)))
            for x, y in self.positions.values()
        ]
        order = sorted(
            self.graph.hubs,
            key=lambda n: n not in (self.graph.start_hub, self.graph.end_hub),
        )
        for name in order:
            pos = self.positions[name]
            if name == self.graph.start_hub:
                color = SUCCESS
            elif name == self.graph.end_hub:
                color = GOAL
            else:
                color = TEXT_MUTED
            txt = self.fonts.render(name, 11, color)
            extra = self._cluster_extent(len(parked.get(name, [])))
            y = pos[1] + r + self.px(6) + extra
            box = txt.get_rect(midtop=(int(pos[0]), int(y)))
            if box.inflate(self.px(4), 0).collidelist(taken) != -1:
                continue
            taken.append(box.inflate(self.px(8), self.px(2)))
            self.screen.blit(txt, box)

    def _draw_drones(self, states: dict[int, DroneState],
                     parked: dict[str, list[int]], dt: float) -> None:
        draw_list: list[tuple[float, int, Point]] = []
        crowded = {d for ids in parked.values() if len(ids) > 3 for d in ids}

        for hub_name, ids in parked.items():
            base = self.positions[hub_name]
            for d, (ox, oy) in zip(sorted(ids),
                                   self._parked_offsets(len(ids))):
                draw_list.append((0.0, d, (base[0] + ox, base[1] + oy)))

        for d, st in states.items():
            f = st.flight
            if f is None:
                continue
            a, b = self.positions[f.src], self.positions[f.dst]
            target = math.atan2(b[1] - a[1], b[0] - a[0])
            self._turn_towards(d, target, dt)
            altitude = math.sin(math.pi * st.progress)
            draw_list.append((altitude, d,
                              self._flight_point(f, st.progress)))

        # parked first, then flying drones from low to high
        draw_list.sort(key=lambda item: (item[0], item[1]))
        for altitude, d, pos in draw_list:
            flying = states[d].flight is not None
            spin = self.anim * (30.0 if flying else 9.0) + d
            draw_drone(self.screen, pos, self.headings[d], self.drone_size,
                       self.colors[d], spin, altitude)
            if self.show_labels and (flying or d not in crowded):
                self._drone_badge(d, pos, altitude)

    def _turn_towards(self, d: int, target: float, dt: float) -> None:
        cur = self.headings[d]
        diff = (target - cur + math.pi) % (2 * math.pi) - math.pi
        self.headings[d] = cur + diff * min(1.0, dt * 9.0)

    def _drone_badge(self, d: int, pos: Point, altitude: float) -> None:
        s = self.drone_size * (0.82 + 0.3 * altitude)
        txt = self.fonts.render(str(d), 10, self.colors[d], True)
        self.screen.blit(txt, (int(pos[0] + s * 1.1),
                               int(pos[1] - s * 1.1 - txt.get_height())))

    def _hovered_hub(self) -> str | None:
        if not self.canvas.collidepoint(self.mouse):
            return None
        mx, my = self.mouse
        for name, (x, y) in self.positions.items():
            if math.hypot(mx - x, my - y) <= self.hub_r + self.px(6):
                return name
        return None

    def _draw_tooltip(self, name: str, here: int) -> None:
        hub = self.graph.hubs[name]
        rows = [
            ("Zone", ZONE_LABELS.get(hub.zone_type, hub.zone_type)),
            ("Capacity", str(hub.max_drones)),
            ("Drones here", str(here)),
            ("Position", f"{hub.x}, {hub.y}"),
        ]
        p = self.px
        title = self.fonts.render(name, 13, TEXT, True)
        w = max(p(170), title.get_width() + p(40))
        h = p(38 + len(rows) * 18)
        x, y = self.mouse[0] + p(16), self.mouse[1] + p(16)
        x = min(x, self.canvas.right - w - p(10))
        y = min(y, self.canvas.bottom - h - p(10))
        rect = pygame.Rect(x, y, w, h)
        panel(self.screen, rect, PANEL_FILL, PANEL_BORDER, p(8))
        aa_circle(self.screen, self._hub_color(hub), (x + p(16), y + p(19)),
                  p(4))
        self.screen.blit(title, (x + p(26),
                                 y + p(19) - title.get_height() // 2))
        for i, (k, v) in enumerate(rows):
            ry = y + p(34 + i * 18)
            self.screen.blit(self.fonts.render(k, 12, TEXT_MUTED),
                             (x + p(14), ry))
            val = self.fonts.render(v, 12, TEXT)
            self.screen.blit(val, (x + w - p(14) - val.get_width(), ry))

    def _draw_help(self) -> None:
        p = self.px
        w, h = p(240), p(24 + len(CONTROLS) * 20)
        rect = pygame.Rect(p(16), self.canvas.bottom - h - p(16), w, h)
        panel(self.screen, rect, PANEL_FILL, PANEL_BORDER, p(8))
        for i, (key, label) in enumerate(CONTROLS):
            ry = rect.y + p(12 + i * 20)
            self.screen.blit(self.fonts.render(key, 12, TEXT, True),
                             (rect.x + p(14), ry))
            self.screen.blit(self.fonts.render(label, 12, TEXT_MUTED),
                             (rect.x + p(96), ry))

    # ------------------------------------------------------------ top bar

    def _status(self) -> tuple[str, RGB]:
        if self.time >= self.total_turns:
            return "Complete", SUCCESS
        if self.playing:
            return "Playing", ACCENT
        return "Paused", WARNING

    def _draw_topbar(self, states: dict[int, DroneState]) -> None:
        p = self.px
        w = self.screen.get_width()
        pygame.draw.rect(self.screen, BAR_FILL, (0, 0, w, p(TOPBAR_H)))
        cy = p(TOPBAR_H - 3) // 2

        def blit_mid(surf: pygame.Surface, x: int) -> int:
            self.screen.blit(surf, (x, cy - surf.get_height() // 2))
            return x + surf.get_width()

        # left: title + map
        x = blit_mid(self.fonts.render("Fly-in", 16, TEXT, True), p(20))
        if self.map_name:
            blit_mid(self.fonts.render(self.map_name, 13, TEXT_MUTED),
                     x + p(12))

        # center: turn counter + status
        turn = min(self.total_turns, math.ceil(self.time - 1e-9))
        t1 = self.fonts.render(f"Turn {turn}", 15, TEXT, True)
        t2 = self.fonts.render(f" / {self.total_turns}", 15, TEXT_MUTED)
        label, color = self._status()
        st = self.fonts.render(label, 12, color)
        group = t1.get_width() + t2.get_width() + p(26) + st.get_width()
        x = w // 2 - group // 2
        x = blit_mid(t2, blit_mid(t1, x)) + p(16)
        aa_circle(self.screen, color, (x + p(3), cy), p(3))
        blit_mid(st, x + p(10))

        # right: key numbers
        delivered = sum(1 for s in states.values()
                        if s.hub == self.graph.end_hub)
        flying = sum(1 for s in states.values() if s.flight is not None)
        items: list[tuple[str, str, RGB]] = [
            (f"{delivered}/{len(states)}", "delivered", SUCCESS),
            (str(flying), "flying", ACCENT),
            (f"{1 / self.seconds_per_turn:.1f}", "turns/s", TEXT),
            ("H", "help", TEXT_MUTED),
        ]
        x = w - p(20)
        for value, name, col in reversed(items):
            lbl = self.fonts.render(name, 12, TEXT_DIM)
            val = self.fonts.render(value, 13, col, True)
            x -= lbl.get_width()
            blit_mid(lbl, x)
            x -= val.get_width() + p(5)
            blit_mid(val, x)
            x -= p(22)

        # progress line along the bottom edge of the bar
        bar = self.progress_rect
        pygame.draw.rect(self.screen, DIVIDER, bar)
        frac = self.time / self.total_turns if self.total_turns else 1.0
        pygame.draw.rect(self.screen, ACCENT,
                         (bar.x, bar.y, int(bar.w * frac), bar.h))
        if self.dragging or self._progress_hit().collidepoint(self.mouse):
            aa_circle(self.screen, TEXT,
                      (bar.x + bar.w * frac, bar.centery), p(5))
