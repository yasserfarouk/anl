#!/usr/bin/env python
"""The ANL universal command line tool"""

import math
import sys
import warnings
from collections import defaultdict
from functools import partial
from itertools import chain
from pathlib import Path
from time import perf_counter
from typing import Iterable, List

import click
import click_config_file
import matplotlib.pyplot as plt
import negmas
from negmas.helpers import humanize_time, unique_name
from negmas.helpers.inout import load
from negmas.helpers.types import get_class
from negmas.inout import Scenario
from negmas.plots.util import plot_offline_run
from rich import print

import anl
from anl import DEFAULT_AN2024_COMPETITORS
from anl.anl2024.runner import (
    DEFAULT2024SETTINGS,
    DEFAULT_TOURNAMENT_PATH,
    GENMAP,
    anl2024_tournament,
)

n_completed = 0
n_total = 0


def default_log_path():
    """Default location for all logs"""
    return Path.home() / "negmas" / "anl"


DB_FOLDER = default_log_path().parent / "runsdb"
DB_NAME = "rundb.csv"


def read_range(x, min_x, max_x):
    if x > 0:
        return x
    if min_x < 0 and max_x < 0:
        return min_x
    if min_x == max_x:
        return min_x
    return (min_x, max_x)


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
    default=DEFAULT2024SETTINGS["n_outcomes"]
    if not isinstance(DEFAULT2024SETTINGS["n_outcomes"], Iterable)
    else -1,  # type: ignore # type: ignore
    type=int,
    help="Number of outcomes in every scenario. If negative or zero, --min-outcomes and --max-outcomes will beused",
)
@click.option(
    "--min-outcomes",
    default=DEFAULT2024SETTINGS["n_outcomes"][0]
    if isinstance(DEFAULT2024SETTINGS["n_outcomes"], Iterable)
    else -1,  # type: ignore # type: ignore
    type=int,
    help="Minimum number of outcomes in every scenario. Only used of --outcomes is zero or negative",
)
@click.option(
    "--max-outcomes",
    default=DEFAULT2024SETTINGS["n_outcomes"][1]
    if isinstance(DEFAULT2024SETTINGS["n_outcomes"], Iterable)
    else -1,  # type: ignore # type: ignore
    type=int,
    help="Max number of outcomes in every scenario. Only used of --outcomes is zero or negative",
)
@click.option(
    "--scenarios",
    "-S",
    default=min(5, DEFAULT2024SETTINGS["n_scenarios"]),  # type: ignore
    type=int,
    help="Number of scenarios to generate",
)
@click.option(
    "--repetitions",
    "-r",
    default=DEFAULT2024SETTINGS["n_repetitions"],  # type: ignore
    type=int,
    help="Number of repetition for each negotiation",
)
@click.option(
    "--competitors",
    default=";".join(
        _().type_name.split(".")[-1] for _ in DEFAULT2024SETTINGS["competitors"]
    ),  # type: ignore # type: ignore
    help="A semicolon (;) separated list of agent types to use for the competition. You"
    " can also pass the special value default for the default builtin"
    " agents",
)
@click.option(
    "--params",
    default="",
    help="A string encoding the parameters to pass for negotiators. Default is None. The format of this string is:\n"
    "'competitor:key:value,key:value,..key:value;competitor:key:value,key:value,...key:value\n"
    "For example:\nRVFitter:enable_logging:True:e:4.0;NashSeeker:nash_factor:1.0\nmeans: RVFitter's params are dict(enable_logging=True, e=True)"
    " and NashSeeker's params are dict(nash_factor=1.0)\n\nBe sure to use the python-correct format for values. For example put strings in single quots.",
)
@click.option(
    "--metric",
    default=DEFAULT2024SETTINGS["final_score"][0],  # type: ignore # type: ignore
    help="The metric to use for evaluating agents. Can be one of: utility, advantage, partner_welfare, welfare",
)
@click.option(
    "--stat",
    default=DEFAULT2024SETTINGS["final_score"][1],  # type: ignore # type: ignore
    help="The statistic applied to the metric to evaluate agents. Can be one of: mean, median, std, min, max",
)
@click.option(
    "--small/--normal",
    default=False,
    help="If --small, then a small tournament will be run and most parameters will be ignored",
)
@click.option(
    "--known-partner/--unknown-partner",
    default=DEFAULT2024SETTINGS["known_partner"],  # type: ignore
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
    default=DEFAULT2024SETTINGS["hidden_time_limit"]  # type: ignore
    if not isinstance(DEFAULT2024SETTINGS["hidden_time_limit"], Iterable)  # type: ignore
    else -1,
    type=float,
    help="Number of seconds allowed in every negotiation. Negative numbers mean no-limit",
)
@click.option(
    "--allowedtime",
    "-T",
    default=DEFAULT2024SETTINGS["time_limit"]  # type: ignore
    if not isinstance(DEFAULT2024SETTINGS["time_limit"], Iterable)  # type: ignore
    else -1,
    type=float,
    help="Number of seconds allowed in every negotiation. Negative numbers mean no-limit",
)
@click.option(
    "--min-allowedtime",
    default=DEFAULT2024SETTINGS["time_limit"][0]  # type: ignore
    if isinstance(DEFAULT2024SETTINGS["time_limit"], Iterable)  # type: ignore
    else -1,
    type=int,
    help="Minimum number of seconds in every scenario. Only used of --allowedtime is zero or negative",
)
@click.option(
    "--max-allowedtime",
    default=DEFAULT2024SETTINGS["time_limit"][1]  # type: ignore
    if isinstance(DEFAULT2024SETTINGS["time_limit"], Iterable)  # type: ignore
    else -1,
    type=int,
    help="Max number of seconds in every scenario. Only used of --allowedtime is zero or negative",
)
@click.option(
    "--steps",
    "-s",
    default=DEFAULT2024SETTINGS["n_steps"]  # type: ignore
    if not isinstance(DEFAULT2024SETTINGS["n_steps"], Iterable)  # type: ignore
    else -1,
    type=int,
    help="Number of negotiation rounds allowed in every negotiation. Negative numbers mean no-limit",
)
@click.option(
    "--min-steps",
    default=DEFAULT2024SETTINGS["n_steps"][0]  # type: ignore
    if isinstance(DEFAULT2024SETTINGS["n_steps"], Iterable)  # type: ignore
    else -1,
    type=int,
    help="Minimum number of steps in every scenario. Only used of --steps is zero or negative",
)
@click.option(
    "--max-steps",
    default=DEFAULT2024SETTINGS["n_steps"][1]  # type: ignore
    if isinstance(DEFAULT2024SETTINGS["n_steps"], Iterable)  # type: ignore
    else -1,
    type=int,
    help="Max number of steps in every scenario. Only used of --steps is zero or negative",
)
@click.option(
    "--pend",
    default=DEFAULT2024SETTINGS["pend"]  # type: ignore
    if not isinstance(DEFAULT2024SETTINGS["pend"], Iterable)  # type: ignore
    else -1,
    type=float,
    help="Probability of ending the negotiation at every round",
)
@click.option(
    "--min-pend",
    default=DEFAULT2024SETTINGS["pend"][0]  # type: ignore
    if isinstance(DEFAULT2024SETTINGS["pend"], Iterable)  # type: ignore
    else -1,
    help="Minimum pend in every scenario. Only used of --pend is zero or negative",
)
@click.option(
    "--max-pend",
    default=DEFAULT2024SETTINGS["pend"][1]  # type: ignore
    if isinstance(DEFAULT2024SETTINGS["pend"], Iterable)  # type: ignore
    else -1,
    help="Max pend in every scenario. Only used of --pend is zero or negative",
)
@click.option(
    "--self-play/--no-self-play",
    default=DEFAULT2024SETTINGS["self_play"],  # type: ignore
    type=bool,
    help="Allow self-play during the tournament",
)
@click.option(
    "--plot",
    "-p",
    default=0.1 if sys.platform in ("darwin", "linux") else 0,
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
    "--generator",
    default=DEFAULT2024SETTINGS["scenario_generator"],  # type: ignore
    type=str,
    help="The method to generate scenarios. Default is mix which generates a mix of scenario types containing zero-sum, monotonic and general scenarios. Other possibilities are monotonic, pie, zerosom, arbitrary",
)
@click.option(
    "--zerosum",
    "-z",
    default=DEFAULT2024SETTINGS["generator_params"].get("zerosum_fraction", 0.05),  # type: ignore
    type=float,
    help="Fraction of zero-sum scenarios (used when generator=mix)",
)
@click.option(
    "--monotonic",
    "-m",
    default=DEFAULT2024SETTINGS["generator_params"].get("monotonic_fraction", 0.25),  # type: ignore
    type=float,
    help="Fraction of monotonic scenarios (used when generator=mix)",
)
@click.option(
    "--curve",
    "-c",
    default=DEFAULT2024SETTINGS["generator_params"].get("curve_fraction", 0.25),  # type: ignore
    type=float,
    help="Fraction of monotonic and general scenarios generated using a Pareto curve not piecewise linear Pareto (used when generator=mix)",
)
@click.option(
    "--pies",
    default=DEFAULT2024SETTINGS["generator_params"].get("pies_fraction", 0.25),  # type: ignore
    type=float,
    help="Fraction of monotonic and general scenarios generated using a Pareto curve not piecewise linear Pareto (used when generator=mix)",
)
@click.option(
    "--rotate/--no-rotate",
    default=DEFAULT2024SETTINGS["rotate_ufuns"],  # type: ignore
    help="Rotate utility functions when creating scenarios for the tournament",
)
@click.option(
    "--randomize/--no-randomize",
    default=DEFAULT2024SETTINGS["randomize_runs"],  # type: ignore
    help="Randomize the order of negotiations or not",
)
@click.option(
    "--two/--cartesian",
    default=False,  # type: ignore
    help="If --two is passed, a single negotiation will be conducted between the first two in the competitors list."
    " This is equivalent to passing --scenarios=1, --no-rotate --competitors=A;B --repetitions=1."
    " If only one competitor is given it is run against itself (with --self-platy assumed).",
)
@click.option(
    "--raise-exceptions/--ignore-exceptions",
    default=True,
    help="Whether to ignore agent exceptions",
)
@click.option(
    "--scenarios-path",
    default=None,
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Path containing folders each representing a negotiation scenario.",
)
@click.option(
    "--settings-file",
    default=None,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to a yaml/json file containing parameters to pass to the generator",
)
@click.option(
    "--path",
    default="",
    help="A path to be added to PYTHONPATH in which all competitors are stored. You can pass a : separated list of "
    "paths on linux/mac and a ; separated list in windows",
)
@click_config_file.configuration_option()
def tournament2024(
    parallel,
    generator,
    name,
    repetitions,
    raise_exceptions,
    competitors,
    params,
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
    min_pend,
    max_pend,
    timelimit,
    allowedtime,
    min_allowedtime,
    max_allowedtime,
    steps,
    min_steps,
    max_steps,
    rotate,
    outcomes,
    min_outcomes,
    max_outcomes,
    scenarios,
    small,
    settings_file,
    zerosum,
    monotonic,
    curve,
    pies,
    two,
    scenarios_path,
):
    if two:
        competitorslst = competitors.split(";")
        scenarios = 1
        rotate = False
        repetitions = 1
        parallel = False
        if len(competitorslst) == 1:
            competitorslst = [competitorslst[0], competitorslst[0]]
            self_play = True
        else:
            competitorslst = competitorslst[:2]
            self_play = False
        competitors = ";".join(competitorslst)
    generator_params = dict()
    # read settings of the scenario generator from the settings file if available
    if settings_file:
        generator_params = load(settings_file)
    # override settings with the appropriate ones based on the generator
    if generator == "mix":
        generator_params.update(
            zerosum_fraction=zerosum,
            monotonic_fraction=monotonic,
            curve_fraction=curve,
            pies_fraction=pies,
        )
    if small:
        scenarios = min(scenarios, 2)
        steps = -1
        min_steps, max_steps = (10, 1000)
        outcomes = 100
        repetitions = 1
        competitors = ";".join(competitors.split(";")[:3])

    steps = read_range(steps, min_steps, max_steps)
    outcomes = read_range(outcomes, min_outcomes, max_outcomes)
    allowedtime = read_range(allowedtime, min_allowedtime, max_allowedtime)
    pend = read_range(pend, min_pend, max_pend)
    if len(path) > 0:
        sys.path.append(path)
    if name == "random":
        name = unique_name(base="", rand_digits=0)

    all_competitors = competitors.split(";")
    all_params = [dict() for _ in all_competitors]
    if params:
        paramslst: list[str] = params.split(";")

        def parse_params(s: str, k: str) -> dict:
            vals = s.split(":")
            if len(vals) % 2 == 1:
                print(
                    f"[red]ERROR[red]: failed to parse {s} (the paramters of {k})"
                    f" in given competitor params {params} because it has an odd "
                    f"number of ':' separated parts ({len(vals)=}, {len(vals) % 2=}, {vals=})."
                )
                exit(1)
            d = dict()
            for i in range(0, len(vals), 2):
                d[vals[i]] = eval(vals[i + 1])
            return d

        params_map = defaultdict(dict)
        for s in paramslst:
            k, _, v = s.partition(":")
            params_map[k] = parse_params(v, k)

        for i, c in enumerate(all_competitors):
            all_params[i] = params_map.get(c, dict())

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
        all_competitors[i] = find_type_name(cp)  # type: ignore

    if not all_competitors:
        all_competitors = DEFAULT_AN2024_COMPETITORS

    print(f"Tournament will be run between {len(all_competitors)} agents: ")
    print(all_competitors)
    n_params = sum(len(_) for _ in all_params)
    if n_params > 0:
        print("Will use the following competitor parameters:")
        for c, p in zip(all_competitors, all_params):
            if not p:
                continue
            print(f"{c}:\n\t{p}")
    if not isinstance(steps, tuple) and steps <= 0:
        steps = None
    if not isinstance(allowedtime, tuple) and allowedtime <= 0:
        allowedtime = None
    if (
        steps is None
        and allowedtime is None
        and not isinstance(pend, tuple)
        and pend <= 0.0
    ):
        print(
            "[red]ERROR[/red] You specified no way to end the negotiation. You MUST pass either --steps, --allowedtime or --pend (or the --min, --max versions of them)"
        )
        sys.exit(1)
    loaded_scenarios = []
    if scenarios:
        print(f"Will generate {scenarios} scenarios of {outcomes} outcomes each.")
    if scenarios_path is not None:
        for path in chain([scenarios_path], Path(scenarios_path).glob("**/*")):
            path = Path(path)
            if not path.is_dir():
                continue
            if not Scenario.is_loadable(path):
                print(f"{path} is not loadable")
                continue
            try:
                scenario = Scenario.load(path, safe_parsing=False)
                if scenario:
                    loaded_scenarios.append(scenario)
            except Exception as e:
                warnings.warn(f"Could not load scenario from {path}. Error: {str(e)}")

        print(
            f"Will use {len(loaded_scenarios)} scenarios loaded from {scenarios_path}."
        )
    print("Negotiations will end if any of the following conditions is satisfied:")
    if steps is not None:
        print(f"\tN. Rounds: {steps}")
    if timelimit is not None:
        print(f"\tN. Seconds: {timelimit}")
    if allowedtime is not None:
        print(f"\tN. Seconds (known): {allowedtime}")
    if pend is not None and (isinstance(pend, tuple) or pend > 0):
        print(f"\tProbability of ending each round : {pend}")
    if len(loaded_scenarios) + scenarios == 0:
        print(
            f"You must either pass --scenarios with the number of scenarios to be generated or pass --scenarios-path with a folder containing scenarios to use.\nYou are passing {scenarios=}, {scenarios_path=}. \nWill exit"
        )
        exit()
    tic = perf_counter()
    results = anl2024_tournament(
        scenarios=loaded_scenarios,
        n_scenarios=scenarios,
        n_outcomes=outcomes,
        competitors=all_competitors,  # type: ignore
        competitor_params=all_params,
        rotate_ufuns=rotate,
        n_repetitions=repetitions,
        n_steps=steps,
        hidden_time_limit=timelimit,
        time_limit=allowedtime,
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
        scenario_generator=generator,
        generator_params=generator_params,
        raise_exceptions=raise_exceptions,
    )
    if verbosity <= 0:
        print(results.final_scores)
    print(f"Done in {humanize_time(perf_counter() - tic, show_ms=True)}")
    if save_logs:
        print(f"Detailed logs are stored at: {DEFAULT_TOURNAMENT_PATH / name}")


