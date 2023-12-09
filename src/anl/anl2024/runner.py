import random
from pathlib import Path
from typing import Sequence

from negmas.helpers.strings import unique_name
from negmas.inout import Scenario
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
    "make_scenarios",
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


def make_scenarios(
    n_outcomes: int = 100,
    n_scenarios: int = 20,
    reserved_ranges: RESERVED_RANGES = ((0.0, 0.5), (0.0, 0.5)),
) -> list[Scenario]:
    """Creates `n_scenarios` scenarios of the divide-the-pie domain all of `n_outcomes`
    outcomes and with different reserved value combinations that fall within `reserved_ranges`
    """
    issues = (
        make_issue([f"{i}_{n_outcomes-1 - i}" for i in range(n_outcomes)], "portions"),
    )
    ufun_sets = [
        tuple(
            U(
                values=(
                    TableFun(
                        {
                            _: int(str(_).split("_")[k]) / (n_outcomes - 1)
                            for _ in issues[0].all
                        }
                    ),
                ),
                name=f"{uname}{i}",
                reserved_value=(r[0] + 1e-8 + random.random() * (r[1] - r[0] - 1e-8)),
                outcome_space=make_os(issues, name=f"DivideTyePie{i}"),
            )
            for k, (uname, r) in enumerate(zip(("First", "Second"), reserved_ranges))
        )
        for i in range(n_scenarios)
    ]

    return [
        Scenario(
            outcome_space=ufuns[0].outcome_space,  # type: ignore We are sure this is not None
            ufuns=ufuns,
        )
        for ufuns in ufun_sets
    ]


def anl2024_tournament(
    n_scenarios: int = 20,
    n_outcomes: int = 100,
    competitors: tuple[type[Negotiator] | str, ...]
    | list[type[Negotiator] | str] = DEFAULT_AN2024_COMPETITORS,
    competitor_params: Sequence[dict | None] | None = None,
    rotate_ufuns: bool = True,
    n_repetitions: int = 5,
    n_steps: int | None = 100,
    time_limit: float | None = None,
    pend: float = 0.0,
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
) -> SimpleTournamentResults:
    if nologs:
        path = None
    else:
        path = DEFAULT_TOURNAMENT_PATH / (name if name else unique_name("anl"))
    return cartesian_tournament(
        competitors=tuple(competitors),
        scenarios=make_scenarios(n_outcomes=n_outcomes, n_scenarios=n_scenarios),
        competitor_params=competitor_params,
        rotate_ufuns=rotate_ufuns,
        n_repetitions=n_repetitions,
        path=path,
        njobs=njobs,
        mechanism_type=SAOMechanism,
        mechanism_params=dict(time_limit=time_limit, n_steps=n_steps, pend=pend),
        plot_fraction=plot_fraction,
        verbosity=verbosity,
        self_play=self_play,
        randomize_runs=randomize_runs,
        save_every=save_every,
        save_stats=save_stats,
        final_score=final_score,
        id_reveals_type=known_partner,
        name_reveals_type=True,
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
