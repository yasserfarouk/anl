# ANL Reference
This package provides a wrapper around NegMAS functionality to generate and run tournaments a la ANL 2024 competition.
You mostly only need to use `anl2024_tournament` in your code. The other helpers are provided to allow for a finer control over the scenarios used.

## Example Negotiators

The package provides few example negotiators. Of special importance is the `MiCRO` negotiator which provides a full implementation of a recently proposed behavioral strategy.
Other negotiators are just wrappers over negotiators provided by NegMAS.


### class: MiCRO
::: anl.anl2024.negotiators.builtins.micro.MiCRO

### class: NashSeeker
::: anl.anl2024.negotiators.builtins.nash_seeker.NashSeeker

### class: RVFitter
::: anl.anl2024.negotiators.builtins.rv_fitter.RVFitter

### class: Boulware
::: anl.anl2024.negotiators.builtins.wrappers.Boulware

### class: Linear
::: anl.anl2024.negotiators.builtins.wrappers.Linear

### class: Conceder
::: anl.anl2024.negotiators.builtins.wrappers.Conceder

### class: StochasticBoulware
::: anl.anl2024.negotiators.builtins.wrappers.StochasticBoulware

### class: StochasticLinear
::: anl.anl2024.negotiators.builtins.wrappers.StochasticLinear

### class: Conceder
::: anl.anl2024.negotiators.builtins.wrappers.StochasticConceder

### class: NaiveTitForTat
::: anl.anl2024.negotiators.builtins.wrappers.NaiveTitForTat
## Tournaments

### function: anl2024_tournament
::: anl.anl2024.anl2024_tournament

### constant: DEFAULT_AN2024_COMPETITORS
::: anl.anl2024.DEFAULT_AN2024_COMPETITORS

### constant: DEFAULT_TOURNAMENT_PATH
::: anl.anl2024.DEFAULT_TOURNAMENT_PATH

### constant: DEFAULT2024SETTINGS
::: anl.anl2024.DEFAULT2024SETTINGS

## Helpers (Scenario Generation)

### type: ScenarioGenerator
::: anl.anl2024.ScenarioGenerator

### function: mixed_scenarios
::: anl.anl2024.mixed_scenarios

### function: pie_scenarios
::: anl.anl2024.pie_scenarios

### function: arbitrary_pie_scenarios
::: anl.anl2024.arbitrary_pie_scenarios

### function: monotonic_pie_scenarios
::: anl.anl2024.monotonic_pie_scenarios

### function: zerosum_pie_scenarios
::: anl.anl2024.zerosum_pie_scenarios


