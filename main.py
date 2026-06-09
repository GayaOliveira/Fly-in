from errors import ParseError
from file_loader import FileLoader
from parser import Parser
from gui import GrafoApp

if __name__ == "__main__":
    try:
        loader = FileLoader("03_priority_puzzle.txt")
        raw = loader.get_config()

        parser = Parser(raw)
        data = parser.parse()

        app = GrafoApp(data)
        app.mainloop()

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

    except ParseError as error:
        print(f"\033[31mError: {error}\033[m")
