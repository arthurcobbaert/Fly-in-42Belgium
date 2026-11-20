from src.parser.parsing import map_picker, Parser
from src.algorithm.pathfinder import Pathfinder
from src.algorithm.simulation import Simulation
from src.visualizer.visualizer import Visualizer
import sys
from pathlib import Path


def main() -> None:
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
        print(e)
        sys.exit(1)
    try:
        valid_lines = parse.parse_lines(data)
        graph = parse.parse_data(valid_lines)
    except Exception as e:
        print(e)
        sys.exit(1)

    path_finder = Pathfinder(graph)
    came_from = path_finder.dijkstra()
    paths = path_finder.enumerate_shortest_paths(came_from)
    for p in paths:
        print(p)

    drone_paths = {}
    for drone_id in range(graph.nb_drones):
        drone_paths[drone_id + 1] = paths[drone_id % len(paths)]
    simulation = Simulation(graph, drone_paths)
    events = simulation.sim()

    map_file = Path(map_path)
    pretty = map_file.stem.lstrip("0123456789_").replace("_", " ").title()
    viz = Visualizer(
        graph, events, drone_ids=list(drone_paths.keys()),
        seconds_per_turn=0.8,
        map_name=f"{map_file.parent.name.capitalize()} · {pretty}",
    )
    viz.run()


if __name__ == "__main__":
    main()
