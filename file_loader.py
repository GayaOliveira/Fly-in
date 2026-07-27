from errors import ParseError


class FileLoader:
    """Reads and lexically validates a simulation configuration file.

    Reads the file line by line, skipping blank lines and comments,
    and builds an ordered list of ``(key, value)`` pairs while
    enforcing basic structural rules: the first key must be
    ``nb_drones``, every key must be recognized, and unique keys
    (``nb_drones``, ``start_hub``, ``end_hub``) must not repeat.

    Attributes:
        file_name (str): Path to the configuration file to load.
        config (list[tuple[str, str]]): Ordered ``(key, value)`` pairs
            parsed from the file so far.
        valid_keys (set[str]): Set of recognized configuration keys.
        unique_keys (set[str]): Set of keys that may appear at most
            once in the file.
        first_key (str): Key that must appear on the first
            non-comment, non-blank line of the file.
    """

    def __init__(self, file_name: str) -> None:
        """Initializes the loader for a given configuration file path.

        Args:
            file_name (str): Path to the configuration file to load.

        Returns:
            None
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
        self.first_key = "nb_drones"

    def has_all_keys(self) -> bool:
        """Checks whether every mandatory configuration key was found.

        Returns:
            bool: True if the set of distinct keys collected so far
            matches the full set of valid keys, False otherwise.
        """

        config_keys = {
            key
            for key, _ in self.config
        }

        number_of_keys = len(config_keys)
        if number_of_keys != len(self.valid_keys):
            return False
        return True

    def get_config(self) -> list[tuple[str, str]]:
        """Reads, validates, and returns the raw configuration entries.

        Opens the configuration file, processes each non-blank,
        non-comment line, and validates the overall structure (first
        key, known keys, uniqueness constraints, and presence of all
        mandatory keys).

        Returns:
            list[tuple[str, str]]: The ordered list of ``(key, value)``
            pairs parsed from the file.

        Raises:
            ParseError: If the file cannot be found, cannot be read
                due to permissions or other OS-level errors, contains
                a malformed line, uses an unknown or duplicated
                mandatory key, or is missing one or more mandatory
                keys.
        """
        try:
            with open(self.file_name, "r") as file:
                for raw_line in file:
                    line = raw_line.rstrip()

                    if not line or line.startswith("#"):
                        continue

                    if not self.config and not line.startswith(self.first_key):
                        raise ParseError(
                            f"First key should be '{self.first_key}'"
                        )

                    if ":" not in line:
                        raise ParseError(f"Invalid line: '{line}'")

                    parts = line.split(": ", 1)

                    if len(parts) <= 1:
                        raise ParseError(f"Invalid line: '{line}'")

                    key, value = parts

                    if key.lower() not in self.valid_keys:
                        raise ParseError(
                            f"Unknown config key: '{key}' in '{line}'"
                        )

                    if (
                        key.lower() in [key for key, _ in self.config]
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
