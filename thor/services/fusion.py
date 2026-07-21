"""
THOR v2

Fusion service.

Merge candidates coming from different brokers that refer
to the same astronomical object and combine their
classifications.
"""

from __future__ import annotations

from collections import defaultdict

from thor.model import (
    Candidate,
    Classification,
)


class FusionService:
    """
    Merge broker candidates into a single THOR candidate.
    """

    def __init__(
        self,
        radius_arcsec: float = 1.0,
        weights: dict[str, float] | None = None,
    ):

        self.radius_arcsec = radius_arcsec

        self.weights = weights or {
            "Fink":0.38,
            "ALeRCE": 0.67, 
            "Lasair": -0.05,
        }

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

    def _group_candidates(
        self,
        candidates: list[Candidate],
    ) -> list[list[Candidate]]:

        #
        # First implementation:
        #
        # group by object_id.
        #
        # Later we will replace this with
        # coordinate matching.
        #

        groups = defaultdict(list)

        for candidate in candidates:

            if candidate.broker_info:

                key = candidate.broker_info[0].object_id

            else:

                key = id(candidate)

            groups[key].append(candidate)

        return list(groups.values())

    # ---------------------------------------------------------

    def _merge_group(
        self,
        group: list[Candidate],
    ) -> Candidate:

        #
        # Start from the first candidate.
        #

        merged = group[0]

        merged.broker_classifications.clear()

        #
        # Store every broker classification.
        #

        for candidate in group:

            if not candidate.broker_info:
                continue
        
            broker = candidate.broker_info[0].broker

            merged.broker_classifications[
                broker
            ] = candidate.classification

        #
        # Compute fused classification.
        #

        merged.classification = self._combine(
            merged.broker_classifications
        )

        return merged

    # ---------------------------------------------------------

    def _combine(
        self,
        classifications: dict[str, Classification],
    ) -> Classification:

        scores = defaultdict(float)

        total_weight = defaultdict(float)

        for broker, classification in classifications.items():

            weight = self.weights.get(
                broker,
                1.0,
            )

            for cls, prob in classification.probabilities.items():

                scores[cls] += weight * prob

                total_weight[cls] += weight

        fused = Classification()

        for cls in scores:

            fused.probabilities[cls] = (
                scores[cls]
                /
                total_weight[cls]
            )

        fused.classifier = "THOR Fusion"

        return fused
