import random
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import numpy as np
from negmas.helpers.misc import intin
from negmas.helpers.strings import unique_name
from negmas.inout import Scenario, UtilityFunction, pareto_frontier
from negmas.negotiators import Negotiator
from negmas.outcomes import make_issue, make_os
from negmas.preferences import LinearAdditiveUtilityFunction as U
from negmas.preferences.generators import generate_utility_values
from negmas.preferences.ops import nash_points
from negmas.preferences.value_fun import TableFun
from negmas.sao.mechanism import SAOMechanism
from negmas.tournaments.neg.simple import SimpleTournamentResults, cartesian_tournament

from anl.anl2024.negotiators.builtins import (
    Boulware,
    Conceder,
    Linear,
    MiCRO,
    NaiveTitForTat,
)

# from anl.anl2024.negotiators.builtin import (
#     StochasticBoulware,
#     StochasticConceder,
#     StochasticLinear,
# )

__all__ = [
    "anl2024_tournament",
    "mixed_scenarios",
    "pie_scenarios",
    "arbitrary_pie_scenarios",
    "monotonic_pie_scenarios",
    "zerosum_pie_scenarios",
    "ScenarioGenerator",
    "DEFAULT_AN2024_COMPETITORS",
    "DEFAULT_TOURNAMENT_PATH",
    "DEFAULT2024SETTINGS",
]

DEFAULT_AN2024_COMPETITORS = (
    Conceder,
    Linear,
    Boulware,
    NaiveTitForTat,
    MiCRO,
    # StochasticLinear,
    # StochasticConceder,
    # StochasticBoulware,
)
"""Default set of negotiators (agents) used as competitors"""

DEFAULT_TOURNAMENT_PATH = Path.home() / "negmas" / "anl2024" / "tournaments"
"""Default location to store tournament logs"""

ReservedRanges = tuple[tuple[float, ...], ...]


