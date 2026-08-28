*This project has been created as part of the 42 curriculum by <acobbaer>.*

# Fly-in

## Description

Fly-in is a drone traffic simulation project developed as part of the 42 curriculum.

The program simulates multiple drones travelling through a network of hubs and connections. Each drone follows a calculated path while respecting hub 
capacities, connection capacities, and restricted zones.

The goal is to find efficient routes for the drones and simulate their movement through the network without exceeding the available capacities.

## Algorithm

The project uses a **weighted Dijkstra algorithm** to calculate the routes taken by the drones.

Unlike a standard Dijkstra algorithm where each connection has a fixed cost, the project dynamically calculates the cost of travelling through the graph. The weight takes the current state of the network into account, such as:

* Connection capacity and current occupancy.
* Hub capacity and current occupancy.
* Restricted zones.
* The distance or cost associated with travelling between hubs.

Dijkstra's algorithm is used to find the shortest valid path from the starting hub to the destination. After finding a path, the graph can be
evaluated again with updated weights to find additional paths. This allows the simulation to use **one or multiple paths** depending on the network
and drone traffic.

The calculated paths are then assigned to drones and used by the simulation engine.

## Implementation Strategy

The project is divided into several components:

* **Parser** — Reads and validates the input file and creates the graph.
* **Models** — Represents hubs, connections, drones, and the graph.
* **Pathfinding** — Uses weighted Dijkstra to find efficient paths through the graph.
* **Simulation** — Handles drone movement, occupancy, restrictions, and turn management.
* **Visualizer** — Displays the graph and animates drone movements using Pygame.

The simulation uses dictionaries to track hub and connection occupancy, allowing fast capacity checks during each turn.

Each drone follows its assigned path. At every turn, the simulation checks whether the next hub and connection have available capacity before allowing the drone to move. Occupancy is updated as drones enter and leave hubs and connections.

## Visualization

The project includes a Pygame-based visualizer that displays:

* Hubs and their zones.
* Connections between hubs.
* Drone positions and movements.
* Current simulation turn.
* Playing/paused state.
* Simulation speed.
* A legend for different hub zones.

The visualization provides a real-time representation of the simulation, making it easier to understand the calculated routes, drone traffic, capacity constraints, and overall behaviour of the algorithm.

## Instructions

### Requirements

* Python 3.13+
* `uv`
* Pygame

### Installation

Clone the repository and install the dependencies:

```bash
uv sync
```

### Run

Run the project with:

```bash
uv run python -m src
```

The visualizer allows the simulation to be paused, resumed, stepped through turn by turn, and sped up or slowed down.

### Type Checking

Run mypy with:

```bash
uv run mypy src
```

## Example

Example input:

```text
nb_drones: 2
start: A
end: D

A-B
B-C
C-D
```

The pathfinding algorithm can calculate routes such as:

```text
Drone 0: A → B → C → D
Drone 1: A → B → C → D
```

The simulation then schedules their movements according to hub and connection capacities.

Example output:

```text
D0-B D1-B
D0-C D1-C
D0-D D1-D
Turns: 3
```

The exact output depends on the graph structure, calculated path weights, drone paths, capacities, and zone restrictions.

## Resources

### Documentation

* Dijkstra documentation: https://www.w3schools.com/dsa dsa_algo_graphs_dijkstra.php
* Python documentation: https://docs.python.org/3/
* Pygame documentation: https://www.pygame.org/docs/
* `uv` documentation: https://docs.astral.sh/uv/

### AI Usage

AI tools were used as a development aid for:

* Understanding and debugging Python type annotations and mypy errors.
* Discussing and refining the weighted Dijkstra implementation.
* Reviewing algorithm and implementation choices.
* Improving code structure and readability.
* Assisting with README documentation.

The final implementation, algorithmic decisions, testing, and integration were performed and reviewed by the project authors.
