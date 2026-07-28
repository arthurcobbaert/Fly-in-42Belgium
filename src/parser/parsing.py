import argparse
from src.models.hubs import Hub
from src.models.graph import Graph
from typing import Any

VALID_HUBS = ["start_hub:", "hub:", "end_hub:"]
VALID_CONNECTION = ["connection:"]
VALID_METADATA_HUB = ["zone", "color", "max_drones"]

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
        self.nb_drones: int = 0
        self.hubs: list[str] = []

    def parse_lines(self, map_data: list[str]) -> list[str]:
        nb_drones: int = 0
        hubs: list[str] = []
        connect: list[str] = []
        valid_lines: list[str] = []
        for line in map_data:
            if line.startswith('#') or line == '\n':
                continue
            splitted = line.split(' ')
            if line.startswith('nb_drones:'):
                if nb_drones == 0 and len(splitted) == 2:
                    try:
                        x = int(splitted[1])
                        if x < 1:
                            raise Exception(
                                f"ERROR: Number of drones should be a positive nummber."
                            )
                        self.nb_drones = x
                    except ValueError:
                        raise Exception(
                            f"Data assigned to line '{line}' is not valid...\n"
                            "ERROR: Number of drones should be an int."
                        )
                    valid_lines.append(line.strip('\n'))
                    nb_drones = 1
                    continue
                else:
                    raise Exception(
                    f"Data assign to line '{line}' is not valid..."
                )
            if splitted[0] in VALID_HUBS:
                if not 4 <= len(splitted) <= 7:
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
                    valid_lines.append(line.strip('\n'))
                    hubs.append(splitted[0])
            elif splitted[0] in VALID_CONNECTION:
                if not 2 <= len(splitted) <= 3 :
                    raise Exception(
                        f"Data assigned to line {line} is not valid..."
                        "ERROR: Connection is wrong."
                    )
                valid_lines.append(line.strip('\n')) 
            else:
                raise Exception(
                    f"Data assigned to line {line} is not valid..."
                    "ERROR: You have to assign a 'VALID_HUB' or 'VALID_CONNECTION'."
                )
        if not "start_hub:" in hubs or not "end_hub:" in hubs:
            raise Exception(
                f"ERROR: You should provide a 'start_hub' and 'end_hub'."
            )
        self.hubs = hubs
        if self.nb_drones == 0:
            raise Exception(
                f"ERROR: Number of drones was not provided..."
            )
        #print(f"Valid lines: {valid_lines}")
        return valid_lines

    def parse_data(self, valid_lines: list[str]):
        splitted: list[str] = []
        hub_name_checker: list[str] = []
        metadata_dict: dict[str, str] = {}
        hubs = {}

        for line in valid_lines:
            splitted = line.split()
            if splitted[0] in VALID_HUBS:
                try:
                    a = int(splitted[2])
                    b = int(splitted[3])
                except ValueError:
                    raise Exception(
                        f"Data assigned to line '{line}' is not valid...\n"
                        "ERROR: You should provide valid integers for the hub coordinates."
                    )
                if splitted[1] in hub_name_checker:
                    raise Exception(
                        f"Data assigned to line '{line}' is not valid...\n"
                        "ERROR: You should provide different names for each hub."
                    )
                hub_name_checker.append(str(splitted[1]))
                if len(splitted) > 4:
                    try:
                        metadata_dict = self.parse_metadata(splitted[4:], "hub")
                    except Exception as e:
                        raise Exception(e)
                hub = Hub(
                    hub_type=splitted[0].rstrip(':'),
                    name=splitted[1],
                    x=a,
                    y=b,
                    color=metadata_dict.get('color', 'blue'),
                    zone_type=metadata_dict.get('zone', 'normal'),
                    max_drones=int(metadata_dict.get('max_drones', 1)),
                )
                hubs[hub.name] = hub
                
                if hub.hub_type == "start_hub":
                    start_hub_name = hub.name
                elif hub.hub_type == "end_hub":
                    end_hub_name = hub.name
            elif splitted[0] in VALID_CONNECTION:
                if len(splitted) > 2:
                    try:
                        metadata_dict = self.parse_metadata(splitted[2:], "connection")
                    except Exception as e:
                        raise Exception(e)


        return Graph(
            nb_drones = self.nb_drones,
            start_hub = start_hub_name,
            end_hub = end_hub_name,
            hubs = hubs,
            connections = [],
        )

    def parse_metadata(self, metadata: list[str], kind: str):
        joined: str = ""
        result: dict[str, str] = {} 
        
        joined = " ".join(metadata)
        if not joined.startswith('[') or not joined.endswith(']'):
            raise Exception(
                f"Data assigned to {metadata} is not valid..."
                "ERROR: The metadata provided is not correct."
            )
        cleaned = joined[1:-1]
        splitted = cleaned.split()
        for i in splitted:
            if i.count('=') != 1:
                raise Exception(
                    f"ERROR: You should provide an equal sign in '{metadata}'."
                )
            key, value = i.split('=')
            if kind == "hub":
                if key not in VALID_METADATA_HUB:
                    raise Exception(
                        f"ERROR: You should provide valid metadata."
                    )
                if key in result:
                    raise Exception(
                        f"ERROR: Duplicate metadata."
                    )
                if key == "zone":
                    valid = ["restricted", "blocked", "priority"]
                    if value not in valid:
                        raise Exception(
                            f"ERROR: Value provided in the metadata is not allowed."
                        )
                elif key == "max_drones":
                    try:
                        x = int(value)
                        if x < 1:
                            raise Exception(
                                "ERROR: Max drones should be a positive integer."
                          )
                    except ValueError:
                        raise Exception(
                            "ERROR: Max drones should be a positivei integer."
                        )
                result[key] = value
            elif kind == "connection":
                if key != "max_link_capacity":
                    raise Exception(
                        f"ERROR: Wrong metadata provided in '{metadata}'."
                    )
                try:
                    x = int(value)
                    if x < 1:
                        raise Exception(
                            f"ERROR: Max_link_capacity should receive a positive number as value."
                        )
                except ValueError:
                    raise Exception(
                        f"ERROR: A number should be provided as value in '{metadata}'."
                    )
                result[key] = value
        return result

## We have to first extract the information from the files in maps...

## Find a way to parse the data in a correct way and manage to store the data in the best way possible.

## This part should be made with try-except blocks so when something goes wrong exit the program without crashing.

## Organize the data in class models so we can visualize clearly whats happening and then it will be easier to implement the algo.

