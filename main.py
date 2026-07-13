from errors import ParseError
from file_loader import FileLoader
from parser import Parser
from entity import Graph
from pathfinder import Dijkstra
from planner import Planner
# from simulation import Simulator
from gui import GraphApp

from rich import print

if __name__ == "__main__":
    try:
        loader = FileLoader("01_the_impossible_dream.txt")
        raw = loader.get_config()

        parser = Parser(raw)
        data = parser.parse()

        graph = Graph.from_parsed(data)

        pathfinder = Dijkstra(graph)

        planner = Planner(pathfinder, graph.drones)
        paths = planner.find_paths()

        # print(paths)

        # simulator = Simulator(graph)
        # simulator.simulate(multi_agent_pathfinder)

        app = GraphApp(graph, paths=paths)
        app.mainloop()

    except ParseError as error:
        print(f"\033[31mError: {error}\033[m")

    except ParseError as error:
        print(f"\033[31mError: {error}\033[m")
