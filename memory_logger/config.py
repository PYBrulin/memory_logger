import argparse
import json
import logging
import os


class Config:
    """
    This is the configuration class for the memory logger.
    It is used to store the configuration of the memory logger on system.
    """

    _config = {}
    _local = False

    def __init__(self) -> None:
        self.read_config_file()

    @property
    def has_local_config(self) -> str:
        """
        Get the configuration file path.
        """
        return os.path.exists(self.local_config_filepath)

    @property
    def is_local(self) -> bool:
        return self._local

    @is_local.setter
    def is_local(self, value: bool) -> None:
        self._local = value

    @property
    def config_filepath(self) -> str:
        """
        Get the configuration file path.
        """
        if self.has_local_config:
            return self.local_config_filepath
        return self.global_config_filepath

    @property
    def local_config_filepath(self) -> str:
        return "memory_logger.config"

    @property
    def global_config_filepath(self) -> str:
        return os.path.join(os.path.dirname(__file__), "memory_logger.config")

    def read_config_file(self) -> None:
        """
        Read the configuration file from the given path.
        """
        if os.path.exists(self.config_filepath):
            with open(self.config_filepath) as f:
                _config = json.load(f)
            if (
                self.has_local_config and not self.is_local
            ):  # Update the global configuration file with the local configuration
                if os.path.exists(self.global_config_filepath):
                    with open(self.global_config_filepath) as f:
                        global_config = json.load(f)
                    for key, value in global_config.items():
                        if key not in _config:
                            _config[key] = value
            self._config = _config
        else:
            logging.warning("No 'memory_logger.config' file found. Using global configuration.")
            logging.warning("You can configure the memory logger settings using the command:")
            logging.warning("\t $ python -m memory_logger.config --help")

    @property
    def config(self) -> dict:
        """
        Get the configuration dictionary.
        """
        self.read_config_file()
        return self._config

    def write_config_file(self) -> None:
        """
        Write the configuration file to the given path.
        """
        with open(self.local_config_filepath if self.is_local else self.global_config_filepath, "w") as f:
            json.dump(self._config, f)

    def set_config(self, key: str, value) -> None:
        """
        Set a configuration parameter to the given value.
        """
        self.read_config_file()
        self._config[key] = value
        self.write_config_file()

    # region Configuration parameters
    @property
    def rate(self) -> float:
        """Rate at which the memory usage is logged (in seconds). Default is 0.01 seconds (100 Hz)."""
        return self._config.get("rate", 0.01)

    @property
    def show_gui(self) -> bool:
        """Whether to show the signal viewer GUI at the end of the run. Default is True."""
        return self._config.get("show_gui", True)

    # endregion


if __name__ == "__main__":
    config = Config()

    parser = argparse.ArgumentParser(
        description="Memory usage logger configuration",
    )
    scope = parser.add_argument_group("Configuration scope")
    scope.add_argument(
        "--local",
        action="store_true",
        help="Use a local memory_logger.config file",
    )
    scope.add_argument(
        "--list",
        action="store_true",
        help="List the current configuration parameters (global overriden by local)",
    )
    params = parser.add_argument_group(
        "Configurable parameters",
    )
    params.add_argument(
        "--rate",
        type=float,
        help="Rate at which the memory usage is logged (in seconds). Default is 0.01 seconds (100 Hz).",
    )
    params.add_argument(
        "--show-gui",
        action="store_true",
        help="Show the GUI for the memory logger at the end of the run",
    )
    params.add_argument(
        "--no-show-gui",
        action="store_true",
        help="Do not show the GUI for the memory logger at the end of the run",
    )
    args = parser.parse_args()

    # Set to local if the flag is set (global is the default)
    config.is_local = args.local

    if args.list:
        print(json.dumps(config.config, indent=4))

    # Apply the configuration parameters
    if args.rate:
        config.set_config("rate", args.rate)

    if args.show_gui or args.no_show_gui:
        if args.show_gui and args.no_show_gui:
            raise ValueError("You cannot set both --show-gui and --no-show-gui at the same time.")
        config.set_config("show_gui", args.show_gui if args.show_gui else not args.no_show_gui)
