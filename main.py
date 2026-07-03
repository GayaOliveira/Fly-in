from cbs import CBS
from errors import ParseError
from file_loader import FileLoader
from parser import Parser
# from gui import GraphApp
from entity import Graph
from pathfinder import Dijkstra
from simulation import Simulator

if __name__ == "__main__":
    try:
        loader = FileLoader("03_ultimate_challenge.txt")
        raw = loader.get_config()

        parser = Parser(raw)
        data = parser.parse()

        graph = Graph.from_parsed(data)

        pathfinder = Dijkstra()
        multi_agent_pathfinder = CBS(pathfinder)

        simulator = Simulator(graph)
        simulator.simulate(multi_agent_pathfinder)

        # app = GraphApp(graph, path)
        # app.mainloop()

    except ParseError as error:
        print(f"\033[31mError: {error}\033[m")
