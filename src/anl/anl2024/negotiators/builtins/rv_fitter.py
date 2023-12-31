import random

import numpy as np
from negmas import Outcome, ResponseType, SAONegotiator, SAOResponse, SAOState
from scipy.optimize import curve_fit

__all__ = ["RVFitter"]


def aspiration_function(t, mx, rv, e):
    return (mx - rv) * (1.0 - np.power(t, e)) + rv


class RVFitter(SAONegotiator):
    """A simple negotiator that uses curve fitting to learn the reserved value.

    Args:
        min_unique_utilities: Number of different offers from the opponent before starting to
                              attempt learning their reserved value.
        e: The concession exponent used for the agent's offering strategy
        stochasticity: The level of stochasticity in the offers.
        enable_logging: If given, a log will be stored  for the estimates.

    Remarks:

        - Assumes that the opponent is using a time-based offering strategy that offers
          the outcome at utility $u(t) = (u_0 - r) - r \\exp(t^e)$ where $u_0$ is the utility of
          the first offer (directly read from the opponent ufun), $e$ is an exponent that controls the
          concession rate and $r$ is the reserved value we want to learn.
        - After it receives offers with enough different utilities, it starts finding the optimal values
          for $e$ and $r$.
        - When it is time to respond, RVFitter, calculates the set of rational outcomes **for both agents**
          based on its knowledge of the opponent ufun (given) and reserved value (learned). It then applies
          the same concession curve defined above to concede over an ordered list of these outcomes.
        - Is this better than using the same concession curve on the outcome space without even trying to learn
          the opponent reserved value? Maybe sometimes but empirical evaluation shows that it is not in general.
        - Note that the way we check for availability of enough data for training is based on the uniqueness of
          the utility of offers from the opponent (for the opponent). Given that these are real values, this approach
          is suspect because of rounding errors. If two outcomes have the same utility they may appear to have different
          but very close utilities because or rounding errors (or genuine very small differences). Such differences should
          be ignored.
        - Note also that we start assuming that the opponent reserved value is 0.0 which means that we are only restricted
          with our own reserved values when calculating the rational outcomes. This is the best case scenario for us because
          we have MORE negotiation power when the partner has LOWER utility.
    """

    def __init__(
        self,
        *args,
        min_unique_utilities: int = 10,
        e: float = 5.0,
        stochasticity: float = 0.1,
        enable_logging: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.min_unique_utilities = min_unique_utilities
        self.e = e
        self.stochasticity = stochasticity
        # keeps track of times at which the opponent offers
        self.opponent_times: list[float] = []
        # keeps track of opponent utilities of its offers
        self.opponent_utilities: list[float] = []
        # keeps track of the our last estimate of the opponent reserved value
        self._past_oppnent_rv = 0.0
        # keeps track of the rational outcome set given our estimate of the
        # opponent reserved value and our knowledge of ours
        self._rational: list[tuple[float, float, Outcome]] = []
        self._enable_logging = enable_logging

    def __call__(self, state: SAOState) -> SAOResponse:
        assert self.ufun and self.opponent_ufun
        # update the opponent reserved value in self.opponent_ufun
        self.update_reserved_value(state)
        # rune the acceptance strategy and if the offer received is acceptable, accept it
        if self.is_acceptable(state):
            return SAOResponse(ResponseType.ACCEPT_OFFER, state.current_offer)
        # The offering strategy
        # We only update our estimate of the rational list of outcomes if it is not set or
        # there is a change in estimated reserved value
        if (
            not self._rational
            or abs(self.opponent_ufun.reserved_value - self._past_oppnent_rv) > 1e-3
        ):
            # The rational set of outcomes sorted dependingly according to our utility function
            # and the opponent utility function (in that order).
            self._rational = sorted(
                [
                    (my_util, opp_util, _)
                    for _ in self.nmi.outcome_space.enumerate_or_sample(
                        levels=10, max_cardinality=100_000
                    )
                    if (my_util := float(self.ufun(_))) > self.ufun.reserved_value
                    and (opp_util := float(self.opponent_ufun(_)))
                    > self.opponent_ufun.reserved_value
                ],
            )
        # If there are no rational outcomes (i.e. our estimate of the opponent rv is very wrogn),
        # then just revert to offering our top offer
        if not self._rational:
            return SAOResponse(ResponseType.REJECT_OFFER, self.ufun.best())
        # find our aspiration level (value between 0 and 1) the higher the higher utility we require
        asp = aspiration_function(state.relative_time, 1.0, 0.0, self.e)
        # find the index of the rational outcome at the aspiration level (in the rational set of outcomes)
        n_rational = len(self._rational)
        max_rational = n_rational - 1
        min_indx = max(0, min(max_rational, int(asp * max_rational)))
        # find current stochasticity which goes down from the set level to zero linearly
        s = aspiration_function(state.relative_time, self.stochasticity, 0.0, 1.0)
        # find the index of the maximum utility we require based on stochasticity (going down over time)
        max_indx = max(0, min(int(min_indx + s * n_rational), max_rational))
        # offer an outcome in the selected range
        indx = random.randint(min_indx, max_indx) if min_indx != max_indx else min_indx
        outcome = self._rational[indx][-1]
        return SAOResponse(ResponseType.REJECT_OFFER, outcome)

    def is_acceptable(self, state: SAOState) -> bool:
        # The acceptance strategy
        assert self.ufun and self.opponent_ufun
        # get the offer from the mechanism state
        offer = state.current_offer
        # If there is no offer, there is nothing to accept
        if offer is None:
            return False
        # Find the current aspiration level
        asp = aspiration_function(
            state.relative_time, 1.0, self.ufun.reserved_value, self.e
        )
        # accept if the utility of the received offer is higher than
        # the current aspiration
        return float(self.ufun(offer)) >= asp

    def update_reserved_value(self, state: SAOState):
        # Learns the reserved value of the partner
        assert self.opponent_ufun is not None
        # extract the current offer from the state
        offer = state.current_offer
        if offer is None:
            return
        # save to the list of utilities received from the opponent and their times
        self.opponent_utilities.append(float(self.opponent_ufun(offer)))
        self.opponent_times.append(state.relative_time)

        # If we do not have enough data, just assume that the opponent
        # reserved value is zero
        n_unique = len(set(self.opponent_utilities))
        if n_unique < self.min_unique_utilities:
            self._past_oppnent_rv = 0.0
            self.opponent_ufun.reserved_value = 0.0
            return
        # Use curve fitting to estimate the opponent reserved value
        # We assume the following:
        # - The opponent is using a concession strategy with an exponent between 0.2, 5.0
        # - The opponent never offers outcomes lower than their reserved value which means
        #   that their rv must be no higher than the worst outcome they offered for themselves.
        bounds = ((0.2, 0.0), (5.0, min(self.opponent_utilities)))
        err = ""
        try:
            optimal_vals, _ = curve_fit(
                lambda x, e, rv: aspiration_function(
                    x, self.opponent_utilities[0], rv, e
                ),
                self.opponent_times,
                self.opponent_utilities,
                bounds=bounds,
            )
            self._past_oppnent_rv = self.opponent_ufun.reserved_value
            self.opponent_ufun.reserved_value = optimal_vals[1]
        except Exception as e:
            err, optimal_vals = f"{str(e)}", [None, None]

        # log my estimate
        if self._enable_logging:
            self.nmi.log_info(
                self.id,
                dict(
                    estimated_rv=self.opponent_ufun.reserved_value,
                    n_unique=n_unique,
                    opponent_utility=self.opponent_utilities[-1],
                    estimated_exponent=optimal_vals[0],
                    estimated_max=self.opponent_utilities[0],
                    error=err,
                ),
            )
