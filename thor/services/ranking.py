"""
THOR v2

Candidate ranking service.

The ranking combines multiple independent scores into a single
THOR priority score.

Current components
------------------
- Classification confidence
- Lightcurve quality
- Temporal information
- Host information (placeholder)
- Broker agreement: mean pairwise cosine similarity between the
  probability distributions of every broker that classified the
  candidate (neutral 0.5 when fewer than two brokers reported)
- Rarity (placeholder)

Every partial score is normalized in [0,1].
"""

from __future__ import annotations

import math
from itertools import combinations

from thor.model import Candidate

from .base import BaseService


class RankingService(BaseService):

    name = "Ranking"

    #
    # Relative weights
    #
    WEIGHTS = {

        "classification": 0.50,

        "lightcurve": 0.20,

        "temporal": 0.15,

        "host": 0.05,

        "agreement": 0.05,

        "rarity": 0.05,
    }

    # ---------------------------------------------------------

    def run(
        self,
        candidate: Candidate,
    ) -> Candidate:

        candidate.ranking.classification = (
            self.classification_score(candidate)
        )

        candidate.ranking.lightcurve = (
            self.lightcurve_score(candidate)
        )

        candidate.ranking.temporal = (
            self.temporal_score(candidate)
        )

        candidate.ranking.host = (
            self.host_score(candidate)
        )

        candidate.ranking.agreement = (
            self.agreement_score(candidate)
        )

        candidate.ranking.rarity = (
            self.rarity_score(candidate)
        )

        candidate.ranking.total = self.total_score(candidate)

        return candidate

    # ---------------------------------------------------------

    def classification_score(
        self,
        candidate: Candidate,
    ) -> float:

        probability = candidate.classification.best_probability

        if probability is None:

            return 0.0

        return max(
            0.0,
            min(1.0, float(probability)),
        )

    # ---------------------------------------------------------

    def lightcurve_score(
        self,
        candidate: Candidate,
    ) -> float:

        ndet = candidate.ndet

        if ndet == 0:

            return 0.0

        #
        # Saturates at 20 detections.
        #
        return min(
            ndet / 20.0,
            1.0,
        )

    # ---------------------------------------------------------

    def temporal_score(
        self,
        candidate: Candidate,
    ) -> float:

        duration = candidate.features.get(
            "duration",
            0.0,
        )

        #
        # Prefer objects discovered during the
        # first ~30 days.
        #
        score = 1.0 - min(
            duration / 30.0,
            1.0,
        )

        return score

    # ---------------------------------------------------------

    def host_score(
        self,
        candidate: Candidate,
    ) -> float:

        if candidate.host is None:

            return 0.0

        score = 0.5

        if candidate.host.redshift is not None:

            if candidate.host.redshift < 0.1:

                score += 0.3

        if candidate.host.separation_arcsec is not None:

            if candidate.host.separation_arcsec > 2:

                score += 0.2

        return min(score, 1.0)

    # ---------------------------------------------------------

    def agreement_score(
        self,
        candidate: Candidate,
    ) -> float:

        #
        # Compares the classifications coming from every broker
        # that reported one, using the mean pairwise cosine
        # similarity between their probability distributions.
        #
        # Cosine similarity is used (rather than a strict
        # best-class match) because it degrades gracefully: two
        # brokers that both split their probability mass between
        # the same couple of classes still score as "agreeing"
        # even if their top class differs by a hair.
        #
        # With 0 or 1 broker there is nothing to compare, so we
        # fall back to the previous neutral placeholder value.
        #

        classifications = [
            c for c in candidate.broker_classifications.values()
            if c.probabilities
        ]

        if len(classifications) < 2:

            return 0.5

        similarities = [
            self._cosine_similarity(
                c1.probabilities,
                c2.probabilities,
            )
            for c1, c2 in combinations(classifications, 2)
        ]

        return max(
            0.0,
            min(1.0, sum(similarities) / len(similarities)),
        )

    # ---------------------------------------------------------

    @staticmethod
    def _cosine_similarity(
        a: dict[str, float],
        b: dict[str, float],
    ) -> float:

        classes = set(a) | set(b)

        dot = sum(
            a.get(cls, 0.0) * b.get(cls, 0.0)
            for cls in classes
        )

        norm_a = math.sqrt(sum(v * v for v in a.values()))

        norm_b = math.sqrt(sum(v * v for v in b.values()))

        if norm_a == 0.0 or norm_b == 0.0:

            return 0.0

        return dot / (norm_a * norm_b)

    # ---------------------------------------------------------

    def rarity_score(
        self,
        candidate: Candidate,
    ) -> float:

        best = candidate.classification.best_class

        if best is None:

            return 0.0

        best = best.lower()

        if "tde" in best:

            return 1.0

        if "unknown" in best:

            return 0.9

        if "sn ia" in best:

            return 0.4

        if "sn" in best:

            return 0.6

        return 0.5

    # ---------------------------------------------------------

    def total_score(
        self,
        candidate: Candidate,
    ) -> float:

        r = candidate.ranking

        score = (

            self.WEIGHTS["classification"] * r.classification +

            self.WEIGHTS["lightcurve"] * r.lightcurve +

            self.WEIGHTS["temporal"] * r.temporal +

            self.WEIGHTS["host"] * r.host +

            self.WEIGHTS["agreement"] * r.agreement +

            self.WEIGHTS["rarity"] * r.rarity

        )

        return round(score, 4)