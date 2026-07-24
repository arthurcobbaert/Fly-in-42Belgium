import argparse
from typing import Any

VALID_HUBS = ["start_hub:", "hub:", "end_hub:"]
VALID_CONNECTION = "connection:"
def map_picker():
    parser = argparse.ArgumentParser(
        description="Fly-in: Implementation of pathfinder with the least number of turns"
    )

    parser.add_argument(
        "--input",
        default="maps/easy/01_linear_path.txt",
        help="Default map for program execution",
    )
    return parser.parse_args()

class Parser:

    def __init__(self):
        self.corrected_data = {} 

    def parse_lines(self, map_data: list[str]):
        nb_drones: int = 0
        hubs: list[str] = []
        connect: list[str] = []
        splitted: list[str] = []
        for line in map_data:
            if line.startswith('#') or line == '\n':
                continue
            splitted = line.split(' ')
            if splitted[0] in VALID_HUBS:
                if not 4 <= len(splitted) <= 5 :
                    raise Exception(
                        f"Data assigned to line {line} is not valid..."
                    )
                if splitted[0] == "start_hub:" and splitted[0] in hubs:
                    raise Exception(
                        f"Data assigned to line '{line}' is not valid...\n"
                        "ERROR: You can assign only 1 start_hub."
                    )
                elif splitted[0] == "end_hub:" and splitted[0] in hubs:
                    raise Exception(
                        f"Data assigned to line '{line}' is not valid...\n"
                        "ERROR: You can assign only 1 end_hub."
                    )
                else:
                    hubs.append(splitted[0])
            elif splitted[0] in VALID_CONNECTION:
                if not 2 <= len(splitted) <= 3 :
                    raise Exception(
                        f"Data assigned to line {line} is not valid..."
                    )
                connect.append(splitted[0])
            else:
                raise Exception(
                    f"Data assigned to line {line} is not valid..."
                )
        print(f"Hubs: {hubs}")
        print(f"Connections: {connect}")

        



## We have to first extract the information from the files in maps...

## Find a way to parse the data in a correct way and manage to store the data in the best way possible.

## This part should be made with try-except blocks so when something goes wrong exit the program without crashing.

## Organize the data in class models so we can visualize clearly whats happening and then it will be easier to implement the algo.

