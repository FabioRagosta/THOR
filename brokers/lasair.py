"""
THOR v2

Lasair broker.
"""

from __future__ import annotations

from typing import List, Optional
from .registry import register
from thor.config import CONFIG
from thor.model import Candidate

from .base import BaseBroker
from .parser.lasair import LasairParser
from .rest.lasair import LasairREST


@register
class LasairBroker(BaseBroker):
    """
    THOR interface to the Lasair broker.
    """

    def __init__(
        self,
        survey: str = "ztf",
        token: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
        cache: bool = True,
        parser: LasairParser | None = None,
    ):

        if token is None:
            token = (
                CONFIG.lasair_token_lsst
                if survey.lower() == "lsst"
                else CONFIG.lasair_token_ztf
            )

        self.client = LasairREST(
            survey=survey,
            token=token,
            timeout=timeout,
            retries=max_retries,
        )

        self.parser = parser or LasairParser()

        self._timeout = timeout
        self._retries = max_retries

        self.survey = survey
        
    @property
    def survey(self):
        return self._survey
    
    @survey.setter
    def survey(self, value):
    
        value = value.lower()
    
        self._survey = value
    
        token = (
            CONFIG.lasair_token_lsst
            if value == "lsst"
            else CONFIG.lasair_token_ztf
        )
    
        self.client = LasairREST(
            survey=value,
            token=token,
            timeout=30,
            retries=3,
        )
    
        if hasattr(self, "parser"):
            self.parser.survey = value
    # ---------------------------------------------------------

    name = "Lasair"

    # ---------------------------------------------------------

    supports_ztf=True

    # ---------------------------------------------------------

    supports_lsst = True

    # ---------------------------------------------------------

    def search(
            self,
            classifier=None,
            n=100,
            **kwargs,
        ) -> List[Candidate]:
        # classifier non supportato
        del classifier
        data = self.client.search(**kwargs)

        candidates = self.parser.parse(data)

        for candidate in candidates:
            candidate.metadata["survey"] = self.survey
    
        return candidates

    # ---------------------------------------------------------

    def cone_search(
        self,
        ra: float,
        dec: float,
        radius_arcsec: float,
        **kwargs,
    ) -> List[Candidate]:

        data = self.client.cone_search(
            ra=ra,
            dec=dec,
            radius_arcsec=radius_arcsec,
            **kwargs,
        )

        return self.parser.parse(data)

    # ---------------------------------------------------------

    def get_object(
        self,
        object_id: str,
    ) -> Optional[Candidate]:

        data = self.client.get_object(object_id)

        candidates = self.parser.parse(data)

        if not candidates:

            return None

        return candidates[0]

    # ---------------------------------------------------------

    def lightcurve(
        self,
        object_id: str,
    ):

        return self.client.lightcurve(object_id)

    # ---------------------------------------------------------

    def classifications(
        self,
        object_id: str,
    ):

        candidate = self.get_object(object_id)

        if candidate is None:

            return {}

        return candidate.broker_classifications

    # ---------------------------------------------------------

    def extract_features(
        self,
        candidate: Candidate,
    ) -> Candidate:

        #
        # Features computed later by FeatureService
        #

        return candidate