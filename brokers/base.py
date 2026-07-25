"""
THOR v2
========

Abstract broker interface.

Every broker must inherit from BaseBroker.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from thor.model import (
    Candidate,
    Classification,
    Detection,
)
from .client import BrokerClient

class BaseBroker(ABC):
    """
    Base class for every astronomical broker.

    Every broker must implement the methods below.
    """

    def __init__(
        self,
        survey: str = "ztf",
        timeout: int = 30,
        max_retries: int = 3,
        cache: bool = True,
    ):

        self._survey = survey.lower()

        self.timeout = timeout

        self.max_retries = max_retries

        self.cache = cache
        self.client = BrokerClient(
            timeout=timeout,
            retries=max_retries,
            cache=cache,)
    # ----------------------------------------------------
    # Search interface
    # ----------------------------------------------------

    @abstractmethod
    def search(
                self,
                **kwargs,
            ) -> list[Candidate]:
        """
        Generic search.

        Returns
        -------
        SearchResult
        """

        raise NotImplementedError

    # ----------------------------------------------------

    @abstractmethod
    def cone_search(
        self,
        ra: float,
        dec: float,
        radius_arcsec: float,
        **kwargs,
    ) -> list[Candidate]:
        """
        Cone search around coordinates.
        """

        raise NotImplementedError

    # ----------------------------------------------------

    @abstractmethod
    def get_object(
        self,
        object_id: str,
    ) -> Optional[Candidate]:
        """
        Download one object.
        """

        raise NotImplementedError

    # ----------------------------------------------------

    @abstractmethod
    def lightcurve(
        self,
        object_id: str,
    ) -> list[Detection]:
        """
        Return full lightcurve.
        """

        raise NotImplementedError

    # ----------------------------------------------------

    @abstractmethod
    def classifications(
        self,
        object_id: str,
    ) -> Classification:
        """
        Return all broker classifications.

        NOT only SN.

        Example

        {
            SN : 0.92
            AGN : 0.03
            TDE : 0.04
            CV : 0.01
        }

        """

        raise NotImplementedError

    # ----------------------------------------------------
    @property
    def supports_host(self)-> bool:
    
        return False

    @property
    def supports_lightcurve(self)-> bool:
    
        return True
    
    @property
    @abstractmethod
    def name(self):

        raise NotImplementedError

    # ----------------------------------------------------

    @property
    @abstractmethod
    def supports_lsst(self):

        raise NotImplementedError

    # ----------------------------------------------------

    @property
    @abstractmethod
    def supports_ztf(self):

        raise NotImplementedError
