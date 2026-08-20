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
    path = path_finder.dijkstra()
    simulation = Simulation(graph, path)
    simulation.sim()
if __name__ == "__main__":
    main()
