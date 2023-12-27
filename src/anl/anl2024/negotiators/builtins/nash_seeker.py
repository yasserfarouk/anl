import random

from negmas import nash_points, pareto_frontier
from negmas.outcomes import Outcome
from negmas.sao import ResponseType, SAONegotiator, SAOResponse, SAOState

__all__ = ["NashSeeker"]


class NashSeeker(SAONegotiator):
    """Assumes that the opponent has a fixed reserved value and seeks the Nash equilibrium.

    Args:
        opponent_reserved_value: Assumed reserved value for the opponent
        nash_factor: Fraction (or multiple) of the agent utility at the Nash Point (assuming the `opponent_reserved_value`) that is acceptable

    """

    def __init__(
        self, *args, opponent_reserved_value: float = 0.25, nash_factor=0.9, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._opponent_r = opponent_reserved_value
        self._outcomes: list[Outcome] = []
        self._min_acceptable = float("inf")
        self._nash_factor = nash_factor
        self._best: Outcome = None  # type: ignore

    def on_preferences_changed(self, changes):
        _ = changes  # silenting a typing warning
        # This callback is called at the start of the negotiation after the ufun is set
        assert self.ufun is not None and self.ufun.outcome_space is not None
        # save my best outcome for later use
        self._best = self.ufun.best()
        # check that I have access to  the opponent ufun
        assert self.opponent_ufun is not None
        # set the reserved value of the opponent
        self.opponent_ufun.reserved_value = self._opponent_r
        # consider my and my parther's ufuns
        ufuns = (self.ufun, self.opponent_ufun)
        # list all outcomes
        outcomes = list(self.ufun.outcome_space.enumerate_or_sample())
        # find the pareto-front and the nash point
        frontier_utils, frontier_indices = pareto_frontier(ufuns, outcomes)
        frontier_outcomes = [outcomes[_] for _ in frontier_indices]
        my_frontier_utils = [_[0] for _ in frontier_utils]
        nash = nash_points(ufuns, frontier_utils)  # type: ignore
        if nash:
            # find my utility at the Nash Bargaining Solution.
            my_nash_utility = nash[0][0][0]
        else:
            my_nash_utility = 0.5 * (float(self.ufun.max()) + self.ufun.reserved_value)
        # Set the acceptable utility limit
        self._min_acceptable = my_nash_utility * self._nash_factor
        # Set the set of outcomes to offer from
        self._outcomes = [
            w
            for u, w in zip(my_frontier_utils, frontier_outcomes)
            if u >= self._min_acceptable
        ]

    def __call__(self, state: SAOState) -> SAOResponse:
        # just assert that I have a ufun and I know the outcome space.
        assert self.ufun is not None and self.ufun.outcome_space is not None
        # read the current offer from the state. None means I am starting the negotiation
        offer = state.current_offer
        # Accept the offer if its utility is higher than my utility at the Nash Bargaining Solution with the assumed opponent ufun
        if offer and float(self.ufun(offer)) >= self._min_acceptable:
            return SAOResponse(ResponseType.ACCEPT_OFFER, offer)
        # If I could not find the Nash Bargaining Solution, just offer my best outcome forever.
        if not self._outcomes:
            return SAOResponse(ResponseType.REJECT_OFFER, self._best)
        # Offer some outcome with high utility relative to the Nash Bargaining Solution
        return SAOResponse(ResponseType.REJECT_OFFER, random.choice(self._outcomes))
