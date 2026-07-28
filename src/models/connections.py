from dataclasses import dataclass


@dataclass
class Connection:

    hub_a: str
    hub_b: str
    max_link_capacity: int | None = None
