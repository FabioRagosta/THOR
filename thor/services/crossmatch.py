"""
THOR v2
========

Cross-match service.

This service executes one or more cross-match functions on a
Candidate object.

Each matcher is a callable receiving a Candidate and returning
the updated Candidate.

Author:
Fabio Ragosta et al.
"""

from __future__ import annotations

from typing import Callable, List

from thor.model import Candidate

from .base import BaseService


class CrossMatchService(BaseService):
    """
    Execute one or more cross-match routines.
    """

    name = "CrossMatch"

    def __init__(self):

        self._matchers: List[Callable[[Candidate], Candidate]] = []

    # ---------------------------------------------------------

    def register(self, matcher: Callable[[Candidate], Candidate]) -> None:
        """
        Register a new cross-match function.
        """

        if matcher not in self._matchers:
            self._matchers.append(matcher)

    # ---------------------------------------------------------

    def unregister(
            self,
            matcher: Callable[[Candidate], Candidate],
        ) -> None:

        if matcher in self._matchers:
            self._matchers.remove(matcher)

    # ---------------------------------------------------------

    def clear(self) -> None:

        self._matchers.clear()

    # ---------------------------------------------------------

    @property
    def matchers(
        self,
    ) -> tuple[Callable[[Candidate], Candidate], ...]:

        return tuple(self._matchers)

    # ---------------------------------------------------------

    def run(
        self,
        candidate: Candidate,
    ) -> Candidate:

        for matcher in self._matchers:

            try:

                updated = matcher(candidate)

                if updated is not None:
                    candidate = updated

            except Exception as exc:

                #
                # Il framework continua anche se
                # un catalogo fallisce.
                #
                candidate.metadata.setdefault(
                                                "crossmatch_errors",
                                                []
                                            ).append(
                                                {
                                                    "matcher": getattr(
                                                        matcher,
                                                        "__name__",
                                                        matcher.__class__.__name__,
                                                    ),
                                                    "error": str(exc),
                                                }
                                            )

        return candidate