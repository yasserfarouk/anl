# ANL Reference
This package provides a wrapper around NegMAS functionality to generate and run tournaments a la ANL 2024 competition.
You mostly only need to use `anl2024_tournament` in your code. The other helpers are provided to allow for a finer control over the scenarios used.


## Example Negotiators

The package provides few example negotiators. Of special importance is the `MiCRO` negotiator which provides a full implementation of a recently proposed behavioral strategy.
Other negotiators are just wrappers over negotiators provided by NegMAS.


::: anl.anl2024.negotiators.builtins.micro.MiCRO

::: anl.anl2024.negotiators.builtins.nash_seeker.NashSeeker

::: anl.anl2024.negotiators.builtins.rv_fitter.RVFitter

::: anl.anl2024.negotiators.builtins.wrappers.Boulware

::: anl.anl2024.negotiators.builtins.wrappers.Linear

::: anl.anl2024.negotiators.builtins.wrappers.Conceder

::: anl.anl2024.negotiators.builtins.wrappers.StochasticBoulware

::: anl.anl2024.negotiators.builtins.wrappers.StochasticLinear

::: anl.anl2024.negotiators.builtins.wrappers.StochasticConceder

::: anl.anl2024.negotiators.builtins.wrappers.NaiveTitForTat

## Tournaments

::: anl.anl2024.anl2024_tournament

::: anl.anl2024.DEFAULT_AN2024_COMPETITORS

::: anl.anl2024.DEFAULT_TOURNAMENT_PATH

::: anl.anl2024.DEFAULT2024SETTINGS

## Helpers (Scenario Generation)

::: anl.anl2024.ScenarioGenerator

::: anl.anl2024.mixed_scenarios

::: anl.anl2024.pie_scenarios

::: anl.anl2024.arbitrary_pie_scenarios

::: anl.anl2024.monotonic_pie_scenarios

::: anl.anl2024.zerosum_pie_scenarios


