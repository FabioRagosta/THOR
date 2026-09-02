"""
THOR v2
=======

Core data models used across the entire framework.

Author:
Fabio Ragosta et al.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================
# Sky Coordinates
# ============================================================

@dataclass(slots=True)
class Coordinates:
    """
    Sky coordinates.
    """

    ra: float | None = None
    dec: float | None = None

    def tuple(self):
        return (self.ra, self.dec)


# ============================================================
# Photometry
# ============================================================

@dataclass(slots=True)
class Detection:

    mjd: float

    mag: float

    magerr: float

    filt: str

    snr: Optional[float] = None


# ============================================================
# Host Galaxy
# ============================================================

@dataclass(slots=True)
class HostGalaxy:

    name: Optional[str] = None

    redshift: Optional[float] = None

    separation_arcsec: Optional[float] = None

    catalog: Optional[str] = None


# ============================================================
# Broker Information
# ============================================================

@dataclass(slots=True)
class BrokerInfo:

    broker: str

    object_id: str

    url: Optional[str] = None

    retrieved_at: datetime = field(default_factory=datetime.utcnow)

    raw: Optional[dict] = None


# ============================================================
# Classification
# ============================================================

@dataclass(slots=True)
class Classification:

    probabilities: Dict[str, float] = field(default_factory=dict)

    classifier: Optional[str] = None

    confidence: Optional[float] = None

    calibrated: bool = False

    source: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def best_class(self):

        if len(self.probabilities) == 0:
            return None

        return max(self.probabilities,
                   key=self.probabilities.get)

    @property
    def best_probability(self):

        if len(self.probabilities) == 0:
            return None

        return self.probabilities[self.best_class]


# ============================================================
# Feature Vector
# ============================================================

@dataclass(slots=True)
class FeatureVector:
    """
    Container for derived features.

    Behaves like a lightweight dictionary while keeping
    a clean interface for feature extraction modules.
    """

    values: Dict[str, float] = field(default_factory=dict)

    def add(self, name: str, value: float):

        self.values[name] = float(value)

    def update(self, dictionary: Dict[str, float]):

        self.values.update(dictionary)

    def get(self, key: str, default=None):

        return self.values.get(key, default)

    def __getitem__(self, key):

        return self.values[key]

    def __setitem__(self, key, value):

        self.values[key] = value

    def __contains__(self, key):

        return key in self.values

    def keys(self):

        return self.values.keys()

    def items(self):

        return self.values.items()

    def to_dict(self):

        return dict(self.values)

# ============================================================
# Ranking
# ============================================================

@dataclass(slots=True)
class Ranking:
    """
    Ranking information produced by THOR.

    Each score is normalized in the interval [0,1].
    """

    classification: float = 0.0

    agreement: float = 0.0

    lightcurve: float = 0.0

    host: float = 0.0

    temporal: float = 0.0

    rarity: float = 0.0

    total: float = 0.0



# ============================================================
# Candidate
# ============================================================

@dataclass(slots=True)
class Candidate:

    coordinates: Coordinates= field(default_factory=Coordinates)

    broker_info: List[BrokerInfo]= field(default_factory=list)

    detections: List[Detection] = field(default_factory=list)

    features: FeatureVector = field(default_factory=FeatureVector)

    classification: Classification = field(default_factory=Classification)

    broker_classifications: Dict[str, Classification] = field(
    default_factory=dict)
    
    ranking: Ranking = field(default_factory=Ranking)

    host: Optional[HostGalaxy] = None

    metadata: Dict = field(default_factory=dict)

    discovered: Optional[datetime] = None

    last_update: Optional[datetime] = None

    def add_broker(self, broker: BrokerInfo):

        self.broker_info.append(broker)
    def sort_detections(self):
    
        self.detections.sort(
            key=lambda d: d.mjd
        )
    def add_detection(
        self,
        mjd: float,
        mag: float,
        magerr: float,
        filt: str,
        snr: Optional[float]=None,
    ):
    
        self.detections.append(
            Detection(
                mjd=mjd,
                mag=mag,
                magerr=magerr,
                filt=filt,
                snr=snr,
            )
        )
    @property
    def last_detection(self):
    
        if not self.detections:
            return None
    
        return max(
            self.detections,
            key=lambda d: d.mjd,
        )
    @property
    def first_detection(self):
    
        if not self.detections:
            return None
    
        return min(
            self.detections,
            key=lambda d: d.mjd,
        )
    @property
    def ndet(self):
    
        return len(self.detections)
    @property
    def brokers(self):

        return [b.broker for b in self.broker_info]

    @property
    def ids(self):

        return {
            b.broker: b.object_id
            for b in self.broker_info
        }
    @property
    def score(self) -> float:
    
        return self.ranking.total
    
    def __repr__(self):

        object_id = (
            self.broker_info[0].object_id
            if self.broker_info else
            "Unknown"
        )
    
        brokers = ", ".join(
            b.broker for b in self.broker_info
        )
    
        if self.classification is not None:
            cls = self.classification.best_class or "Unknown"
            prob = self.classification.best_probability
    
            if prob is not None:
                cls = f"{cls} ({prob:.2%})"
        else:
            cls = "Unknown"
    
        return (
            f"Candidate("
            f"object='{object_id}', "
            f"class='{cls}', "
            f"RA={self.coordinates.ra:.5f}, "
            f"Dec={self.coordinates.dec:.5f}, "
            f"brokers=[{brokers}]"
            f")"
        )
# ============================================================
# Search Result
# ============================================================

@dataclass(slots=True)
class SearchResult:

    candidates: List[Candidate]

    runtime: float

    survey: str

    query_time: datetime = field(default_factory=datetime.utcnow)

    statistics: Dict = field(default_factory=dict)
