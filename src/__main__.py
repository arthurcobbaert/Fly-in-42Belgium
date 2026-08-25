from src.parser.parsing import map_picker, Parser
from src.algorithm.pathfinder import Pathfinder
from src.algorithm.simulation import Simulation
from src.visualizer.visualizer import Visualizer
import sys


def main():
    map_path = map_picker()
    parse = Parser()
    data: list[str] = []
    valid_lines: list[str] = []
    try:
        with open(map_path) as f:
            for line in f:
                if not line:
                    continue
                data.append(line)
    except (FileNotFoundError, PermissionError) as e:
        sys.exit(e)
    try:
        valid_lines = parse.parse_lines(data)
        graph = parse.parse_data(valid_lines)
    except Exception as e:
        sys.exit(e)

    path_finder = Pathfinder(graph)
    came_from, distances = path_finder.dijkstra()

    if distances[graph.end_hub] == float('inf'):
        sys.exit("No path found between start_hub and end_hub.")

    paths = path_finder.enumerate_shortest_paths(came_from)
    for p in paths:
        print(p)

    drone_paths = {}
    for drone_id in range(graph.nb_drones):
        drone_paths[drone_id + 1] = paths[drone_id % len(paths)]
    simulation = Simulation(graph, drone_paths)
    events = simulation.sim()

    viz = Visualizer(
        graph, events, drone_ids=list(drone_paths.keys()), seconds_per_turn=0.8
    )
    viz.run()


if __name__ == "__main__":
    main()
