import random
from math import exp, log
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
from negmas.helpers.strings import unique_name
from negmas.inout import LinearAdditiveUtilityFunction, Scenario
from negmas.negotiators import Negotiator
from negmas.outcomes import make_issue, make_os
from negmas.preferences import LinearAdditiveUtilityFunction as U
from negmas.preferences.value_fun import TableFun
from negmas.sao.mechanism import SAOMechanism
from negmas.tournaments.neg.simple import SimpleTournamentResults, cartesian_tournament

from anl.anl2024.negotiators.builtins import Boulware, Conceder, Linear

# from anl.anl2024.negotiators.builtin import (
#     StochasticBoulware,
#     StochasticConceder,
#     StochasticLinear,
# )

__all__ = [
    "make_divide_the_pie_scenarios",
    "anl2024_tournament",
    "DEFAULT_AN2024_COMPETITORS",
    "DEFAULT_TOURNAMENT_PATH",
    "RESERVED_RANGES",
]

DEFAULT_AN2024_COMPETITORS = (
    Conceder,
    Linear,
    Boulware,
    # StochasticLinear,
    # StochasticConceder,
    # StochasticBoulware,
)
"""Default set of negotiators (agents) used as competitors"""

DEFAULT_TOURNAMENT_PATH = Path.home() / "negmas" / "anl2024" / "tournaments"
"""Default location to store tournament logs"""

RESERVED_RANGES = tuple[tuple[float, float], tuple[float, float]]


def onein(x: int | tuple[int, int], log_uniform: bool) -> int:
    if isinstance(x, tuple):
        if x[0] == x[-1]:
            return x[0]
        if log_uniform:
            l = [log(_) for _ in x]
            return min(
                x[1], max(x[0], int(exp(random.random() * (l[1] - l[0]) + l[0])))
            )

        return random.randint(*x)
    return x


def make_divide_the_pie_scenarios(
    n_scenarios: int = 20,
    n_outcomes: int | tuple[int, int] = 100,
    *,
    reserved_ranges: RESERVED_RANGES = ((0.0, 0.999999), (0.0, 0.999999)),
    log_range: bool = True,
    monotonic=False,
) -> list[Scenario]:
    """Creates single-issue scenarios with arbitrary/monotonically increasing utility functions

    Args:
        n_scenarios: Number of scenarios to create
        n_outcomes: Number of outcomes per scenario (if a tuple it will be interpreted as a min/max range to sample n. outcomes from).
        reserved_ranges: Ranges of reserved values for first and second negotiators
        log_range: If given, the distribution used will be uniform on the logarithm of n. outcomes (only used when n_outcomes is a 2-valued tuple).
        monotonic: If true all ufuns are monotonically increasing in the portion of the pie

    Remarks:
        - When n_outcomes is a tuple, the number of outcomes for each outcome will be sampled independently
    """
    ufun_sets = []
    base_name = "DivideTyePie" if monotonic else "S"

    def normalize(x):
        mn, mx = x.min(), x.max()
        return ((x - mn) / (mx - mn)).tolist()

    def make_monotonic(x, i):
        x = np.sort(np.asarray(x), axis=None)

        if i:
            x = x[::-1]
        r = random.random()
        if r < 0.33:
            x = np.exp(x)
        elif r < 0.67:
            x = np.log(x)
        else:
            pass
        return normalize(x)

    max_jitter_level = 0.8
    for i in range(n_scenarios):
        n = onein(n_outcomes, log_range)
        issues = (
            make_issue(
                [f"{i}_{n-1 - i}" for i in range(n)],
                "portions" if not monotonic else "i1",
            ),
        )
        # funs = [
        #     dict(
        #         zip(
        #             issues[0].all,
        #             # adjust(np.asarray([random.random() for _ in range(n)])),
        #             generate(n, i),
        #         )
        #     )
        #     for i in range(2)
        # ]
        os = make_os(issues, name=f"{base_name}{i}")
        outcomes = list(os.enumerate_or_sample())
        ufuns = U.generate_bilateral(
            outcomes,
            conflict_level=0.5 + 0.5 * random.random(),
            conflict_delta=random.random(),
        )
        jitter_level = random.random() * max_jitter_level
        funs = [
            np.asarray([float(u(_)) for _ in outcomes])
            + np.random.random() * jitter_level
            for u in ufuns
        ]

        if monotonic:
            funs = [make_monotonic(x, i) for i, x in enumerate(funs)]
        else:
            funs = [normalize(x) for x in funs]
        ufun_sets.append(
            tuple(
                U(
                    values=(TableFun(dict(zip(issues[0].all, vals))),),
                    name=f"{uname}{i}",
                    reserved_value=(r[0] + random.random() * (r[1] - r[0] - 1e-8)),
                    outcome_space=os,
                )
                for (uname, r, vals) in zip(("First", "Second"), reserved_ranges, funs)
            )
        )

    return [
        Scenario(
            outcome_space=ufuns[0].outcome_space,  # type: ignore We are sure this is not None
            ufuns=ufuns,
        )
        for ufuns in ufun_sets
    ]


