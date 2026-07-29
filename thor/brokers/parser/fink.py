"""
THOR v2

Fink parser.
"""

from __future__ import annotations

from collections.abc import Iterable

from thor.utils import (
    get_object_id, 
    get_ra, 
    get_dec,
    get_mjd, 
    get_filter, 
    get_snr
)
from thor.model import (
    BrokerInfo,
    Candidate,
    Classification,
    Coordinates
)
from thor.utils import (
    safe_float,
    safe_int,
    safe_str,
)
from .base import BaseParser

FILTER_MAP = {
                1: "g",
                2: "r",
                3: "i",
            }
FINK_CLASSES = {
    "sn",
    "snia",
    "rf_snia",
    "kilonova",
    "slsn",
    "agn",
    "tde"
}

FINK_METADATA = {
    "rate",
    "sigma(rate)",
    "lapse",
    "anomaly"
}
class FinkParser(BaseParser):
    """
    Convert Fink JSON objects into THOR Candidates.
    """
    # ---------------------------------------------------------

    def parse(self, raw):
        """
        Entry point required by BaseParser.
        """

        return self.parse_candidates(raw)
    # ---------------------------------------------------------

    def parse_candidate(
        self,
        raw: dict,
    ) -> Candidate:
    
        candidate = Candidate()
    
        classification = Classification(
            classifier="Fink"
        )
    
        # ------------------------------------------------------------------
        # Mantieni il payload completo come metadata della classificazione
        # ------------------------------------------------------------------
    
        classification.metadata = raw.copy()
    
        # Classificazione testuale restituita da Fink
        candidate.metadata["broker_classification"] = raw.get(
            "v:classification"
        )
    
        # ------------------------------------------------------------------
        # Informazioni broker
        # ------------------------------------------------------------------
        broker = BrokerInfo(
            broker="Fink",
            object_id=get_object_id(raw),
            raw=raw,
        )
    
        candidate.add_broker(broker)
    
        # ------------------------------------------------------------------
        # Coordinate
        # ------------------------------------------------------------------
        
        candidate.coordinates.ra = get_ra(raw)
        candidate.coordinates.dec = get_dec(raw)
    
        # ------------------------------------------------------------------
        # Detection
        # ------------------------------------------------------------------
    
        candidate.add_detection(
            mjd=safe_float(get_mjd(raw)),
            mag=None,
            magerr=None,
            filt=get_filter(raw),
            snr=None,
        )
    
        # ------------------------------------------------------------------
        # Vere probabilità scientifiche prodotte da Fink
        # ------------------------------------------------------------------
    
        mapping = {
    
            "d:snn_sn_vs_all": "SN",
    
            "d:snn_snia_vs_nonia": "SNIa",
    
            "d:rf_kn_vs_nonkn": "Kilonova",
    
            "d:rf_snia_vs_nonia": "RF_SNIa",
    
            "d:slsn_score": "SLSN",
    
        }
    
        for key, cls in mapping.items():
    
            value = safe_float(raw.get(key))
    
            if value is None:
                continue
    
            # Fink usa -1 quando il classificatore non è disponibile
            if value < 0:
                continue
    
            classification.probabilities[cls] = value
    
        # ------------------------------------------------------------------
        # Confidence
        # ------------------------------------------------------------------
    
        classification.confidence = safe_float(
            raw.get("v:lapse")
        )
    
        # ------------------------------------------------------------------
        # Metadata del candidato
        # ------------------------------------------------------------------
    
        reserved = {
    
            "i:objectId",
            "i:ra",
            "i:dec",
            "i:jd",
            "i:magpsf",
            "i:sigmapsf",
            "i:fid",
    
            "v:classification",
    
        }
    
        for key, value in raw.items():
    
            if key not in reserved:
    
                candidate.metadata[key] = value
    
        candidate.metadata["survey"] = raw.get(
            "i:publisher",
            "Fink"
        )
    
        candidate.classification = classification
    
        candidate.broker_classifications["Fink"] = classification
    
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
            self.parse_candidate(raw)
            for raw in data
        ]

