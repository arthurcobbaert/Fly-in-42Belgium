from src.parser.parsing import map_picker, Parser
from src.algorithm.pathfinder import Pathfinder
from src.algorithm.simulation import Simulation
import sys

def main():
    args = map_picker()
    parse = Parser()
    data: list[str] = []
    valid_lines: list[str] = []
    try:
        with open(args.input) as f:
            for l in f:
                if not l:
                    continue
                data.append(l)
    except (FileNotFoundError, PermissionError) as e:
        sys.exit(e)
    try:
        valid_lines = parse.parse_lines(data)
        graph = parse.parse_data(valid_lines)
    except Exception as e:
        sys.exit(e)

    path_finder = Pathfinder(graph)
    came_from, distances = path_finder.dijkstra()
    paths = path_finder.enumerate_shortest_paths(came_from)
    print(f"PATHS: {paths}")

    drone_paths = {}
    for drone_id in range(graph.nb_drones):
        drone_paths[drone_id + 1] = paths[drone_id % len(paths)]
    simulation = Simulation(graph, drone_paths)
    simulation.sim()
if __name__ == "__main__":
    main()
