"""Turns the simulation's per-turn snapshots into continuous flights so
drones can be animated smoothly between hubs."""
from dataclasses import dataclass
from src.models.graph import Graph


@dataclass(frozen=True)
class Flight:
    drone_id: int
    src: str
    dst: str
    start: float      # time (in turns) the drone leaves `src`
    end: float        # time (in turns) the drone lands on `dst`
    lane: float       # lateral offset when several drones share an edge


@dataclass(frozen=True)
class DroneState:
    drone_id: int
    hub: str | None           # hub the drone is parked at, None if flying
    flight: Flight | None
    progress: float           # eased progress along the flight (0..1)


def ease(t: float) -> float:
    """Half smoothstep, half linear: drones accelerate gently out of a hub
    but don't fully stop on hubs they just pass through."""
    smooth = t * t * (3 - 2 * t)
    return 0.55 * smooth + 0.45 * t


class Timeline:
    """
    Snapshot `k` is the position of every drone after turn `k`
    (snapshot 0 = everyone on the start hub). A normal move completed in
    turn `k` is animated over [k-1, k]. Moving into a restricted zone takes
    two turns in the simulation (the drone is "in transit" during the first
    one), so it is animated over [k-2, k].
    """

    def __init__(
            self, graph: Graph, snapshots: list[dict[int, str]],
            drone_ids: list[int]
    ) -> None:
        self.graph = graph
        self.snapshots = snapshots
        self.drone_ids = drone_ids
        self.total_turns = len(snapshots) - 1
        self.flights: dict[int, list[Flight]] = {d: [] for d in drone_ids}
        self._build()

    def _build(self) -> None:
        raw: list[tuple[int, str, str, int, int]] = []
        for d in self.drone_ids:
            for k in range(1, len(self.snapshots)):
                a = self.snapshots[k - 1][d]
                b = self.snapshots[k][d]
                if a == b:
                    continue
                start = k - 1
                if self.graph.hubs[b].zone_type == "restricted":
                    start = max(0, k - 2)
                raw.append((d, a, b, start, k))

        groups: dict[tuple[str, str, int, int], list[int]] = {}
        for d, a, b, start, end in raw:
            groups.setdefault((a, b, start, end), []).append(d)

        for (a, b, start, end), ids in groups.items():
            ids.sort()
            n = len(ids)
            for i, d in enumerate(ids):
                self.flights[d].append(
                    Flight(d, a, b, float(start), float(end),
                           i - (n - 1) / 2)
                )
        for flights in self.flights.values():
            flights.sort(key=lambda f: f.start)

    def state(self, drone_id: int, t: float) -> DroneState:
        for f in self.flights[drone_id]:
            if f.start <= t < f.end:
                p = (t - f.start) / (f.end - f.start)
                return DroneState(drone_id, None, f, ease(p))
        idx = max(0, min(int(t), self.total_turns))
        return DroneState(drone_id, self.snapshots[idx][drone_id], None, 0.0)

    def next_flight(self, drone_id: int, t: float) -> Flight | None:
        for f in self.flights[drone_id]:
            if f.start >= t:
                return f
        return None

    def route_edges(self) -> set[frozenset[str]]:
        return {
            frozenset((f.src, f.dst))
            for flights in self.flights.values() for f in flights
        }
