from dataclasses import dataclass


@dataclass
class Hub:

    hub_type: str
    name: str
    x: int
    y: int
    color: str | None
    zone_type: str
    max_drones: int
