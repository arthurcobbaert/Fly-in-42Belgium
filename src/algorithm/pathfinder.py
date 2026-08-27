from src.models.graph import Graph
from typing import Any
import heapq


class Pathfinder:

    def __init__(self, graph: Graph):
        self.graph = graph
        self.neighbors = self.build_neighbors()

    def get_cost(self, hub_name: str) -> int:
        # Return cost of moving to a certain hub and returns an int with cost
        if self.graph.hubs[hub_name].zone_type in ("normal", "priority"):
            return 1
        elif self.graph.hubs[hub_name].zone_type == "restricted":
            return 2
        else:
            return 99999

    def build_neighbors(self) -> dict:
        # Make a hashmap of which hubs are adjacent to eah hub
        neighbors: dict[str, Any] = {}

        # loops through the hubs creating key for each hub name we have.
        for key in self.graph.hubs:
            neighbors[key] = []

        for conn in self.graph.connections:
            hub_a = self.graph.hubs[conn.hub_a]
            hub_b = self.graph.hubs[conn.hub_b]

            # If its not blocked we append it to the list attatched to the key.
            if hub_a.zone_type != "blocked":
                neighbors[conn.hub_a].append(conn.hub_b)
            if hub_b.zone_type != "blocked":
                neighbors[conn.hub_b].append(conn.hub_a)
        return neighbors

    def dijkstra(self) -> dict[str, list[str]]:
        start_hub: str = self.graph.start_hub
        came_from: dict[str, list[str]] = {}
        visited = []
        distances: dict[str, Any] = {}
        for name in self.graph.hubs:
            if name == start_hub:
                distances[name] = 0
            else:
                distances[name] = float('inf')

        pq = [(0, start_hub)]
        while pq:
            cost, current = heapq.heappop(pq)
            if current in visited:
                continue
            visited.append(current)
            for neighbor in self.neighbors[current]:
                new_dist = cost + self.get_cost(neighbor)
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    came_from[neighbor] = [current]
                    heapq.heappush(pq, (new_dist, neighbor))
                elif new_dist == distances[neighbor]:
                    if current not in came_from.get(neighbor, []):
                        came_from[neighbor].append(current)
                        heapq.heappush(pq, (new_dist, neighbor))
        return came_from

    def enumerate_shortest_paths(
            self,
            came_from: dict[str, list[str]]
    ) -> list[list[str]]:
        start_hub = self.graph.start_hub
        end_hub = self.graph.end_hub
        paths: list[list[str]] = []

        def backtrack(current: str, path_so_far: list[str]) -> None:
            if current == start_hub:
                paths.append([start_hub] + path_so_far[::-1])
                return
            for predecessor in came_from.get(current, []):
                backtrack(predecessor, path_so_far + [current])

        backtrack(end_hub, [])
        paths.sort(key=self.path_priority_score, reverse=True)
        return paths

    def path_priority_score(self, path: list[str]) -> int:
        return sum(
            1 for hub_name in path
            if self.graph.hubs[hub_name].zone_type == "priority"
        )
