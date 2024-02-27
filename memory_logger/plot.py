import argparse
import os
import re

import numpy
import pandas
from signal_plotter.plot_window import plot_window


def plot_memory_usage(output_foldername: str) -> None:
    items = {}
    # List files in the folder
    files = os.listdir(output_foldername)

    # Read the command from the command.txt file
    if "command.txt" in files:
        with open(os.path.join(output_foldername, "command.txt"), "r") as f:
            command = f.read()
    else:
        command = None

    # Read the content of the system file first
    system_file = next((f for f in files if "system" in f), None)
    if system_file is None:
        raise FileNotFoundError("No system.csv file found in the output folder")

    sys_data = pandas.read_csv(os.path.join(output_foldername, system_file))
    sys_time = numpy.ravel(sys_data["time"])  # get time as reference

    # Read the content of the files except the system file and the command.txt file
    pid_files = [f for f in files if f.endswith(".csv") and f != system_file]
    for pid_file in pid_files:
        pid_data = pandas.read_csv(os.path.join(output_foldername, pid_file))

        # Merge the data with the system data along the time axis
        sys_data = sys_data.merge(pid_data, on="time", how="outer").fillna(0)

    # Compute the sum of the memory usage for the process and its children
    sys_data["pid.mem_total"] = sys_data.filter(regex=re.compile(r'child\.\d+\.mem')).sum(axis=1) + sys_data["pid.mem"]

    for key, value in sys_data.items():
        items[key] = {
            "x": numpy.ravel(sys_time),
            "y": numpy.ravel(value),
            "units": "%" if ("cpu" in key or "percent" in key) else "MB" if "mem" in key else "",
        }

    plot_window(
        title="Memory usage" + (f" '{command}'" if command is not None else ""),
        items=items,
        sub_groups={
            "cpu": [key for key in items.keys() if "cpu" in key],
            "mem": [key for key in items.keys() if "mem" in key],
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot memory usage")
    parser.add_argument("output_foldername", type=str, help="Folder containing the memory data")
    args = parser.parse_args()

    plot_memory_usage(args.output_foldername)
