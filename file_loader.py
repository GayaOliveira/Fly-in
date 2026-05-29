from errors import ParseError


class FileLoader:
    """
    """
    def __init__(self, file_name: str) -> None:
        """
        """
        self.file_name = file_name
        self.config: list[tuple[str, str]] = []
        self.valid_keys = {
            "nb_drones",
            "start_hub",
            "hub",
            "end_hub",
            "connection"
        }
        self.unique_keys = {
            "nb_drones",
            "start_hub",
            "end_hub"
        }

    def has_all_keys(self) -> bool:
        """
        """

        config_keys = {
            t[0]
            for t in self.config
        }

        number_of_keys = len(config_keys)
        if number_of_keys != len(self.valid_keys):
            return False
        return True

    def get_config(self) -> dict[str, str]:
        """
        """
        try:
            with open(self.file_name, "r") as file:
                for raw_line in file:
                    line = raw_line.rstrip()

                    if not line or line.startswith("#"):
                        continue

                    if ":" not in line:
                        raise ParseError(f"Invalid line: '{line}'")

                    key, value = line.split(": ", 1)

                    if key.lower() not in self.valid_keys:
                        raise ParseError(
                            f"Unknown config key: '{key}' in '{line}'"
                        )

                    if (
                        key.lower() in self.config
                        and key.lower() in self.unique_keys
                    ):
                        raise ParseError(
                            f"Key must be unique: '{key}' ('{line}')"
                        )

                    self.config.append((key, value))

                if not self.has_all_keys():
                    raise ParseError("Missing mandatory key(s)")

            return self.config

        except FileNotFoundError:
            raise ParseError(
                "Configuration file not found"
            )

        except PermissionError:
            raise ParseError(
                "Permission denied when reading config file"
            )

        except OSError:
            raise ParseError(
                "Error accessing configuration file"
            )
