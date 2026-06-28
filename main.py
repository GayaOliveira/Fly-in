from errors import ParseError
from file_loader import FileLoader
from parser import Parser
from gui import GraphApp
from entity import Graph, Drone
from dijkstra import Dijkstra

if __name__ == "__main__":
    try:
        loader = FileLoader("03_priority_puzzle.txt")
        raw = loader.get_config()

        parser = Parser(raw)
        data = parser.parse()

        graph = Graph.from_parsed(data)

        Dijkstra(graph).move_drone(Drone((0, 0)))
        path = Dijkstra(graph).dijkstra()[1]

        app = GraphApp(graph, path)
        app.mainloop()

    except ParseError as error:
        print(f"\033[31mError: {error}\033[m")
