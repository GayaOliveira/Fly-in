from errors import ParseError
from file_loader import FileLoader
from parser import Parser

if __name__ == "__main__":
    try:
        loader = FileLoader("03_priority_puzzle.txt")
        raw = loader.get_config()

        parser = Parser(raw)
        data = parser.parse()

        print("nb_drones =>", data["nb_drones"])

        for element in data["graph_elements"]:
            print(element)

    except ParseError as error:
        print(f"\033[31mError: {error}\033[m")
