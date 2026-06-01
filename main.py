from file_loader import FileLoader
from parser import Parser

if __name__ == "__main__":

    loader = FileLoader("03_priority_puzzle.txt")
    raw = loader.get_config()

    parser = Parser(raw)
    data = parser.parse()
    print(data)
