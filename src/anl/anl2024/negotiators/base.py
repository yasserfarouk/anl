from abc import abstractmethod
from negmas.gb.mechanisms.base import ResponseType
from negmas.sao.negotiators import SAONegotiator
from negmas.sao.common import SAOState, SAOResponse
from negmas.outcomes import Outcome, ExtendedOutcome

__all__ = ["ANLNegotiator"]


class ANLNegotiator(SAONegotiator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__last_offer: Outcome | None | int = 0
        self.__last_response: ResponseType | None = None

    @abstractmethod
    def __call__(self, state: SAOState) -> SAOResponse: ...

    def propose(self, state) -> Outcome | ExtendedOutcome | None:
        if isinstance(self.__last_offer, int) and self.__last_offer == 0:
            # assert self.__last_response is None
            resp = self(state)
            self.__last_response = resp.response
            self.__last_offer = resp.outcome
        assert not isinstance(self.__last_offer, int)
        off = self.__last_offer
        self.__last_offer = 0
        return off

    def respond(self, state, source: str | None = None) -> ResponseType:
        _ = source
        if self.__last_response is None:
            # assert isinstance(self.__last_offer, int) and self.__last_offer == 0
            resp = self(state)
            self.__last_response = resp.response
            self.__last_offer = resp.outcome
        r = self.__last_response
        self.__last_response = None
        return r