def make_arbitrary_divide_the_pie_scenarios(
    n_scenarios: int = 20,
    n_outcomes: int | tuple[int, int] = 100,
    *,
    reserved_ranges: RESERVED_RANGES = ((0.0, 0.999999), (0.0, 0.999999)),
    log_range: bool = True,
) -> list[Scenario]:
    return make_divide_the_pie_scenarios(
        n_scenarios,
        n_outcomes,
        reserved_ranges=reserved_ranges,
        log_range=log_range,
        monotonic=False,
    )


def make_monotonic_divide_the_pie_scenarios(
    n_scenarios: int = 20,
    n_outcomes: int | tuple[int, int] = 100,
    *,
    reserved_ranges: RESERVED_RANGES = ((0.0, 0.999999), (0.0, 0.999999)),
    log_range: bool = True,
) -> list[Scenario]:
    return make_divide_the_pie_scenarios(
        n_scenarios,
        n_outcomes,
        reserved_ranges=reserved_ranges,
        log_range=log_range,
        monotonic=True,
    )


def make_zerosum_divide_the_pie_scenarios(
    n_scenarios: int = 20,
    n_outcomes: int | tuple[int, int] = 100,
    *,
    reserved_ranges: RESERVED_RANGES = ((0.0, 0.499999), (0.0, 0.499999)),
    log_range: bool = True,
) -> list[Scenario]:
    """Creates scenarios all of the DivideThePie variety with proportions giving utility

    Args:
        n_scenarios: Number of scenarios to create
        n_outcomes: Number of outcomes per scenario (if a tuple it will be interpreted as a min/max range to sample n. outcomes from).
        reserved_ranges: Ranges of reserved values for first and second negotiators
        log_range: If given, the distribution used will be uniform on the logarithm of n. outcomes (only used when n_outcomes is a 2-valued tuple).

    Remarks:
        - When n_outcomes is a tuple, the number of outcomes for each outcome will be sampled independently
    """
    ufun_sets = []
    for i in range(n_scenarios):
        n = onein(n_outcomes, log_range)
        issues = (make_issue([f"{i}_{n-1 - i}" for i in range(n)], "portions"),)
        ufun_sets.append(
            tuple(
                U(
                    values=(
                        TableFun(
                            {
                                _: int(str(_).split("_")[k]) / (n - 1)
                                for _ in issues[0].all
                            }
                        ),
                    ),
                    name=f"{uname}{i}",
                    reserved_value=(r[0] + random.random() * (r[1] - r[0] - 1e-8)),
                    outcome_space=make_os(issues, name=f"DivideTyePie{i}"),
                )
                for k, (uname, r) in enumerate(
                    zip(("First", "Second"), reserved_ranges)
                )
            )
        )

    return [
        Scenario(
            outcome_space=ufuns[0].outcome_space,  # type: ignore We are sure this is not None
            ufuns=ufuns,
        )
        for ufuns in ufun_sets
    ]


GENERAROR_MAP = dict(
    monotonic=make_monotonic_divide_the_pie_scenarios,
    arbitrary=make_arbitrary_divide_the_pie_scenarios,
    zerosum=make_zerosum_divide_the_pie_scenarios,
)


