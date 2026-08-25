from src.models.connections import Connection
from src.models.hubs import Hub
from dataclasses import dataclass


@dataclass
class Graph:
    nb_drones: int
    start_hub: str
    end_hub: str
    hubs: dict[str, Hub]
    connections:  list[Connection]
