"""
THOR v2
========

Base class for all scientific services.

Author:
Fabio Ragosta et al.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from thor.model import Candidate


class BaseService(ABC):
    """
    Base class for every THOR scientific service.
    """

    name = "BaseService"

    @abstractmethod
    def run(
        self,
        candidate: Candidate,
    ) -> Candidate:
        """
        Process a Candidate.
        """
        raise NotImplementedError

    # -----------------------------------------------------

    def __call__(
        self,
        candidate: Candidate,
    ) -> Candidate:
        """
        Allow the service to be called like a function.

        Example
        -------
        candidate = service(candidate)
        """
        return self.run(candidate)