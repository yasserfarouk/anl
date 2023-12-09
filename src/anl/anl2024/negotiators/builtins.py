from negmas.sao.negotiators import (
    AspirationNegotiator,
    BoulwareTBNegotiator,
    ConcederTBNegotiator,
    LinearTBNegotiator,
)

__all__ = ["Linear", "Conceder", "Boulware"]


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
