from src.models.graph import Graph
from src.models.hubs import Hub 
import heapq
import sys

class Pathfinder:

    def __init__(self, graph: Graph):
        self.graph = graph
        self.neighbors = self.build_neighbors()

    def get_cost(self, hub_name) -> int:
        # Return cost of moving to a certain hub and returns an int with cost
        if self.graph.hubs[hub_name].zone_type in ("normal", "priority"):
            return 1
        elif self.graph.hubs[hub_name].zone_type == "restricted":
            return 2
        else:
            sys.exit("Unexpected zone_type.")


    def build_neighbors(self) -> dict:
        # Make a hashmap of which hubs are adjacent to eah hub
        neighbors: dict[str, str] = {}

        #loops through the hubs creating key for each hub name we have.
        for key in self.graph.hubs:
            neighbors[key] = []

        for conn in self.graph.connections:
            #First we are extracting the hub information to make sure we do not have blocked zone types.
            hub_a = self.graph.hubs[conn.hub_a]
            hub_b = self.graph.hubs[conn.hub_b]

            #If its not blocked we append it to the list attatched to the key.
            if hub_a.zone_type != "blocked":
                neighbors[conn.hub_a].append(conn.hub_b)
            if hub_b.zone_type != "blocked":
                neighbors[conn.hub_b].append(conn.hub_a)
        return neighbors


    def dijkstra(self):
        #We define the start and end hub to set where we start and end our operation.
        start_hub: str = self.graph.start_hub
        end_hub: str = self.graph.end_hub

        came_from: dict[str, list[str]] = {} 

        #We have to make an array to keep track of which hubs we have already visted, as we begin from start hub its the first one we put inside.
        visited = []

        #we need to keep track of the distances to reach each hub from the beggining and figure out the logic to keep always the shortest distance.
        distances = {}
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
            #if current == end_hub:
            #    return self.reconstruct_path(came_from, end_hub, start_hub)

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
        return came_from, distances

    def enumerate_shortest_paths(self, came_from: dict[str, list[str]]) -> list[list[str]]:
        start_hub = self.graph.start_hub
        end_hub = self.graph.end_hub
        paths: list[list[str]] = []

        def backtrack(current: str, path_so_far: list[str]):
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


    def reconstruct_path(self, came_from: dict[str, str], end: str, start: str) -> list[str]:
        drone_paths = {}
        path = [end]
        while path[-1] != start:
            path.append(came_from[path[-1]])
        i = 1
        while i <= self.graph.nb_drones:
            drone_paths[i] = path[::-1]
            i += 1
        return drone_paths

    
