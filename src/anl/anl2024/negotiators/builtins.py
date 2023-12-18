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

    Args:
         name: Negotiator name
         parent: Parent controller if any
         preferences: The preferences of the negotiator
         ufun: The ufun of the negotiator (overrides preferences)
         owner: The `Agent` that owns the negotiator.

    Remarks:
        This negotiator implements the MiCRO strategy which concedes as slowly as possible as long as the partner is changing its offers

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.next_indx: int = 0
        self.sorter = None
        self._received = set()
        self._sent = set()
        self.accept_same = True

    def on_negotiation_start(self, state: SAOState) -> None:  # type: ignore
        assert self.ufun is not None and state.step == 0
        # A sorter, sorts a ufun and can be used to get outcomes using their utiility
        self.sorter = PresortingInverseUtilityFunction(
            self.ufun, rational_only=True, eps=-1, rel_eps=-1
        )
        # Initialize the sorter. This is an O(nlog n) operation where n is the number of outcomes
        self.sorter.init()
        # indicate that I am getting my best offer first
        self.next_indx = 0
        # I did not receive or send anything yet
        self._received = set()
        self._sent = set()

    def sample_sent(self) -> Outcome | None:
        # Get an outcome from the set I sent so far (or my best if I sent nothing)
        if not len(self._sent):
            assert self.sorter is not None
            return self.sorter.best()
        return random.choice(list(self._sent))

    def next_offer(self) -> Outcome | None:
        assert self.sorter is not None
        return self.sorter.outcome_at(self.next_indx)

    def best_offer_so_far(self) -> Outcome | None:
        assert self.sorter is not None
        if self.next_indx > 0:
            return self.sorter.outcome_at(self.next_indx - 1)
        return None

    def ready_to_concede(self) -> bool:
        # concede if I did not send more than the number of offers I received
        return len(self._sent) <= len(self._received)

    def __call__(self, state: SAOState) -> SAOResponse:
        """The main implementation of the MiCRO strategy"""
        offer = state.current_offer
        # check whether the offer I received is acceptable
        response = ResponseType.REJECT_OFFER
        # check if the offer is acceptable (if one is received)
        if offer is not None:
            self._received.add(offer)
            response = self.acceptance_policy(offer)

        if response == ResponseType.ACCEPT_OFFER:
            return SAOResponse(response, offer)

        # get my next offer
        outcome = self.next_offer()
        assert self.sorter
        assert self.ufun
        # I will repeat a past offer in any of the three following conditions:
        # 1. I cannot find a new rational outcome to offer
        # 2. My next offer is worse than disagreement
        # 3. I am not ready to concede (i.e. I already sent more unique offers than the unique offers I received)
        if (
            outcome is None
            or self.ufun.is_worse(outcome, None)
            or not self.ready_to_concede()
        ):
            return SAOResponse(response, self.sample_sent())
        # I am willing and can concede. Concede by one outcome
        self.next_indx += 1
        self._sent.add(outcome)
        return SAOResponse(response, outcome)

    def acceptance_policy(self, offer: Outcome) -> ResponseType:
        # The Acceptance Policy of MiCRO
        if not self.ufun:
            return ResponseType.REJECT_OFFER
        # find my next offer
        mine = (
            self.next_offer() if self.ready_to_concede() else self.best_offer_so_far()
        )
        # if my next offer is not rational, just indicate that none can be found
        if self.ufun.is_better(None, mine):
            mine = None
        # choose an acceptance method (either not worse or is better)
        is_acceptable = (
            self.ufun.is_not_worse if self.accept_same else self.ufun.is_better
        )
        # Accept if the offer I received is acceptable given my next offer
        if is_acceptable(offer, mine):
            return ResponseType.ACCEPT_OFFER
        return ResponseType.REJECT_OFFER