@main.command(
    help="Generates sceanrios a la ANL.\n\nYou must pass the path to save the scenarios into as the first parameter"
)
@click.argument(
    "path",
    type=click.Path(file_okay=False),
)
@click.option(
    "--outcomes",
    "-o",
    default=DEFAULT2024SETTINGS["n_outcomes"]
    if not isinstance(DEFAULT2024SETTINGS["n_outcomes"], Iterable)
    else -1,  # type: ignore # type: ignore
    type=int,
    help="Number of outcomes in every scenario. If negative or zero, --min-outcomes and --max-outcomes will beused",
)
@click.option(
    "--min-outcomes",
    default=DEFAULT2024SETTINGS["n_outcomes"][0]
    if isinstance(DEFAULT2024SETTINGS["n_outcomes"], Iterable)
    else -1,  # type: ignore # type: ignore
    type=int,
    help="Minimum number of outcomes in every scenario. Only used of --outcomes is zero or negative",
)
@click.option(
    "--max-outcomes",
    default=DEFAULT2024SETTINGS["n_outcomes"][1]
    if isinstance(DEFAULT2024SETTINGS["n_outcomes"], Iterable)
    else -1,  # type: ignore # type: ignore
    type=int,
    help="Max number of outcomes in every scenario. Only used of --outcomes is zero or negative",
)
@click.option(
    "--scenarios",
    "-S",
    default=min(5, DEFAULT2024SETTINGS["n_scenarios"]),  # type: ignore
    type=int,
    help="Number of scenarios to generate",
)
@click.option(
    "--generator",
    default=DEFAULT2024SETTINGS["scenario_generator"],  # type: ignore
    type=str,
    help="The method to generate scenarios. Default is mix which generates a mix of scenario types containing zero-sum, monotonic and general scenarios",
)
@click.option(
    "--zerosum",
    "-z",
    default=DEFAULT2024SETTINGS["generator_params"].get("zerosum_fraction", 0.05),  # type: ignore
    type=float,
    help="Fraction of zero-sum scenarios (used when generator=mix)",
)
@click.option(
    "--monotonic",
    "-m",
    default=DEFAULT2024SETTINGS["generator_params"].get("monotonic_fraction", 0.25),  # type: ignore
    type=float,
    help="Fraction of monotonic scenarios (used when generator=mix)",
)
@click.option(
    "--curve",
    "-c",
    default=DEFAULT2024SETTINGS["generator_params"].get("curve_fraction", 0.5),  # type: ignore
    type=float,
    help="Fraction of monotonic and general scenarios generated using a Pareto curve not piecewise linear Pareto (used when generator=mix)",
)
@click.option(
    "--settings-file",
    default=None,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to a yaml/json file containing parameters to pass to the generator",
)
@click.option(
    "--plot",
    "-p",
    default=0.1 if sys.platform in ("darwin", "linux") else 0,
    type=float,
    help="Fraction of negotiations to plot and save",
)
@click_config_file.configuration_option()
def make_scenarios(
    path,
    scenarios,
    outcomes,
    min_outcomes,
    max_outcomes,
    generator,
    settings_file,
    zerosum,
    monotonic,
    curve,
    plot,
):
    if scenarios == 0:
        print("You must pass --scenarios with the number of scenarios to be generated")
        exit()
    generator_params = dict()
    # read settings of the scenario generator from the settings file if available
    if settings_file:
        generator_params = load(settings_file)
    # override settings with the appropriate ones based on the generator
    if generator == "mix":
        generator_params.update(
            zerosum_fraction=zerosum,
            monotonic_fraction=monotonic,
            curve_fraction=curve,
        )

    outcomes = read_range(outcomes, min_outcomes, max_outcomes)

    print(f"Will generate {scenarios} scenarios of {outcomes} outcomes each.")
    scenario_generator = GENMAP[generator]
    scenarios = scenario_generator(
        n_scenarios=scenarios, n_outcomes=outcomes, **generator_params
    )
    path = Path(path)
    for s in scenarios:
        mypath = path / s.outcome_space.name  # type: ignore
        s.dumpas(mypath)  # type: ignore
        if plot:
            plot_offline_run(
                trace=[],
                ids=["First", "Second"],
                ufuns=s.ufuns,  # type: ignore
                agreement=None,
                timedout=False,
                broken=False,
                has_error=False,
                names=["First", "Second"],
                save_fig=True,
                path=mypath,
                fig_name="fig.png",
                only2d=True,
                show_annotations=False,
                show_agreement=False,
                show_pareto_distance=False,
                show_nash_distance=False,
                show_kalai_distance=False,
                show_max_welfare_distance=False,
                show_max_relative_welfare_distance=False,
                show_end_reason=False,
                show_reserved=True,
                show_total_time=False,
                show_relative_time=False,
                show_n_steps=False,
            )
            plt.close()


@main.command(help="Displays ANL and NegMAS versions")
def version():
    print(f"anl: {anl.__version__} (NegMAS: {negmas.__version__})")


if __name__ == "__main__":
    main()
