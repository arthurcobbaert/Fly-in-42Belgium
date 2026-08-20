from dataclasses import dataclass


@dataclass
class Drone:
    id: int
    path: list[str]
    position: int = 0
    status: str = "waiting"
    turns_left: int = 0

    def current_hub(self) -> str:
        return self.path[self.position]

    def next_hub(self) -> str | None:
        if self.position + 1 < len(self.path):
            return self.path[self.position + 1]
        return None

    def is_arrived(self) -> bool:
        return self.status == "arrived"
