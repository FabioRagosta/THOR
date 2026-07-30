"""
THOR v2
========

Main user interface.

Hunter is the entry point of the THOR framework.

Example
-------
>>> from thor.hunter import Hunter
>>> hunter = Hunter()
>>> hunter.load("fink")
>>> result = hunter.search(classifier="SuperNNova")

Author
------
Fabio Ragosta et al.
"""

from __future__ import annotations

from typing import Optional

from thor.model import Candidate

from thor.brokers.manager import BrokerManager

from thor.services.fusion import FusionService
from thor.services.features import FeatureExtractor
from thor.services.crossmatch import CrossMatchService
from thor.services.calibration import CalibrationService
from thor.services.ranking import RankingService


class Hunter:
    """
    Main THOR interface.
    """
    @property
    def survey(self):
        return self._survey

    @survey.setter
    def survey(self, value):
        self._survey = value

        if self._broker is not None:
            self._broker.survey = value
    def __init__(self):

        self.manager = BrokerManager()

        self.features = FeatureExtractor()

        self.crossmatch = CrossMatchService()

        self.fusion = FusionService()
        
        self.calibration = CalibrationService()

        self.ranking = RankingService()

        self._broker = None
        
        self._survey = "ztf"

    # ---------------------------------------------------------

    @property
    def broker(self):

        """
        Currently loaded broker.
        """

        return self._broker

    # ---------------------------------------------------------

    def load(
        self,
        broker: str,
    ):

        """
        Load a broker.

        Parameters
        ----------
        broker : str
            Broker name.
        """

        self._broker = self.manager.load(broker, survey=self.survey)
        self._broker.survey = self.survey

        return self._broker

    # ---------------------------------------------------------

    def available_brokers(self):

        """
        List registered brokers.
        """

        return self.manager.available()

    # ---------------------------------------------------------

    def process(
        self,
        candidate: Candidate,
    ) -> Candidate:

        """
        Run all THOR services.
        """

        candidate = self.features(candidate)

        candidate = self.crossmatch(candidate)

        candidate = self.calibration(candidate)

        candidate = self.ranking(candidate)

        return candidate

    # ---------------------------------------------------------

    def search(self,
        **kwargs,) -> list[Candidate]:

        """
        Generic broker search.
        """
        
        if self._broker is None:

            raise RuntimeError(
                "No broker loaded."
            )

        candidates = self._broker.search(**kwargs)

        candidates = self.fusion.run(candidates)
        
        return [
            self.process(candidate)
            for candidate in candidates
        ]

    # ---------------------------------------------------------

    def cone_search(
        self,
        ra: float,
        dec: float,
        radius_arcsec: float,
        **kwargs,
    ) -> list[Candidate]:

        """
        Cone search.
        """

        if self._broker is None:

            raise RuntimeError(
                "No broker loaded."
            )

        candidates = self._broker.cone_search(
            ra=ra,
            dec=dec,
            radius_arcsec=radius_arcsec,
            **kwargs,
        )
        
        candidates = self.fusion.run(candidates)
        
        return [
            self.process(candidate)
            for candidate in candidates
        ]

    # ---------------------------------------------------------
    def search_all(
        self,
        brokers: list[str],
        mode: str = "search",
        ra: Optional[float] = None,
        dec: Optional[float] = None,
        radius_arcsec: Optional[float] = None,
        broker_kwargs: Optional[dict[str, dict]] = None,
        **kwargs,
    ) -> list[Candidate]:
 
        """
        Query several brokers and fuse the results into a single,
        weighted list of candidates.
 
        Unlike `search`/`cone_search`, which only use the broker
        loaded via `load()`, this queries every broker in `brokers`
        and merges the resulting candidates through `FusionService`
        *before* running the rest of the pipeline, so that objects
        seen by more than one broker are actually cross-matched and
        classified with the broker weights.
 
        Parameters
        ----------
        brokers : list[str]
            Broker names to query (e.g. ["fink", "lasair", "alerce"]).
        mode : str
            Either "search" or "cone_search".
        ra, dec, radius_arcsec : float
            Required when mode="cone_search".
        broker_kwargs : dict[str, dict], optional
            Per-broker keyword arguments, keyed by broker name.
            Merged on top of the shared `**kwargs`.
        **kwargs
            Keyword arguments shared by every broker call.
        """
 
        if mode not in ("search", "cone_search"):
 
            raise ValueError(
                "mode must be 'search' or 'cone_search'."
            )
 
        if mode == "cone_search" and (
            ra is None or dec is None or radius_arcsec is None
        ):
 
            raise ValueError(
                "ra, dec and radius_arcsec are required "
                "when mode='cone_search'."
            )
 
        broker_kwargs = broker_kwargs or {}
 
        candidates: list[Candidate] = []
 
        for name in brokers:
 
            broker = self.manager.load(name, survey=self.survey)
            broker.survey = self.survey
 
            call_kwargs = {
                **kwargs,
                **broker_kwargs.get(name, {}),
            }
 
            if mode == "search":
 
                result = broker.search(**call_kwargs)
 
            else:
 
                result = broker.cone_search(
                    ra=ra,
                    dec=dec,
                    radius_arcsec=radius_arcsec,
                    **call_kwargs,
                )
 
            candidates.extend(result)
 
        candidates = self.fusion.run(candidates)
 
        return [
            self.process(candidate)
            for candidate in candidates
        ]
        
    def get(
        self,
        object_id: str,
    ) -> Optional[Candidate]:

        """
        Download one object.
        """

        if self._broker is None:

            raise RuntimeError(
                "No broker loaded."
            )

        candidate = self._broker.get_object(
            object_id
        )
        if candidate is None:
            return None
        
        
        classification = self.broker.classifications(object_id)
        
        candidate.broker_classifications[
            self.broker.name
        ] = classification
        
        
        return candidate
        #if candidate is None:

        #    return None

        #return self.process(candidate)

    # ---------------------------------------------------------

    def lightcurve(
        self,
        object_id: str,
    ):

        """
        Download full lightcurve.
        """

        if self._broker is None:

            raise RuntimeError(
                "No broker loaded."
            )

        return self._broker.lightcurve(
            object_id
        )

    # ---------------------------------------------------------

    def classifications(
        self,
        object_id: str,
    ):

        """
        Download broker classifications.
        """

        if self._broker is None:

            raise RuntimeError(
                "No broker loaded."
            )

        return self._broker.classifications(
            object_id
        )
