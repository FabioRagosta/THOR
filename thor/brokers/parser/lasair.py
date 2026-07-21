"""
THOR v2

Lasair parser.
"""

from __future__ import annotations

from collections.abc import Iterable

from thor.model import (
    Candidate,
    BrokerInfo,
    Classification,
    Coordinates,
    HostGalaxy
)
from thor.utils import safe_float

from .base import BaseParser


FILTER_MAP = {
    1: "g",
    2: "r",
    3: "i",
}


class LasairParser(BaseParser):

    def parse(self, raw):
        return self.parse_candidates(raw)

    # ---------------------------------------------------------

    def parse_candidate(self, raw) -> Candidate:

        object_data = raw.get("objectData", {})
        detections = raw.get("candidates", [])
    
        candidate = Candidate(
            coordinates=Coordinates(
                ra=safe_float(object_data.get("ramean")),
                dec=safe_float(object_data.get("decmean")),
            ),
            broker_info=[],
        )
    
        sherlock = raw.get("sherlock")
    
        #
        # Default empty classification
        #
        candidate.classification = Classification()
    
        #
        # Sherlock contextual classification
        #
        if sherlock:
    
            label = sherlock.get("classification")
    
            if label:
    
                candidate.classification.probabilities = {
                    label: 1.0
                }
    
                candidate.classification.classifier = "Sherlock"
    
                candidate.classification.confidence = float(
                    sherlock.get("classificationReliability", 1.0)
                )
    
                candidate.classification.source = "Lasair"
    
                candidate.classification.calibrated = False
    
        candidate.add_broker(
            BrokerInfo(
                broker="Lasair",
                object_id=raw.get("objectId", ""),
                raw=raw,
            )
        )
    
        #
        # Last detection
        #
        if detections:
    
            det = detections[-1]
    
            filt = FILTER_MAP.get(det.get("fid"), "?")
    
            jd = safe_float(det.get("jd"))
    
            if jd is not None:
    
                candidate.add_detection(
                    mjd=jd - 2400000.5,
                    mag=safe_float(det.get("magpsf")),
                    magerr=safe_float(det.get("sigmapsf")),
                    filt=filt,
                    snr=None,
                )
    
        #
        # Store full response
        #
        candidate.metadata.update(raw)
    
        return candidate

    # ---------------------------------------------------------

    def parse_candidates(
        self,
        data: Iterable,
    ) -> list[Candidate]:

        if data is None:
            return []

        if isinstance(data, dict):
            data = [data]

        return [
            self.parse_candidate(row)
            for row in data
        ]