#!/usr/bin/env python
"""The anl universal command line tool"""
import math
import os
import sys
import traceback
from collections import defaultdict
from functools import partial
from pathlib import Path
from pprint import pformat, pprint
from time import perf_counter
from typing import List

import click
import click_config_file
import negmas
import numpy as np
import pandas as pd
import tqdm
import yaml
from negmas import save_stats
from negmas.helpers import humanize_time, unique_name
from negmas.helpers.inout import load
from tabulate import tabulate

import anl

try:
    from anl.vendor.quick.quick import gui_option
except:

    def gui_option(x):
        return x


try:
    # disable a warning in yaml 1b1 version
    yaml.warnings({"YAMLLoadWarning": False})
except:
    pass

n_completed = 0
n_total = 0


def default_log_path():
    """Default location for all logs"""
    return Path.home() / "negmas" / "anl"


DB_FOLDER = default_log_path().parent / "runsdb"
DB_NAME = "rundb.csv"


def save_run_info(
    name: str, log_path: Path, type_: str = "world", path: Path = DB_FOLDER
):
    try:
        path.mkdir(parents=True, exist_ok=True)
        with open(path / DB_NAME, "a") as f:
            f.write(f"{name},{type_},{str(log_path)}\n")
    except Exception as e:
        print(f"Failed to save run info: {str(e)}")


def default_tournament_path():
    """The default path to store tournament run info"""
    return default_log_path() / "tournaments"


def default_world_path():
    """The default path to store world run info"""
    return default_log_path() / "negotiations"


def print_progress(_, i, n) -> None:
    """Prints the progress of a tournament"""
    global n_completed, n_total
    n_completed = i + 1
    n_total = n
    print(
        f"{n_completed:04} of {n:04} worlds completed ({n_completed / n:0.2%})",
        flush=True,
    )


def shortest_unique_names(strs: List[str], sep="."):
    """
    Finds the shortest unique strings starting from the end of each input
    string based on the separator.

    The final strings will only be unique if the inputs are unique.

    Example:
        given ["a.b.c", "d.e.f", "a.d.c"] it will generate ["b.c", "f", "d.c"]
    """
    lsts = [_.split(sep) for _ in strs]
    names = [_[-1] for _ in lsts]
    if len(names) == len(set(names)):
        return names
    locs = defaultdict(list)
    for i, s in enumerate(names):
        locs[s].append(i)
    mapping = {"": ""}
    for s, l in locs.items():
        if len(s) < 1:
            continue
        if len(l) == 1:
            mapping[strs[l[0]]] = s
            continue
        strs_new = [sep.join(lsts[_][:-1]) for _ in l]
        prefixes = shortest_unique_names(strs_new, sep)
        for loc, prefix in zip(l, prefixes):
            x = sep.join([prefix, s])
            if x.startswith(sep):
                x = x[len(sep) :]
            mapping[strs[loc]] = x
    return [mapping[_] for _ in strs]


def nCr(n, r):
    return math.factorial(n) / math.factorial(r) / math.factorial(n - r)


click.option = partial(click.option, show_default=True)


@gui_option
@click.group()
def main():
    pass


@main.command(help="Runs an ANL 2024 tournament")
@click.option(
    "--parallel/--serial",
    default=True,
    help="Run a parallel/serial tournament on a single machine",
)
@click.option(
    "--name",
    "-n",
    default="random",
    help='The name of the tournament. The special value "random" will result in a random name',
)
@click.option(
    "--repetitions",
    "-r",
    default=10,
    type=int,
    help="Number of repetition for each negotiation",
)
@click.option(
    "--timeout",
    "-t",
    default=-1,
    type=int,
    help="Timeout the whole tournament after the given number of seconds (0 for infinite, -1 for None)",
)
@click.option(
    "--competitors",
    default="BoulwareTBNegoatiator;ConcederTBNegotiator",
    help="A semicolon (;) separated list of agent types to use for the competition. You"
    " can also pass the special value default for the default builtin"
    " agents",
)
@click.option(
    "--log",
    "-l",
    type=click.Path(dir_okay=True, file_okay=False),
    default=default_tournament_path(),
    help="Default location to save logs (A folder will be created under it)",
)
@click.option(
    "--verbosity",
    default=1,
    type=int,
    help="verbosity level",
)
@click.option(
    "--raise-exceptions/--ignore-exceptions",
    default=True,
    help="Whether to ignore agent exceptions",
)
@click.option(
    "--path",
    default="",
    help="A path to be added to PYTHONPATH in which all competitors are stored. You can path a : separated list of "
    "paths on linux/mac and a ; separated list in windows",
)
@click_config_file.configuration_option()
def tournament2024(
    parallel,
    name,
    repetitions,
    timeout,
    competitors,
    log,
    verbosity,
    raise_exceptions,
    path,
):
    ...


@main.command(help="Prints ANL version and NegMAS version")
def version():
    print(f"anl: {anl.__version__} (NegMAS: {negmas.__version__})")


if __name__ == "__main__":
    main()
