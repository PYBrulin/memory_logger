# Track the memory usage of a process and its children over time.

import datetime
import logging
import os
import sys
import time

import pandas
import psutil

from memory_logger.config import Config
from memory_logger.plot import plot_memory_usage


class MemoryLogger:
    def __init__(self, command) -> None:
        self.process = None
        self.child_processes = {}
        self.command = command

        datetime_now = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%dT%H%M%S")
        self.foldername = f"memory_logger_{datetime_now}.log"
        os.makedirs(self.foldername, exist_ok=True)

        # Create a file to store the command
        with open(os.path.join(self.foldername, "command.txt"), "w") as f:
            f.write(" ".join(self.command))

        self.start_timestamp = time.time()

    def trace_memory_usage(self, pid=None) -> None:
        timestamp = time.time() - self.start_timestamp

        # Return memory usage in Megabytes
        if pid is not None and self.process is None:
            self.process = psutil.Process(pid)

        mem_info = {
            "time": timestamp,
            "sys.mem.total": psutil.virtual_memory().total / (1024 * 1024),
            "sys.mem.available": psutil.virtual_memory().available / (1024 * 1024),
            "sys.mem.percent": psutil.virtual_memory().percent,
            "sys.mem.used": psutil.virtual_memory().used / (1024 * 1024),
            "sys.mem.free": psutil.virtual_memory().free / (1024 * 1024),
            "sys.cpu": psutil.cpu_percent(),
        }
        pandas.DataFrame(mem_info, index=[0]).to_csv(
            os.path.join(self.foldername, "system.csv"),
            mode="a" if os.path.exists(os.path.join(self.foldername, "system.csv")) else "w",
            header=not os.path.exists(os.path.join(self.foldername, "system.csv")),
            index=False,
        )

        if pid is not None:
            try:
                pid_info = {
                    "time": timestamp,
                    "pid.mem": self.process.memory_info().rss / (1024 * 1024) if pid is not None else 0,
                    "pid.cpu": self.process.cpu_percent() if pid is not None else 0,
                }
                pandas.DataFrame(pid_info, index=[0]).to_csv(
                    os.path.join(self.foldername, f"pid_{pid}.csv"),
                    mode="a" if os.path.exists(os.path.join(self.foldername, f"pid_{pid}.csv")) else "w",
                    header=not os.path.exists(os.path.join(self.foldername, f"pid_{pid}.csv")),
                    index=False,
                )
            except psutil.NoSuchProcess:
                logging.warning(f"Process {pid} does not exist anymore.")
                return

            # Get the child processes
            child_processes = self.process.children(recursive=True)
            for child in child_processes:
                try:
                    if child.pid not in self.child_processes:
                        self.child_processes[child.pid] = child
                    else:
                        # Change reference to the known process
                        child = self.child_processes[child.pid]

                    child_info = {
                        "time": timestamp,
                        f"child.{child.pid}.mem": child.memory_info().rss / (1024 * 1024),
                        f"child.{child.pid}.cpu": child.cpu_percent(),
                    }
                    pandas.DataFrame(child_info, index=[0]).to_csv(
                        os.path.join(self.foldername, f"child_{child.pid}.csv"),
                        mode="a" if os.path.exists(os.path.join(self.foldername, f"child_{child.pid}.csv")) else "w",
                        header=not os.path.exists(os.path.join(self.foldername, f"child_{child.pid}.csv")),
                        index=False,
                    )
                except psutil.NoSuchProcess:
                    logging.warning(f"Process {child.pid} does not exist anymore.")


def main() -> None:
    # Note: Unfortunatelly, it is not possible to use argparse to parse the command line arguments here.
    # The reason is that the process to be traced has priority over the command line arguments.

    if len(sys.argv) < 2:
        print("Usage: python memory_usage.py <command>")
        sys.exit(1)

    config = Config()

    command = sys.argv[1:]

    mem_logger = MemoryLogger(command=command)

    # Start the process
    print(f"Running command: {command}")
    process = psutil.Popen(command)
    pid = process.pid

    # Log the memory usage
    time_cpu = time.time()
    while process.is_running():  # ! Note: Ensure that the process can exit by itself (No GUI blocking the process, etc.)
        mem_logger.trace_memory_usage(pid)

        # Try to enforce the rate.  Although this is only useful for low rate
        # configurations, the rate at which the memory usage is logged is
        # limited by the rate at which the memory is collected, the number of
        # processes/children processes being traced, and the rate at which the
        # data is written to disk. Optimizations are definitely possible.
        time.sleep(max(0, config.rate - (time.time() - time_cpu)))

    # Plot the memory usage
    if config.show_gui:
        plot_memory_usage(mem_logger.foldername)


if __name__ == "__main__":
    main()
