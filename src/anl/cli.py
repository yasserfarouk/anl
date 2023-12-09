#!/usr/bin/env python
"""The ANL universal command line tool"""
import math
import os
import sys
from collections import defaultdict
from functools import partial
from pathlib import Path
from time import perf_counter
from typing import List

import click
import click_config_file
import negmas
from negmas.helpers import humanize_time, unique_name
from negmas.helpers.types import get_class
from rich import print

import anl
from anl import DEFAULT_AN2024_COMPETITORS
from anl.anl2024.runner import DEFAULT_TOURNAMENT_PATH, anl2024_tournament

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


@click.group()
def main():
    pass


def _path(path) -> Path:
    """Creates an absolute path from given path which can be a string"""
    if isinstance(path, Path):
        return path.absolute()
    path.replace("/", os.sep)
    if isinstance(path, str):
        if path.startswith("~"):
            path = Path.home() / (os.sep.join(path.split(os.sep)[1:]))
    return Path(path).absolute()


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
    "--outcomes",
    "-o",
    default=1000,
    type=int,
    help="Number of outcomes in every scenario",
)
@click.option(
    "--scenarios",
    "-S",
    default=10,
    type=int,
    help="Number of scenarios to generate",
)
@click.option(
    "--repetitions",
    "-r",
    default=10,
    type=int,
    help="Number of repetition for each negotiation",
)
@click.option(
    "--competitors",
    default="Conceder;Linear;Boulware",
    help="A semicolon (;) separated list of agent types to use for the competition. You"
    " can also pass the special value default for the default builtin"
    " agents",
)
@click.option(
    "--metric",
    default="advantage",
    help="The metric to use for evaluating agents. Can be one of: utility, advantage, partner_welfare, welfare",
)
@click.option(
    "--stat",
    default="mean",
    help="The statistic applied to the metric to evaluate agents. Can be one of: mean, median, std, min, max",
)
@click.option(
    "--known-partner/--unknown-partner",
    default=False,
    help="Can the agent know its partner type?",
)
@click.option(
    "--save-logs/--no-logs",
    default=True,
    help="Whether to save logs.",
)
@click.option(
    "--timelimit",
    "-t",
    default=-1,
    type=float,
    help="Number of seconds allowed in every negotiation. Negative numbers mean no-limit",
)
@click.option(
    "--steps",
    "-s",
    default=-1,
    type=int,
    help="Number of negotiation rounds allowed in every negotiation. Negative numbers mean no-limit",
)
@click.option(
    "--pend",
    default=0.0,
    type=float,
    help="Probability of ending the negotiation at every round",
)
@click.option(
    "--plot",
    "-p",
    default=0.1,
    type=float,
    help="Fraction of negotiations to plot and save",
)
@click.option(
    "--verbosity",
    "-v",
    default=1,
    type=int,
    help="verbosity level",
)
@click.option(
    "--save_every",
    "-e",
    default=1,
    type=int,
    help="Number of negotiations after which to save stats",
)
@click.option(
    "--rotate/--no-rotate",
    default=True,
    help="Rotate utility functions when creating scenarios for the tournament",
)
@click.option(
    "--self-play/--no-self-play",
    default=True,
    help="Allow each agent to negotiate with itself or not",
)
@click.option(
    "--randomize/--no-randomize",
    default=True,
    help="Randomize the order of negotiations or not",
)
# @click.option(
#     "--raise-exceptions/--ignore-exceptions",
#     default=True,
#     help="Whether to ignore agent exceptions",
# )
@click.option(
    "--path",
    default="",
    help="A path to be added to PYTHONPATH in which all competitors are stored. You can pass a : separated list of "
    "paths on linux/mac and a ; separated list in windows",
)
@click_config_file.configuration_option()
def tournament2024(
    parallel,
    name,
    repetitions,
    competitors,
    verbosity,
    path,
    metric,
    save_logs,
    stat,
    known_partner,
    save_every,
    randomize,
    self_play,
    plot,
    pend,
    timelimit,
    steps,
    rotate,
    outcomes,
    scenarios,
):
    if len(path) > 0:
        sys.path.append(path)
    if name == "random":
        name = unique_name(base="", rand_digits=0)

    all_competitors = competitors.split(";")

    def find_type_name(stem: str):
        for pre in (
            "",
            "anl.anl2024.negotiators.",
            "negmas.sao.negotiators.",
            "negmas.genius.gnegotiators.",
        ):
            s = pre + stem
            try:
                get_class(s)
                return s
            except:
                pass
        print(f"[red]ERROR[/red] Unknown Competitor Type: {stem}")
        sys.exit()

    for i, cp in enumerate(all_competitors):
        all_competitors[i] = find_type_name(cp)

    if not all_competitors:
        all_competitors = DEFAULT_AN2024_COMPETITORS
    all_competitors_params = [dict() for _ in range(len(all_competitors))]

    print(f"Tournament will be run between {len(all_competitors)} agents: ")
    print(all_competitors)
    if steps <= 0:
        steps = None
    if timelimit <= 0:
        timelimit = None
    if steps is None and timelimit is None and pend <= 0.0:
        print(
            f"[red]ERROR[/red] You specified no way to end the negotiation. You MUST pass either --steps, --timelimit or --pend"
        )
        sys.exit(1)
    tic = perf_counter()
    results = anl2024_tournament(
        n_scenarios=scenarios,
        n_outcomes=outcomes,
        competitors=all_competitors,
        competitor_params=all_competitors_params,
        rotate_ufuns=rotate,
        n_repetitions=repetitions,
        n_steps=steps,
        time_limit=timelimit,
        pend=pend,
        name=name,
        nologs=not save_logs,
        njobs=0 if parallel else -1,
        plot_fraction=plot,
        verbosity=verbosity,
        self_play=self_play,
        randomize_runs=randomize,
        save_every=save_every,
        known_partner=known_partner,
        final_score=(metric, stat),
    )
    print(results.final_scores)
    print(f"Done in {humanize_time(perf_counter() - tic, show_ms=True)}")
    if save_logs:
        print(f"Detailed logs are stored at: {DEFAULT_TOURNAMENT_PATH / name}")


@main.command(help="Prints ANL version and NegMAS version")
def version():
    print(f"anl: {anl.__version__} (NegMAS: {negmas.__version__})")


if __name__ == "__main__":
    main()
