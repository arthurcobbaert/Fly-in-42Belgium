from src.models.graph import Graph
from src.models.drone import Drone


class Simulation:

    def __init__(self, graph: Graph, drone_paths: dict[int, list[str]]):
        self.graph = graph
        self.drones = [
            Drone(id=id, path=path) for id, path in drone_paths.items()
        ]
        self.hub_occupancy = {name: 0 for name in graph.hubs}
        self.hub_occupancy[self.graph.start_hub] = self.graph.nb_drones
        self.turns = 0
        self.conn_occupancy = {
            tuple(sorted((conn.hub_a, conn.hub_b))): 0
            for conn in self.graph.connections
        }
        self.link_capacity = {
            tuple(sorted((conn.hub_a, conn.hub_b))): conn.max_link_capacity
            for conn in self.graph.connections
        }
        # print(f"Link capacity: ", self.link_capacity)

    def sim(self) -> list[dict[int, str]]:
        events = []
        while True:
            log = []
            completed = []
            self.turns += 1
            for drone in self.drones:
                if drone.status == "arrived":
                    continue
                result = None
                if drone.status == "in_transit":
                    drone.turns_left -= 1
                    if drone.turns_left == 0:
                        result, edges = self.complete_move(drone)
                        completed.append((drone.id, edges))
                elif drone.status == "waiting":
                    can_move = self.try_move(drone)
                    if can_move:
                        result, edges = self.complete_move(drone)
                        completed.append((drone.id, edges))
                    elif drone.status == "in_transit":
                        result = self.logging(drone, "wait")
                if result is not None:
                    log.append(result)
            # print(f"Hub occupancy: {drone.current_hub()}")
            if log:
                print(" ".join(log))
            for drone_id, edge_key in completed:
                self.conn_occupancy[edge_key] -= 1

            turn_snapshot = {
                drone.id: drone.current_hub() for drone in self.drones
            }
            events.append(turn_snapshot)
            # if completed:
            #    self.update_conn(completed)
            if all(drone.status == "arrived" for drone in self.drones):
                print(f"Turns: {self.turns}")
                return events

    def try_move(self, drone: Drone) -> bool | None:
        next_hub_name = drone.next_hub()
        if next_hub_name is None:
            return False
        next_hub = self.graph.hubs[next_hub_name]
        edges = tuple(sorted((drone.current_hub(), next_hub_name)))
        if (
                next_hub_name == self.graph.end_hub or
                self.hub_occupancy[next_hub_name] < next_hub.max_drones
                and self.conn_occupancy[edges] < self.link_capacity[edges]
        ):
            self.conn_occupancy[edges] += 1
            self.hub_occupancy[next_hub_name] += 1
            if next_hub.zone_type == "restricted":
                drone.turns_left = 1
                drone.status = "in_transit"
#                return self.logging(drone, "wait")
                return False
            else:
                # result, edges = self.complete_move(drone)
                # return result, edges
                return True
        return None

    def complete_move(self, drone: Drone) -> tuple[str, tuple[str, str]]:
        old_hub = drone.current_hub()
        self.hub_occupancy[old_hub] -= 1
        drone.position += 1
        if drone.current_hub() == drone.path[-1]:
            drone.status = "arrived"
        else:
            drone.status = "waiting"
        return (
            self.logging(drone, "move"),
            (min((old_hub, drone.current_hub())),
             max(old_hub, drone.current_hub()))
        )

    def logging(self, drone: Drone, action: str) -> str:
        if action == "move":
            return f"D{drone.id}-{drone.path[drone.position]}"
        elif action == "wait":
            hub_a = drone.current_hub()
            hub_b = drone.next_hub()
            return f"D{drone.id}-{hub_a}-{hub_b}"
        return ""
