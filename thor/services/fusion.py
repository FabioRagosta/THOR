"""
THOR v2

Fusion service.

Merge candidates coming from different brokers that refer
to the same astronomical object and combine their
classifications in a common THOR taxonomy.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from math import isfinite

from thor.model import Candidate, Classification


class FusionService:
    """
    Merge broker candidates into a single THOR candidate.

    Broker classifications are first mapped to a common THOR
    taxonomy and then combined using broker-dependent weights.

    The fusion operates on the following scientific classes:

        SN
        SLSN
        TDE
        AGN
        Kilonova
        Unknown

    Non-scientific/contextual labels such as ``UNCLEAR`` and
    ALeRCE ``bogus`` are ignored by the scientific fusion.
    """

    # ---------------------------------------------------------
    # Common THOR taxonomy
    # ---------------------------------------------------------

    THOR_CLASSES = (
        "SN",
        "SLSN",
        "TDE",
        "AGN",
        "Kilonova",
        "Unknown",
    )

    # ---------------------------------------------------------
    # Broker weights
    # ---------------------------------------------------------

    DEFAULT_WEIGHTS = {
        "Fink": 0.38,
        "ALeRCE": 0.67,
        "Lasair": 0.0,
    }

    # ---------------------------------------------------------
    # Labels that must not participate in scientific fusion
    # ---------------------------------------------------------

    IGNORED_CLASSES = {
        "unclear",
        "unknown",
        "bogus",
        "transient",
        "periodic",
        "periodic-other",
        "vs",
        "lpv",
        "ea",
        "eb/ew",
        "qso",
        "stochastic",
        "blazar",
        "asteroid",
        "rscvn",
        "yso",
        "cep",
        "cv/nova",
        "rrlab",
        "rrlc",
        "dsct",
        "e",
        "satellite",
        "microlensing",
    }

    # ---------------------------------------------------------

    def __init__(
        self,
        radius_arcsec: float = 1.0,
        weights: dict[str, float] | None = None,
        detection_tolerance_days: float = 1.0e-5,
    ):

        self.radius_arcsec = radius_arcsec

        # Detections reported by different brokers for the same survey
        # exposure can differ by tiny floating-point offsets in MJD.
        # Treat measurements in the same filter within this tolerance
        # as the same detection. 1e-5 d is about 0.86 s.
        self.detection_tolerance_days = max(
            float(detection_tolerance_days),
            0.0,
        )

        self.weights = (
            weights.copy()
            if weights is not None
            else self.DEFAULT_WEIGHTS.copy()
        )

    # ---------------------------------------------------------

    def run(
        self,
        candidates: list[Candidate],
    ) -> list[Candidate]:

        groups = self._group_candidates(candidates)

        return [
            self._merge_group(group)
            for group in groups
        ]

    # ---------------------------------------------------------
    # Candidate grouping
    # ---------------------------------------------------------

    def _group_candidates(
        self,
        candidates: list[Candidate],
    ) -> list[list[Candidate]]:

        """
        Group candidates referring to the same object.

        The current implementation groups by broker object ID.

        Coordinate-based matching can be introduced later using
        ``radius_arcsec``.
        """

        groups = defaultdict(list)

        for candidate in candidates:

            if candidate.broker_info:

                key = candidate.broker_info[0].object_id

            else:

                key = id(candidate)

            groups[key].append(candidate)

        return list(groups.values())

    # ---------------------------------------------------------
    # Merge one group
    # ---------------------------------------------------------

    def _merge_group(
        self,
        group: list[Candidate],
    ) -> Candidate:

        """
        Merge all broker information belonging to one object.

        The merge is intentionally order-independent. In particular,
        photometric detections are collected from every broker candidate
        and deduplicated before feature extraction and ranking.
        """

        if not group:
            raise ValueError("Cannot merge an empty candidate group.")

        # Work on a copy rather than mutating one of the broker candidates.
        # A deterministic base candidate prevents the result from depending
        # on the order in which broker responses were supplied.
        ordered_group = sorted(
            group,
            key=self._candidate_sort_key,
        )
        merged = deepcopy(ordered_group[0])

        # ---------------------------------------------------------
        # Merge broker information
        # ---------------------------------------------------------

        broker_info = []
        seen_broker_info = set()

        for candidate in ordered_group:
            for info in candidate.broker_info:
                key = (info.broker, info.object_id)
                if key in seen_broker_info:
                    continue
                seen_broker_info.add(key)
                broker_info.append(deepcopy(info))

        broker_info.sort(
            key=lambda info: (
                str(info.broker),
                str(info.object_id),
            )
        )
        merged.broker_info = broker_info

        # ---------------------------------------------------------
        # Merge broker classifications
        # ---------------------------------------------------------

        by_broker = defaultdict(list)
        for candidate in ordered_group:
            for broker, classification in (
                candidate.broker_classifications.items()
            ):
                by_broker[broker].append(classification)

        merged.broker_classifications = {
            broker: deepcopy(
                max(
                    classifications,
                    key=self._classification_quality_key,
                )
            )
            for broker, classifications in sorted(by_broker.items())
        }

        # ---------------------------------------------------------
        # Merge detections from all brokers
        # ---------------------------------------------------------

        merged.detections = self._merge_detections(ordered_group)

        # ---------------------------------------------------------
        # Merge simple candidate-level metadata
        # ---------------------------------------------------------

        discovered = [
            c.discovered for c in ordered_group
            if c.discovered is not None
        ]
        last_update = [
            c.last_update for c in ordered_group
            if c.last_update is not None
        ]

        merged.discovered = min(discovered) if discovered else None
        merged.last_update = max(last_update) if last_update else None

        # Merge metadata without making the result order-dependent.
        # Existing keys are retained from the deterministic base candidate.
        metadata = {}
        for candidate in ordered_group:
            for key in sorted(candidate.metadata):
                metadata.setdefault(key, deepcopy(candidate.metadata[key]))
        merged.metadata = metadata

        # Host cross-matching normally runs after fusion. Preserve an
        # already available host only when one is present in the inputs.
        hosts = [c.host for c in ordered_group if c.host is not None]
        merged.host = deepcopy(hosts[0]) if hosts else None

        # Features and ranking are derived downstream from the merged data.
        # Reset them so stale broker-local values cannot leak into THOR.
        merged.features.values.clear()
        merged.ranking.classification = 0.0
        merged.ranking.agreement = 0.0
        merged.ranking.lightcurve = 0.0
        merged.ranking.host = 0.0
        merged.ranking.temporal = 0.0
        merged.ranking.rarity = 0.0
        merged.ranking.total = 0.0

        # ---------------------------------------------------------
        # Fuse classifications
        # ---------------------------------------------------------

        merged.classification = self._combine(
            merged.broker_classifications
        )

        return merged

    # ---------------------------------------------------------
    # Deterministic merge helpers
    # ---------------------------------------------------------

    @staticmethod
    def _candidate_sort_key(candidate: Candidate) -> tuple:
        """Stable ordering used only to make merging reproducible."""

        ids = sorted(
            (str(info.broker), str(info.object_id))
            for info in candidate.broker_info
        )

        if ids:
            return tuple(ids)

        ra = candidate.coordinates.ra
        dec = candidate.coordinates.dec

        return (
            ("", f"{ra!r}:{dec!r}"),
        )

    @staticmethod
    def _classification_quality_key(
        classification: Classification,
    ) -> tuple:
        """Choose deterministically between duplicate broker outputs."""

        probabilities = classification.probabilities or {}
        confidence = classification.confidence

        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = -1.0

        probability_signature = tuple(
            sorted(
                (str(key), float(value))
                for key, value in probabilities.items()
                if value is not None
            )
        )

        return (
            len(probabilities),
            confidence_value,
            probability_signature,
            str(classification.classifier or ""),
        )

    def _merge_detections(
        self,
        group: list[Candidate],
    ) -> list:
        """
        Collect and deduplicate detections from every broker candidate.

        Detections are considered duplicates when they have the same filter
        and their MJDs differ by no more than ``detection_tolerance_days``.
        If duplicate records contain different amounts of information, the
        most complete measurement is retained deterministically.
        """

        detections = [
            deepcopy(detection)
            for candidate in group
            for detection in candidate.detections
            if detection.mjd is not None
        ]

        detections.sort(key=self._detection_sort_key)

        merged = []

        for detection in detections:
            duplicate_index = None

            # Because detections are time-sorted, scanning backwards can stop
            # as soon as the time difference exceeds the tolerance.
            for index in range(len(merged) - 1, -1, -1):
                previous = merged[index]
                delta = float(detection.mjd) - float(previous.mjd)

                if delta > self.detection_tolerance_days:
                    break

                same_filter = self._normalise_filter(
                    detection.filt
                ) == self._normalise_filter(previous.filt)

                if same_filter and abs(delta) <= self.detection_tolerance_days:
                    duplicate_index = index
                    break

            if duplicate_index is None:
                merged.append(detection)
                continue

            previous = merged[duplicate_index]
            if self._detection_quality_key(detection) > (
                self._detection_quality_key(previous)
            ):
                merged[duplicate_index] = detection

        merged.sort(key=self._detection_sort_key)
        return merged

    @staticmethod
    def _normalise_filter(value) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    @classmethod
    def _detection_sort_key(cls, detection) -> tuple:
        try:
            mjd = float(detection.mjd)
        except (TypeError, ValueError):
            mjd = float("inf")

        return (
            mjd,
            cls._normalise_filter(detection.filt),
            cls._safe_float(detection.mag),
            cls._safe_float(detection.magerr),
            cls._safe_float(detection.snr),
        )

    @classmethod
    def _detection_quality_key(cls, detection) -> tuple:
        """Prefer complete measurements and, secondarily, lower errors."""

        mag = cls._finite_float(detection.mag)
        magerr = cls._finite_float(detection.magerr)
        snr = cls._finite_float(detection.snr)

        completeness = sum(
            value is not None
            for value in (mag, magerr, snr)
        )

        # Smaller magnitude uncertainty is preferable. ``-inf`` ensures that
        # a missing error never beats a finite one at equal completeness.
        error_quality = -magerr if magerr is not None else float("-inf")

        return (
            completeness,
            error_quality,
            snr if snr is not None else float("-inf"),
            mag if mag is not None else float("-inf"),
        )

    @staticmethod
    def _finite_float(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        return number if isfinite(number) else None

    @staticmethod
    def _safe_float(value) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return float("inf")

        return number if isfinite(number) else float("inf")

    # ---------------------------------------------------------
    # Broker taxonomy mapping
    # ---------------------------------------------------------

    def _map_class(
        self,
        broker: str,
        class_name: str,
    ) -> str | None:

        """
        Map a broker-specific class to the THOR taxonomy.

        Returns ``None`` when the broker label should not
        contribute to the scientific fusion.
        """

        if class_name is None:

            return None

        cls = str(class_name).strip()

        if not cls:

            return None

        key = cls.lower()

        # -----------------------------------------------------
        # Explicitly ignored/contextual classes
        # -----------------------------------------------------

        if key in self.IGNORED_CLASSES:

            return None

        # -----------------------------------------------------
        # Supernovae
        # -----------------------------------------------------

        if key in {
            "slsn",
            "slsn-i",
            "slsn-ii",
            "slsn-i?",
        }:

            return "SLSN"

        if key in {
            "sn",
            "snia",
            "sni",
            "snii",
            "sniib",
            "sniic",
            "sniin",
            "sniib/c",
            "sniib/c?",
            "snic",
            "snic-bl",
            "snibc",
            "sesn",
        }:

            return "SN"

        # -----------------------------------------------------
        # TDE
        # -----------------------------------------------------

        if key in {
            "tde",
            "tidal disruption event",
        }:

            return "TDE"

        # -----------------------------------------------------
        # AGN
        # -----------------------------------------------------

        if key in {
            "agn",
            "qso",
        }:

            return "AGN"

        # -----------------------------------------------------
        # Kilonova
        # -----------------------------------------------------

        if key in {
            "kilonova",
            "kn",
        }:

            return "Kilonova"

        # -----------------------------------------------------
        # Unknown / unmapped scientific class
        # -----------------------------------------------------

        return "Unknown"

    # ---------------------------------------------------------
    # Map broker probabilities
    # ---------------------------------------------------------

    def _normalise_classification(
        self,
        broker: str,
        classification: Classification,
    ) -> dict[str, float]:

        """
        Convert a broker classification into THOR classes.

        Multiple broker-specific classes mapped to the same
        THOR class are combined using the maximum probability.

        This is important for ALeRCE, where for example:

            SNIa
            SNII
            SNIbc
            SNIIn

        are separate outputs but all belong to the THOR ``SN``
        category.
        """

        mapped = {}

        for class_name, probability in (
            classification.probabilities.items()
        ):

            try:

                probability = float(probability)

            except (TypeError, ValueError):

                continue

            if probability < 0.0:

                continue

            probability = min(
                probability,
                1.0,
            )

            thor_class = self._map_class(
                broker,
                class_name,
            )

            if thor_class is None:

                continue

            mapped[thor_class] = max(
                mapped.get(thor_class, 0.0),
                probability,
            )

        return mapped

    # ---------------------------------------------------------
    # Combine broker classifications
    # ---------------------------------------------------------

    def _combine(
        self,
        classifications: dict[str, Classification],
    ) -> Classification:

        """
        Combine broker classifications.

        Only brokers with a positive weight and at least one
        scientifically useful classification contribute.

        The resulting score is a weighted mean over the brokers
        that provide evidence for the corresponding THOR class.

        Classes for which no broker provides evidence are assigned
        zero.

        ``Unknown`` is used only when no scientific classification
        is available.
        """

        # -----------------------------------------------------
        # Weighted accumulation
        # -----------------------------------------------------

        scores = defaultdict(float)

        total_weight = 0.0

        contributing_brokers = []

        for broker, classification in classifications.items():

            weight = self.weights.get(
                broker,
                0.0,
            )

            # Negative weights are not meaningful for probability
            # fusion. Treat them as zero.
            if weight <= 0.0:

                continue

            mapped = self._normalise_classification(
                broker,
                classification,
            )

            if not mapped:

                continue

            contributing_brokers.append(broker)

            total_weight += weight

            for cls, probability in mapped.items():

                scores[cls] += (
                    weight * probability
                )

        # -----------------------------------------------------
        # No useful broker classification
        # -----------------------------------------------------

        if total_weight == 0.0:

            return Classification(
                probabilities={
                    "Unknown": 1.0
                },
                classifier="THOR Fusion",
                confidence=0.0,
                calibrated=False,
                source="THOR",
                metadata={
                    "contributing_brokers": [],
                    "ignored_brokers": list(
                        classifications.keys()
                    ),
                },
            )

        # -----------------------------------------------------
        # Weighted mean
        # -----------------------------------------------------

        probabilities = {}

        for cls in self.THOR_CLASSES:

            probabilities[cls] = (
                scores.get(cls, 0.0)
                / total_weight
            )

        # -----------------------------------------------------
        # Remove classes with no evidence
        # -----------------------------------------------------

        probabilities = {
            cls: prob
            for cls, prob in probabilities.items()
            if prob > 0.0
        }

        # -----------------------------------------------------
        # No positive probability after fusion
        # -----------------------------------------------------

        if not probabilities:

            return Classification(
                probabilities={
                    "Unknown": 1.0
                },
                classifier="THOR Fusion",
                confidence=0.0,
                calibrated=False,
                source="THOR",
                metadata={
                    "contributing_brokers":
                        contributing_brokers,

                    "ignored_brokers": [
                        broker
                        for broker in classifications
                        if broker not in contributing_brokers
                    ],

                    "weights": {
                        broker: self.weights.get(
                            broker,
                            0.0,
                        )
                        for broker in classifications
                    },

                    "reason":
                        "No positive probability after broker fusion.",
                },
            )

        # -----------------------------------------------------
        # Determine confidence
        # -----------------------------------------------------

        best_probability = max(
            probabilities.values()
        )

        # -----------------------------------------------------
        # Store fusion metadata
        # -----------------------------------------------------

        metadata = {
            "contributing_brokers": contributing_brokers,
            "ignored_brokers": [
                broker
                for broker in classifications
                if broker not in contributing_brokers
            ],
            "weights": {
                broker: self.weights.get(
                    broker,
                    0.0,
                )
                for broker in classifications
            },
            "taxonomy": list(
                self.THOR_CLASSES
            ),
        }

        return Classification(
            probabilities=probabilities,
            classifier="THOR Fusion",
            confidence=best_probability,
            calibrated=False,
            source="THOR",
            metadata=metadata,
        )