def anl2024_tournament(
    n_scenarios: int = 20,
    n_outcomes: int | tuple[int, int] = (1, 100_000),
    competitors: tuple[type[Negotiator] | str, ...]
    | list[type[Negotiator] | str] = DEFAULT_AN2024_COMPETITORS,
    competitor_params: Sequence[dict | None] | None = None,
    rotate_ufuns: bool = True,
    n_repetitions: int = 5,
    n_steps: int | tuple[int, int] | None = (10, 100_1000),
    time_limit: float | tuple[float, float] | None = 60,
    pend: float | tuple[float, float] = 0.0,
    pend_per_second: float | tuple[float, float] = 0.0,
    step_time_limit: float | tuple[float, float] | None = None,
    negotiator_time_limit: float | tuple[float, float] | None = None,
    name: str | None = None,
    nologs: bool = False,
    njobs: int = 0,
    plot_fraction: float = 0.2,
    verbosity: int = 1,
    self_play: bool = True,
    randomize_runs: bool = True,
    save_every: int = 0,
    save_stats: bool = True,
    known_partner: bool = False,
    final_score: tuple[str, str] = ("advantage", "mean"),
    base_path: Path | None = None,
    scenario_generator: str
    | Callable[[int, int | tuple[int, int]], list[Scenario]] = "arbitrary",
    plot_params: dict[str, Any] | None = None,
) -> SimpleTournamentResults:
    """Runs an ANL 2024 tournament

    Args:
        n_scenarios: Number of negotiation scenarios
        n_outcomes: Number of outcomes (or a min/max tuple of n. outcomes) for each scenario
        competitors: list of competitor agents
        competitor_params: If given, parameters to construct each competitor
        rotate_ufuns: If given, each scenario will be tried with both orders of the ufuns.
        n_repetitions: Number of times to repeat each negotiation
        n_steps: Number of steps/rounds allowed for the each negotiation (None for no-limit and a 2-valued tuple for sampling from a range)
        time_limit: Number of seconds allowed for the each negotiation (None for no-limit and a 2-valued tuple for sampling from a range)
        pend: Probability of ending the negotiation every step/round (None for no-limit and a 2-valued tuple for sampling from a range)
        pend_per_second: Probability of ending the negotiation every second (None for no-limit and a 2-valued tuple for sampling from a range)
        step_time_limit: Time limit for every negotiation step (None for no-limit and a 2-valued tuple for sampling from a range)
        negotiator_time_limit: Time limit for all actions of every negotiator (None for no-limit and a 2-valued tuple for sampling from a range)
        name: Name of the tournament
        nologs: If given, no logs will be saved
        njobs: Number of parallel jobs to use. -1 for serial and 0 for all cores
        plot_fraction: Fraction of negotiations to plot. Only used if not nologs
        verbosity: Verbosity level. The higher the more verbose
        self_play: Allow negotiators to run against themselves.
        randomize_runs: Randomize the order of negotiations
        save_every: Save logs every this number of negotiations
        save_stats: Save statistics for scenarios
        known_partner: Allow negotiators to know the type of their partner (through their ID)
        final_score: The metric and statistic used to calculate the score. Metrics are: advantage, utility, welfare, partner_welfare and Stats are: median, mean, std, min, max
        base_path: Folder in which to generate the logs folder for this tournament. Default is ~/negmas/anl2024/tournaments
        scenario_generator: An alternative method for generating bilateral negotiation scenarios. Must receive the number of scenarios and number of outcomes.
        plot_params: If given, overrides plotting parameters. See `nemgas.sao.SAOMechanism.plot()` for all parameters

    Returns:
        Tournament results as a `SimpleTournamentResults` object.
    """
    if isinstance(scenario_generator, str):
        scenario_generator = GENERAROR_MAP[scenario_generator]
    all_outcomes = not scenario_generator == make_zerosum_divide_the_pie_scenarios
    if nologs:
        path = None
    elif base_path is not None:
        path = Path(base_path) / (name if name else unique_name("anl"))
    else:
        path = DEFAULT_TOURNAMENT_PATH / (name if name else unique_name("anl"))
    params = dict(
        ylimits=(0, 1),
        mark_offers_view=True,
        mark_pareto_points=all_outcomes,
        mark_all_outcomes=all_outcomes,
        mark_nash_points=True,
        mark_kalai_points=all_outcomes,
        mark_max_welfare_points=all_outcomes,
        show_agreement=True,
        show_pareto_distance=False,
        show_nash_distance=True,
        show_kalai_distance=False,
        show_max_welfare_distance=False,
        show_max_relative_welfare_distance=False,
        show_end_reason=True,
        show_annotations=not all_outcomes,
        show_reserved=True,
        show_total_time=True,
        show_relative_time=True,
        show_n_steps=True,
    )
    if plot_params:
        params = params.update(plot_params)
    return cartesian_tournament(
        competitors=tuple(competitors),
        scenarios=scenario_generator(n_scenarios, n_outcomes),
        competitor_params=competitor_params,
        rotate_ufuns=rotate_ufuns,
        n_repetitions=n_repetitions,
        path=path,
        njobs=njobs,
        mechanism_type=SAOMechanism,
        n_steps=n_steps,
        time_limit=time_limit,
        pend=pend,
        pend_per_second=pend_per_second,
        step_time_limit=step_time_limit,
        negotiator_time_limit=negotiator_time_limit,
        mechanism_params=None,
        plot_fraction=plot_fraction,
        verbosity=verbosity,
        self_play=self_play,
        randomize_runs=randomize_runs,
        save_every=save_every,
        save_stats=save_stats,
        final_score=final_score,
        id_reveals_type=known_partner,
        name_reveals_type=True,
        plot_params=params,
    )


if __name__ == "__main__":
    anl2024_tournament(
        # competitors=(StochasticBoulware, StochasticLinear),
        n_scenarios=5,
        n_repetitions=3,
        n_outcomes=10,
        verbosity=2,
        njobs=-1,
    )
