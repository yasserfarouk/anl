from negmas import MappingUtilityFunction
from negmas.inout import SAOMechanism
from negmas.outcomes import make_issue, make_os
from negmas.preferences.generators import make_zero_sum_pareto

from anl.anl2024.negotiators.builtins import MiCRO
from anl.anl2024.runner import anl2024_tournament


def test_micro_agrees_with_itself():
    n_outcomes = 1000
    os = make_os([make_issue(n_outcomes)])
    ufun_values = make_zero_sum_pareto(n_outcomes)
    ufuns = [
        MappingUtilityFunction(
            dict(zip(os.enumerate_or_sample(), [_[i] for _ in ufun_values])),
            outcome_space=os,
            reserved_value=0.05 * i,
        )
        for i in range(2)
    ]
    m = SAOMechanism(n_steps=n_outcomes, outcome_space=os)
    for i in range(2):
        m.add(MiCRO(id=f"{i}", name=f"M{i}"), ufun=ufuns[i])
    m.run()
    assert m.agreement is not None


def test_micro_always_agrees_against_itself():
    results = anl2024_tournament(
        n_scenarios=50,
        competitors=[MiCRO],
        n_repetitions=1,
        nologs=True,
    )
    scores = results.scores

    failed_scenarios = scores.loc[
        (scores.strategy == "MiCRO")
        & (scores.partners == "MiCRO")
        & (scores.advantage < 0),
        "scenario",
    ].unique()
    assert not (failed_scenarios), f"Negative advanate: {failed_scenarios=}"
    failed_scenarios = scores.loc[
        (scores.strategy == "MiCRO")
        & (scores.partners == "MiCRO")
        & (scores.advantage < 1e-3),
        "scenario",
    ].unique()
    assert not (failed_scenarios), f"Failure to get agreement: {failed_scenarios=}"
