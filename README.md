*This project has been created as part of the 42 curriculum by jbrits-m*

# Description

Multi-Agent Drone Path Planning is a Python application that simulates the navigation of multiple drones through a weighted graph while avoiding conflicts over shared resources. The project focuses on solving the **Multi-Agent Path Finding (MAPF)** problem by combining the **A\*** search algorithm with the **Prioritized Planning** strategy.

Each drone is assigned a priority and computes its path individually. Once a path has been planned, the occupied vertices and edges are reserved in time, forcing subsequent drones to generate conflict-free routes. The result is a complete schedule that guarantees collision-free navigation while maintaining a relatively simple and efficient planning process.

To improve the understanding of the generated solution, the project also provides an interactive graphical simulation built with **CustomTkinter**. The interface allows users to inspect the graph, visualize each drone's movement over time, monitor edge occupancy, and navigate through every simulation turn.


# Features

- Multi-agent path planning
- A* pathfinding algorithm
- Prioritized Planning strategy
- Time-aware collision avoidance
- Weighted graph support
- Interactive graphical simulation
- Turn-by-turn playback controls
- Visualization of drone positions and edge occupancy
- Object-oriented architecture with clear separation between planning logic and graphical interface


# Project Architecture

The project is divided into two independent layers.

## Backend

The backend is responsible for every computational aspect of the simulation.

It includes:

- Configuration loading
- Input parsing
- Graph construction
- A* pathfinding
- Prioritized Planning
- Conflict resolution
- Simulation timeline generation

The backend is completely independent of the graphical interface.


## Frontend

The frontend is responsible only for visualization.

Its responsibilities include:

- Rendering the graph
- Displaying drone movements
- User interaction
- Playback controls
- Simulation inspection

The GUI does not perform any pathfinding or planning operations.


# Algorithm

## A* Search

Each drone computes its individual path using the A* algorithm.

The heuristic estimates the remaining cost between the current node and the destination, allowing the search to prioritize promising routes while still guaranteeing an optimal solution whenever the heuristic is admissible.

The implementation considers:

- Weighted edges
- Graph topology
- Travel costs


## Prioritized Planning

Instead of planning all drones simultaneously, the project adopts the Prioritized Planning strategy.

The process follows these steps:

1. Sort drones according to a predefined priority.
2. Plan the highest-priority drone using A*.
3. Reserve every occupied vertex and traversed edge for each time step.
4. Plan the next drone while respecting all previous reservations.
5. Repeat until every drone has been scheduled.

This approach significantly reduces computational complexity compared to optimal MAPF algorithms while still producing collision-free solutions for a wide range of scenarios.

Although Prioritized Planning does not always produce globally optimal solutions, it offers an excellent trade-off between implementation complexity and execution time.


# Visualization

The simulation interface was designed to make the planning process easier to understand.

The visualization includes:

- Graph rendering
- Drone animation
- Current simulation turn
- Occupied connections
- Hub inspection
- Playback controls
- Turn-by-turn navigation

Users can pause the simulation, inspect graph elements, and move freely through the generated timeline, making it easier to understand how reservations affect each drone's path.

The frontend follows an object-oriented architecture composed of specialized components such as:

- `SimulationWindow`
- `SimulationController`
- `SimulationState`
- `SimulationModel`
- `TurnSnapshot`
- `GraphRenderer`
- `GraphInspector`
- `CoordinateMapper`

This separation keeps the visualization independent from the planning algorithms and improves maintainability.


# Instructions

## Requirements

- Python 3.11 or newer
- CustomTkinter

Install the required dependency:

```bash
pip install customtkinter
```


## Running

Execute the project with:

```bash
python main.py
```

The application will:

1. Load the input file.
2. Parse the graph description.
3. Build the graph.
4. Compute collision-free paths using A* and Prioritized Planning.
5. Launch the graphical simulation.


# Input Format

Example:

```text
HUBS
A (0,0)
B (2,0)
C (2,2)
D (0,2)

CONNECTIONS
A B 2
B C 1
C D 2
A D 3

DRONES
Drone1 A -> C
Drone2 D -> B
```


# Expected Output

Console:

```text
Planning completed successfully.

Drone1:
A -> B -> C

Drone2:
D -> A -> B
```

Graphical simulation:

- Graph visualization
- Drone movement over time
- Edge occupancy visualization
- Turn navigation
- Playback controls
- Inspection of graph elements


# Design Decisions

Several architectural decisions were made during development to improve maintainability and readability.

## Separation of Responsibilities

The project separates planning from visualization.

The backend computes the complete simulation before the GUI is created.

The frontend only consumes the generated paths.


## Object-Oriented Design

The graphical interface follows the **Single Responsibility Principle**.

Each component performs one well-defined task.

Examples include:

- Rendering
- Hit detection
- Coordinate mapping
- State management
- Playback control

This organization greatly simplifies future extensions and maintenance.


## Time-Based Simulation

Instead of animating directly from the generated paths, the planner produces a sequence of simulation states.

Each state represents one simulation turn, allowing deterministic playback, inspection, and debugging.


# Resources

## Multi-Agent Path Finding

- Koenig, S., Sharon, G., & Likhachev, M. — *Multi-Agent Path Finding: Definitions, Variants, and Benchmarks*
- Dechter, R., & Pearl, J. — *Generalized Best-First Search Strategies and the Optimality of A\**
- Russell, S., & Norvig, P. — *Artificial Intelligence: A Modern Approach*
- Silver, D. — *Cooperative Pathfinding*
- Amit Patel — *A* Pathfinding for Beginners (Red Blob Games)*

## Python

- Python Official Documentation
- CustomTkinter Documentation


# Artificial Intelligence Usage

Artificial Intelligence was used exclusively as a development assistant.

Its contributions included:

- Discussing software architecture
- Reviewing object-oriented design
- Refactoring the graphical interface
- Suggesting class responsibilities
- Improving code organization
- Generating documentation
- Reviewing technical writing

The planning algorithms, data structures, application logic, and final implementation decisions were designed, implemented, tested, and validated by the author.