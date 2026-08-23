from src.models.graph import Graph
from src.models.drone import Drone



class Simulation:

    def __init__(self, graph: Graph, drone_paths: dict[int, list[str]]):
        self.graph = graph
        self.drones = [Drone(id=id, path=path) for id, path in drone_paths.items()]
        self.hub_occupancy = {name: 0 for name in graph.hubs}
        self.turns = 0
        self.conn_occupancy = {tuple(sorted((conn.hub_a, conn.hub_b))): 0 for conn in self.graph.connections}
        self.link_capacity = {tuple(sorted((conn.hub_a, conn.hub_b))): conn.max_link_capacity for conn in self.graph.connections}
        print(self.link_capacity)
        print(self.conn_occupancy)


    def sim(self):
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
                        completed.append(edges)
                elif drone.status == "waiting":
                    can_move = self.try_move(drone)
                    if can_move:
                        result, edges = self.complete_move(drone)
                        completed.append(edges)
                if result is not None:
                    log.append(result)
            #print(f"Connection occupancy: ", completed)
            print(f"Connection occupancy: ", self.conn_occupancy)
            if log:
                print(" ".join(log))
            for hubs in completed:
                self.conn_occupancy[hubs] -= 1
            #if completed:
            #    self.update_conn(completed)
            if all(drone.status == "arrived" for drone in self.drones):
                print(f"Turns: {self.turns}")
                return

    def try_move(self, drone: Drone):
        next_hub_name = drone.next_hub()
        next_hub = self.graph.hubs[next_hub_name]
        edges = tuple(sorted((drone.current_hub(), drone.next_hub())))
        if next_hub_name == self.graph.end_hub or self.hub_occupancy[next_hub_name] < next_hub.max_drones and self.conn_occupancy[edges] < self.link_capacity[edges]:
            self.conn_occupancy[edges] += 1
            self.hub_occupancy[next_hub_name] += 1
            if next_hub.zone_type == "restricted":
                drone.turns_left = 1
                drone.status = "in_transit"
#                return self.logging(drone, "wait")
                return False
            else:
                #result, edges = self.complete_move(drone)
                #return result, edges
                return True

    def complete_move(self, drone: Drone):
        old_hub = drone.current_hub()
        self.hub_occupancy[old_hub] -= 1
        drone.position += 1
        if drone.current_hub() == drone.path[-1]:
            drone.status = "arrived"
        else:
            drone.status = "waiting"
        return self.logging(drone, "move"), tuple(sorted((old_hub, drone.current_hub())))


    def logging(self, drone: Drone, action: str) -> str:
        if action == "move":
            return f"D{drone.id}-{drone.path[drone.position]}"
        elif action == "wait":
            hub_a = drone.current_hub()
            hub_b = drone.next_hub()
            return f"D{drone.id}-{hub_a}-{hub_b}"

#We have to figure out the drones scheduling.

#The first drone will always follow the base path, whoch is the first one we find with dijkstra...

#But if we have multiple paths that are as shprt as the shortest path we should also use them...

#We have to figure out some functions to be able to spread these drones in that case.

# 1. We already found the first path using the dijkstra we implemented

# 2. Maybe the most efficient way is to figure out if we already have other paths which are as short as the one we found first.

# 3. After we have this information we start the simulation.

# 4. If we have multiple shortest paths we give one path to each drone in order so that they do not end up in the same place.

# 5. Create function to check if we are able to make turn or not depending on the next hub it should get into.

# 6. If its true th drone should move to the next hub, else he should wait.

# 7. We will also create a tie breaker rule, so if 2 drones are looking to move into the same hub the one with the smallest dron_id always win.

   
