"""
THOR v2

Fink broker.
"""

from __future__ import annotations

from typing import List, Optional

from thor.model import Candidate, Classification
from .base import BaseBroker
from .parser import BaseParser
from .rest.fink import FinkREST
from .parser.fink import FinkParser

from .registry import register


@register
class FinkBroker(BaseBroker):
    """
    THOR interface to the Fink broker.
    """

    def __init__(
        self,
        survey: str = "ztf",
        timeout: int = 30,
        max_retries: int = 3,
        cache: bool = True,
        parser: FinkParser | None = None,
    ):

        super().__init__(
            survey=survey,
            timeout=timeout,
            max_retries=max_retries,
            cache=cache,
        )

        self.client = FinkREST(
            survey=survey,
            timeout=timeout,
            retries=max_retries,
        )

        self.parser = parser or FinkParser()

    name = "Fink"

    supports_ztf = True
    
    supports_lsst = True
    CLASSIFIER_MAP = {
                    "ztf": {
                        "SN": "SN",
                        "TDE": "TDE",
                    },
                    "lsst": {
                        "SN": "most_likely_sn",
                        # "TDE": ??? (quando sarà disponibile)
                    },
                }

    def search(
        self,
        classifier: str | None = None,
        **kwargs,
    ) -> List[Candidate]:
        
        if classifier is not None:
            classifier = (
                self.CLASSIFIER_MAP.get(self.survey, {}).get(classifier, classifier)
            )

    
        data = self.client.latest(classifier=classifier, **kwargs)

        return self.parser.parse(data)

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

            return Classification()

        return candidate.classification

    # ---------------------------------------------------------

    