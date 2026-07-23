from errors import ParseError
from file_loader import FileLoader
from parser import Parser
from entity import Graph
from pathfinder import A_star
from planner import Planner
from gui import SimulationWindow

import sys


if __name__ == "__main__":
    try:
        loader = FileLoader(sys.argv[1])
        raw = loader.get_config()

        parser = Parser(raw)
        data = parser.parse()

        graph = Graph.from_parsed(data)

        pathfinder = A_star(graph)

        planner = Planner(pathfinder, graph.drones)
        paths = planner.find_paths()

        app = SimulationWindow(graph, paths)
        app.mainloop()

    except ParseError as error:
        print(f"\033[31mError: {error}\033[m")

    except ParseError as error:
        print(f"\033[31mError: {error}\033[m")
