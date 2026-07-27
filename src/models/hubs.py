from dataclasses import dataclass


@dataclass
class Hub:

    hub_type: str
    name: str
    x: int
    y: int
    color: str | None = None
    zone_type: str = "normal"
    max_drones: int = 1
