"""
THOR v2

ALeRCE broker.
"""

from __future__ import annotations

from typing import Optional

from thor.model import Candidate, Classification

from .base import BaseBroker
from .parser.alerce import AlerceParser
from .registry import register
from .rest.alerce import AlerceREST


@register
class AlerceBroker(BaseBroker):
    """
    THOR interface to the ALeRCE broker.
    """
    CLASSIFIER_MAP = {

                        "SN": {
                            "class_name": [
                                            "SNIa",
                                            "SNII",
                                            "SNIbc",
                                            "SLSN"
                                        ],
                        },
                    
                        "AGN": {
                            "class_name": "AGN",
                        },
                    
                        "LPV": {
                            "class_name": "LPV",
                        },
                    
                    }
    name = "ALeRCE"

    supports_ztf = True

    supports_lsst = True

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache: bool = True,
        parser: AlerceParser | None = None,
        survey: str = "ztf",
    ):

        super().__init__(
                survey=survey,
                timeout=timeout,
                max_retries=max_retries,
                cache=cache,
            )

        self.client = AlerceREST(
            timeout=timeout,
            retries=max_retries,
        )

        self.parser = parser or AlerceParser()
    @property
    def survey(self):
        return self._survey
    
    @survey.setter
    def survey(self, value):
    
        self._survey = value.lower()
    
        if hasattr(self, "client"):
            self.client.survey = self._survey
    
        if hasattr(self, "parser"):
            self.parser.survey = self._survey
    # ---------------------------------------------------------

    def search(
                self,
                survey=None,
                classifier=None,
                limit=100,
                **kwargs,
        ):
        
        if survey is None:
            survey = self._survey
        if classifier in self.CLASSIFIER_MAP:

            kwargs.update(
                self.CLASSIFIER_MAP[classifier]
            )

        kwargs["page_size"] = limit
        
        data = self.client.search(survey=survey, classifier=classifier, **kwargs)
    
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
    ) -> list[Candidate]:

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
        
            candidate = candidates[0]
        
            # Retrieve ALeRCE classification probabilities
            classification = self.classifications(object_id)
        
            candidate.classification = classification
            candidate.broker_classifications["ALeRCE"] = classification
        
            return candidate

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
    ) -> Classification:
        """
        Retrieve ALeRCE classification probabilities.
        """
    
        data = self.client.probabilities(object_id)
    
        if not data:
            return Classification(
                source="ALeRCE"
            )
    
    
        classification = Classification(
            source="ALeRCE"
        )
    
    
        for row in data:
    
            class_name = row.get("class_name")
            probability = row.get("probability")
    
            if (
                class_name is None
                or probability is None
            ):
                continue
    
    
            probability = float(probability)
    
    
            # keep the strongest evidence
            classification.probabilities[class_name] = max(
                classification.probabilities.get(
                    class_name,
                    0.0
                ),
                probability
            )
    
    
        return classification