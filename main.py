from errors import ParseError
from file_loader import FileLoader
from parser import Parser
from gui import GrafoApp
from entity import Map, Drone
from dijkstra import Dijkstra

if __name__ == "__main__":
    try:
        loader = FileLoader("03_priority_puzzle.txt")
        raw = loader.get_config()

        parser = Parser(raw)
        data = parser.parse()

        map_obj = Map.from_parsed(data)

        Dijkstra(map_obj).move_drone(Drone((0, 0)))

        # print("nb_drones =>", data["nb_drones"])

        # print()

        # for element in data["hubs"]:
        #     print(element)

        # print()

        # for element in data["connections"]:
        #     print(
        #         f"{element.hub_pair[0].name}-{element.hub_pair[1].name} "
        #         f"max_link_capacity = {element.max_link_capacity}"
        #         )

        app = GrafoApp(data)
        app.mainloop()

    except ParseError as error:
        print(f"\033[31mError: {error}\033[m")