def pie_scenarios(
    n_scenarios: int = 20,
    n_outcomes: int | tuple[int, int] | list[int] = 100,
    *,
    reserved_ranges: ReservedRanges = ((0.0, 0.999999), (0.0, 0.999999)),
    log_uniform: bool = True,
    monotonic=False,
) -> list[Scenario]:
    """Creates single-issue scenarios with arbitrary/monotonically increasing utility functions

    Args:
        n_scenarios: Number of scenarios to create
        n_outcomes: Number of outcomes per scenario. If a tuple it will be interpreted as a min/max range to sample n. outcomes from.
                    If a list, samples from this list will be used (with replacement).
        reserved_ranges: Ranges of reserved values for first and second negotiators
        log_uniform: If given, the distribution used will be uniform on the logarithm of n. outcomes (only used when n_outcomes is a 2-valued tuple).
        monotonic: If true all ufuns are monotonically increasing in the portion of the pie

    Remarks:
        - When n_outcomes is a tuple, the number of outcomes for each scenario will be sampled independently.
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
        n = intin(n_outcomes, log_uniform)
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
        ufuns = tuple(
            U(
                values=(TableFun(dict(zip(issues[0].all, vals))),),
                name=f"{uname}{i}",
                outcome_space=os,
                # reserved_value=(r[0] + random.random() * (r[1] - r[0] - 1e-8)),
            )
            for (uname, vals) in zip(("First", "Second"), funs)
            # for (uname, r, vals) in zip(("First", "Second"), reserved_ranges, funs)
        )
        sample_reserved_values(ufuns, reserved_ranges=reserved_ranges)
        ufun_sets.append(ufuns)

    return [
        Scenario(
            outcome_space=ufuns[0].outcome_space,  # type: ignore We are sure this is not None
            ufuns=ufuns,
        )
        for ufuns in ufun_sets
    ]


def arbitrary_pie_scenarios(
    n_scenarios: int = 20,
    n_outcomes: int | tuple[int, int] | list[int] = 100,
    *,
    reserved_ranges: ReservedRanges = ((0.0, 0.999999), (0.0, 0.999999)),
    log_uniform: bool = True,
) -> list[Scenario]:
    return pie_scenarios(
        n_scenarios,
        n_outcomes,
        reserved_ranges=reserved_ranges,
        log_uniform=log_uniform,
        monotonic=False,
    )


def monotonic_pie_scenarios(
    n_scenarios: int = 20,
    n_outcomes: int | tuple[int, int] | list[int] = 100,
    *,
    reserved_ranges: ReservedRanges = ((0.0, 0.999999), (0.0, 0.999999)),
    log_uniform: bool = True,
) -> list[Scenario]:
    return pie_scenarios(
        n_scenarios,
        n_outcomes,
        reserved_ranges=reserved_ranges,
        log_uniform=log_uniform,
        monotonic=True,
    )


def sample_reserved_values(
    ufuns: tuple[UtilityFunction, ...],
    pareto: tuple[tuple[float, ...], ...] | None = None,
    reserved_ranges: ReservedRanges = ((0.0, 1.0), (0.0, 1.0)),
    eps: float = 1e-3,
) -> tuple[float, ...]:
    """
    Samples reserved values that are guaranteed to allow some rational outcomes for the given ufuns and sets the reserved values.

    Args:
        ufuns: tuple of utility functions to sample reserved values for
        pareto: The pareto frontier. If not given, it will be calculated
        reserved_ranges: the range to sample reserved values from. Notice that the upper limit of this range will be updated
                         to ensure some rational outcoms
        eps: A small number indicating the absolute guaranteed margin of the sampled reserved value from the Nash point.

    """
    n_funs = len(ufuns)
    if pareto is None:
        pareto = pareto_frontier(ufuns)[0]
    assert pareto is not None, f"Cannot find the pareto frontier."
    nash = nash_points(ufuns, frontier=pareto, ranges=[(0, 1) for _ in range(n_funs)])
    if not nash:
        raise ValueError(
            f"Cannot find the Nash point so we cannot find the appropriate reserved ranges"
        )
    nash_utils = nash[0][0]
    if not reserved_ranges:
        reserved_ranges = tuple((0, 1) for _ in range(n_funs))
    reserved_ranges = tuple(
        tuple(min(r[_], n) for _ in range(n_funs))
        for n, r in zip(nash_utils, reserved_ranges)
    )
    reserved = tuple(
        r[0] + (r[1] - eps - r[0]) * random.random() for r in reserved_ranges
    )
    for u, r in zip(ufuns, reserved):
        u.reserved_value = float(r)
    return reserved


DEFAULT2024SETTINGS = dict(
    n_ufuns=2,
    n_scenarios=50,
    n_outcomes=(900, 1100),
    n_steps=(10, 10_000),
    n_repetitions=5,
    reserved_ranges=((0.0, 1.0), (0.0, 1.0)),
    competitors=DEFAULT_AN2024_COMPETITORS,
    rotate_ufuns=True,
    time_limit=60,
    pend=0,
    pend_per_second=0,
    step_time_limit=None,
    negotiator_time_limit=None,
    self_play=True,
    randomize_runs=True,
    known_partner=False,
    final_score=("advantage", "mean"),
    scenario_generator="mix",
    outcomes_log_uniform=True,
    generator_params=dict(
        reserved_ranges=((0.0, 1.0), (0.0, 1.0)),
        log_uniform=False,
        zerosum_fraction=0.05,
        monotonic_fraction=0.25,
        curve_fraction=0.5,
        pareto_first=False,
        n_pareto=(0.005, 0.5),
    ),
)
"""Default settings for ANL 2024"""


def mixed_scenarios(
    n_scenarios: int = DEFAULT2024SETTINGS["n_scenarios"],  # type: ignore
    n_outcomes: int
    | tuple[int, int]
    | list[int] = DEFAULT2024SETTINGS["n_outcomes"],  # type: ignore
    *,
    reserved_ranges: ReservedRanges = DEFAULT2024SETTINGS["reserved_ranges"],  # type: ignore
    log_uniform: bool = DEFAULT2024SETTINGS["outcomes_log_uniform"],  # type: ignore
    zerosum_fraction: float = DEFAULT2024SETTINGS["generator_params"]["zerosum_fraction"],  # type: ignore
    monotonic_fraction: float = DEFAULT2024SETTINGS["generator_params"]["monotonic_fraction"],  # type: ignore
    curve_fraction: float = DEFAULT2024SETTINGS["generator_params"]["curve_fraction"],  # type: ignore
    pareto_first: bool = DEFAULT2024SETTINGS["generator_params"]["pareto_first"],  # type: ignore
    n_ufuns: int = DEFAULT2024SETTINGS["n_ufuns"],  # type: ignore
    n_pareto: int | float | tuple[float | int, float | int] | list[int | float] = DEFAULT2024SETTINGS["generator_params"]["n_pareto"],  # type: ignore
    pareto_log_uniform: bool = True,
) -> list[Scenario]:
    """Generates a mix of zero-sum, monotonic and general scenarios

    Args:
        n_scenarios: Number of scenarios to genearate
        n_outcomes: Number of outcomes (or a list of range thereof).
        reserved_ranges: the range allowed for reserved values for each ufun.
                         Note that the upper limit will be overridden to guarantee
                         the existence of at least one rational outcome
        log_uniform: Use log-uniform instead of uniform sampling if n_outcomes is a tuple giving a range.
        zerosum_fraction: Fraction of zero-sum scenarios. These are original DivideThePie scenarios
        monotonic_fraction: Fraction of scenarios where each ufun is a monotonic function of the received pie.
        curve_fraction: Fraction of general and monotonic scenarios that use a curve for Pareto generation instead of
                        a piecewise linear Pareto frontier.
        pareto_first: If given, the Pareto frontier will always be in the first set of outcomes
        n_ufuns: Number of ufuns to generate per scenario
        n_pareto: Number of outcomes on the Pareto frontier in general scenarios.
                Can be specified as a number, a tuple of a min and max to sample within, a list of possibilities.
                Each value can either be an integer > 1 or a fraction of the number of outcomes in the scenario.
        pareto_log_uniform: Use log-uniform instead of uniform sampling if n_pareto is a tuple

    Returns:
        A list `Scenario` s
    """
    assert zerosum_fraction + monotonic_fraction <= 1.0
    nongeneral_fraction = zerosum_fraction + monotonic_fraction
    ufun_sets = []
    for i in range(n_scenarios):
        r = random.random()
        n = intin(n_outcomes, log_uniform)
        name = "S"
        if r < nongeneral_fraction:
            n_pareto_selected = n
            name = "DivideThePieGen"
        else:
            if isinstance(n_pareto, Iterable):
                n_pareto = type(n_pareto)(
                    int(_ * n + 0.5) if _ < 1 else int(_) for _ in n_pareto  # type: ignore
                )
            else:
                n_pareto = int(0.5 + n_pareto * n) if n_pareto < 1 else int(n_pareto)
            n_pareto_selected = intin(n_pareto, log_uniform=pareto_log_uniform)  # type: ignore
        if r < zerosum_fraction:
            vals = generate_utility_values(
                n_pareto_selected,
                n,
                n_ufuns=n_ufuns,
                pareto_first=pareto_first,
                pareto_generator="zero_sum",
            )
            name = "DivideThePie"
        else:
            vals = generate_utility_values(
                n_pareto_selected,
                n,
                n_ufuns=n_ufuns,
                pareto_first=pareto_first,
                pareto_generator="curve"
                if random.random() < curve_fraction
                else "piecewise_linear",
            )

        issues = (make_issue([f"{i}_{n-1 - i}" for i in range(n)], "portions"),)
        ufuns = tuple(
            U(
                values=(
                    TableFun(
                        {_: float(vals[i][k]) for i, _ in enumerate(issues[0].all)}
                    ),
                ),
                name=f"{uname}{i}",
                # reserved_value=(r[0] + random.random() * (r[1] - r[0] - 1e-8)),
                outcome_space=make_os(issues, name=f"{name}{i}"),
            )
            for k, uname in enumerate(("First", "Second"))
            # for k, (uname, r) in enumerate(zip(("First", "Second"), reserved_ranges))
        )
        sample_reserved_values(ufuns, reserved_ranges=reserved_ranges)
        ufun_sets.append(ufuns)

    return [
        Scenario(
            outcome_space=ufuns[0].outcome_space,  # type: ignore We are sure this is not None
            ufuns=ufuns,
        )
        for ufuns in ufun_sets
    ]


def zerosum_pie_scenarios(
    n_scenarios: int = 20,
    n_outcomes: int | tuple[int, int] | list[int] = 100,
    *,
    reserved_ranges: ReservedRanges = ((0.0, 0.499999), (0.0, 0.499999)),
    log_uniform: bool = True,
) -> list[Scenario]:
    """Creates scenarios all of the DivideThePie variety with proportions giving utility

    Args:
        n_scenarios: Number of scenarios to create
        n_outcomes: Number of outcomes per scenario (if a tuple it will be interpreted as a min/max range to sample n. outcomes from).
        reserved_ranges: Ranges of reserved values for first and second negotiators
        log_uniform: If given, the distribution used will be uniform on the logarithm of n. outcomes (only used when n_outcomes is a 2-valued tuple).

    Remarks:
        - When n_outcomes is a tuple, the number of outcomes for each outcome will be sampled independently
    """
    ufun_sets = []
    for i in range(n_scenarios):
        n = intin(n_outcomes, log_uniform)
        issues = (make_issue([f"{i}_{n-1 - i}" for i in range(n)], "portions"),)
        ufuns = tuple(
            U(
                values=(
                    TableFun(
                        {
                            _: float(int(str(_).split("_")[k]) / (n - 1))
                            for _ in issues[0].all
                        }
                    ),
                ),
                name=f"{uname}{i}",
                # reserved_value=(r[0] + random.random() * (r[1] - r[0] - 1e-8)),
                outcome_space=make_os(issues, name=f"DivideTyePie{i}"),
            )
            for k, uname in enumerate(("First", "Second"))
            # for k, (uname, r) in enumerate(zip(("First", "Second"), reserved_ranges))
        )
        sample_reserved_values(
            ufuns,
            pareto=tuple(
                tuple(u(_) for u in ufuns)
                for _ in make_os(issues).enumerate_or_sample()
            ),
            reserved_ranges=reserved_ranges,
        )
        ufun_sets.append(ufuns)

    return [
        Scenario(
            outcome_space=ufuns[0].outcome_space,  # type: ignore We are sure this is not None
            ufuns=ufuns,
        )
        for ufuns in ufun_sets
    ]


ScenarioGenerator = Callable[[int, int | tuple[int, int] | list[int]], list[Scenario]]
"""Type of callable that can be used for generating scenarios. It must receive the number of scenarios and number of outcomes (as int, tuple or list) and return a list of `Scenario` s"""

GENERAROR_MAP = dict(
    monotonic=monotonic_pie_scenarios,
    arbitrary=arbitrary_pie_scenarios,
    zerosum=zerosum_pie_scenarios,
    default=mixed_scenarios,
    mix=mixed_scenarios,
)

DEFAULT2024GENERATOR = mixed_scenarios
"""Default generator type for ANL 2024"""


def anl2024_tournament(
    n_scenarios: int = DEFAULT2024SETTINGS["n_scenarios"],  # type: ignore
    n_outcomes: int | tuple[int, int] | list[int] = DEFAULT2024SETTINGS["n_outcomes"],  # type: ignore
    competitors: tuple[type[Negotiator] | str, ...]
    | list[type[Negotiator] | str] = DEFAULT_AN2024_COMPETITORS,
    rotate_ufuns: bool = DEFAULT2024SETTINGS["rotate_ufuns"],  # type: ignore
    n_repetitions: int = DEFAULT2024SETTINGS["n_repetitions"],  # type: ignore
    n_steps: int | tuple[int, int] | None = DEFAULT2024SETTINGS["n_steps"],  # type: ignore
    time_limit: float | tuple[float, float] | None = DEFAULT2024SETTINGS["time_limit"],  # type: ignore
    pend: float | tuple[float, float] = DEFAULT2024SETTINGS["pend"],  # type: ignore
    pend_per_second: float
    | tuple[float, float] = DEFAULT2024SETTINGS["pend_per_second"],  # type: ignore
    step_time_limit: float
    | tuple[float, float]
    | None = DEFAULT2024SETTINGS["step_time_limit"],  # type: ignore
    negotiator_time_limit: float
    | tuple[float, float]
    | None = DEFAULT2024SETTINGS["negotiator_time_limit"],  # type: ignore
    self_play: bool = DEFAULT2024SETTINGS["self_play"],  # type: ignore
    randomize_runs: bool = DEFAULT2024SETTINGS["randomize_runs"],  # type: ignore
    known_partner: bool = DEFAULT2024SETTINGS["known_partner"],  # type: ignore
    final_score: tuple[str, str] = DEFAULT2024SETTINGS["final_score"],  # type: ignore
    scenario_generator: str
    | ScenarioGenerator = DEFAULT2024SETTINGS["scenario_generator"],  # type: ignore
    generator_params: dict[str, Any] | None = DEFAULT2024SETTINGS["generator_params"],  # type: ignore
    competitor_params: Sequence[dict | None] | None = None,
    name: str | None = None,
    nologs: bool = False,
    njobs: int = 0,
    plot_fraction: float = 0.2,
    verbosity: int = 1,
    save_every: int = 0,
    save_stats: bool = True,
    base_path: Path | None = None,
    plot_params: dict[str, Any] | None = None,
    raise_exceptions: bool = True,
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
        generator_params: Parameters passed to the scenario generator
        plot_params: If given, overrides plotting parameters. See `nemgas.sao.SAOMechanism.plot()` for all parameters

    Returns:
        Tournament results as a `SimpleTournamentResults` object.
    """
    if generator_params is None:
        generator_params = dict()
    if isinstance(scenario_generator, str):
        scenario_generator = GENERAROR_MAP[scenario_generator]
    all_outcomes = not scenario_generator == zerosum_pie_scenarios
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
        scenarios=scenario_generator(n_scenarios, n_outcomes, **generator_params),
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
        raise_exceptions=raise_exceptions,
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
