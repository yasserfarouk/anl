import random

from negmas.outcomes import Outcome
from negmas.preferences import PresortingInverseUtilityFunction
from negmas.sao import ResponseType, SAONegotiator, SAOResponse, SAOState
from negmas.sao.negotiators import (
    AspirationNegotiator,
    BoulwareTBNegotiator,
    ConcederTBNegotiator,
    LinearTBNegotiator,
    NaiveTitForTatNegotiator,
)

__all__ = ["Linear", "Conceder", "Boulware", "MiCRO", "NaiveTitForTat"]


class NaiveTitForTat(NaiveTitForTatNegotiator):
    """
    A simple behavioral strategy that assumes a zero-sum game
    """


class StochasticLinear(AspirationNegotiator):
    """
    Time-based linear negotiation strategy (offers above the limit instead of at it)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            max_aspiration=1.0,
            aspiration_type="linear",
            tolerance=0.00001,
            stochastic=True,
            presort=True,
            **kwargs
        )


class StochasticConceder(AspirationNegotiator):
    """
    Time-based conceder negotiation strategy (offers above the limit instead of at it)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            max_aspiration=1.0,
            aspiration_type="conceder",
            tolerance=0.00001,
            stochastic=True,
            presort=True,
            **kwargs
        )


class StochasticBoulware(AspirationNegotiator):
    """
    Time-based boulware negotiation strategy (offers above the limit instead of at it)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            max_aspiration=1.0,
            aspiration_type="boulware",
            tolerance=0.00001,
            stochastic=True,
            presort=True,
            **kwargs
        )


class Linear(LinearTBNegotiator):
    """
    Time-based linear negotiation strategy
    """

    ...


class Conceder(ConcederTBNegotiator):
    """
    Time-based conceder negotiation strategy
    """


class Boulware(BoulwareTBNegotiator):
    """
    Time-based boulware negotiation strategy
    """


class MiCRO(SAONegotiator):
    """
    A simple implementation of the MiCRO negotiation strategy

    Remarks:
        - This is a simplified implementation of the MiCRO strategy.
        - It is not guaranteed to exactly match the published work.
        - MiCRO was introduced here:
          de Jonge, Dave. "An Analysis of the Linear Bilateral ANAC Domains Using the MiCRO Benchmark Strategy."
          Proceedings of the Thirty-First International Joint Conference on Artificial Intelligence, IJCAI. 2022.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # initialize local variables
        self.next_indx: int = 0
        self.sorter = None
        self._received, self._sent = set(), set()

    def __call__(self, state: SAOState) -> SAOResponse:
        """The main implementation of the MiCRO strategy"""
        assert self.ufun
        # initialize the sorter (This should better be done in on_negotiation_start() to allow for reuse but this is not needed in ANL)
        if self.sorter is None:
            # A sorter, sorts a ufun and can be used to get outcomes using their utiility
            self.sorter = PresortingInverseUtilityFunction(
                self.ufun, rational_only=True, eps=-1, rel_eps=-1
            )
            # Initialize the sorter. This is an O(nlog n) operation where n is the number of outcomes
            self.sorter.init()
        offer = state.current_offer
        # check whether the offer I received is acceptable
        response = ResponseType.REJECT_OFFER
        # check if the offer is acceptable (if one is received)

        # find my next offer (or best so far if I am not conceding)
        will_concede = len(self._sent) <= len(self._received)
        if not will_concede:
            outcome = self.sorter.outcome_at(self.next_indx - 1)
        else:
            # If I cannot concede, I will use my best offer so far (last one I sent)
            outcome = self.sorter.outcome_at(self.next_indx)
            if outcome is None and self.next_indx > 0:
                outcome = self.sorter.outcome_at(self.next_indx - 1)
                will_concede = False

        # If I received something, check for acceptance
        if offer is not None:
            self._received.add(offer)
            # The Acceptance Policy of MiCRO
            # accept if the offer is not worse than my next offer if I am conceding or the best so far if I am not
            if self.ufun.is_not_worse(offer, outcome):
                return SAOResponse(ResponseType.ACCEPT_OFFER, offer)

        # I will repeat a past offer in any of the following conditions:
        # 1. My next offer is worse than disagreement
        # 2. I am not ready to concede (i.e. I already sent more unique offers than the unique offers I received)
        # The only way, outcome will still be None is if I have no rational outcomes at all. Should never happen in ANL 2024
        if not will_concede or outcome is None or self.ufun.is_worse(outcome, None):
            return SAOResponse(response, self.sample_sent())
        # I am willing and can concede. Concede by one outcome
        self.next_indx += 1
        self._sent.add(outcome)
        return SAOResponse(response, outcome)

    def sample_sent(self) -> Outcome | None:
        # Get an outcome from the set I sent so far (or my best if I sent nothing)
        if not len(self._sent):
            assert self.sorter is not None
            return self.sorter.best()
        return random.choice(list(self._sent))
