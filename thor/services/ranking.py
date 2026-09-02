"""
THOR v2

Candidate ranking service.

The ranking combines independent, normalised components into a single
follow-up priority score.  The default configuration is deliberately
conservative and is suitable for the validation presented in the paper:
only consensus-classification confidence, inter-broker agreement, and a
rarity term derived from an explicitly supplied class-frequency distribution
can contribute to the final score.

Additional terms based on photometric sampling, temporal information, and
host context are retained by the architecture but have zero weight by
default.  They can be enabled explicitly when the corresponding information
is reliably available.

Missing information never generates ranking credit.  The total score is a
weighted mean over the *available* enabled components, so an unavailable
component is neither rewarded nor treated as a measured zero.
"""

from __future__ import annotations

import math
from itertools import combinations
from typing import Mapping

from thor.model import Candidate

from .base import BaseService


class RankingService(BaseService):
    """Compute the THOR follow-up priority score for a candidate."""

    name = "Ranking"

    # Conservative default used for the paper-level ranking demonstration.
    # Photometric/temporal/contextual terms remain available but must be
    # explicitly enabled by changing the weights.
    DEFAULT_WEIGHTS = {
        "classification": 0.60,
        "lightcurve": 0.00,
        "temporal": 0.00,
        "host": 0.00,
        "agreement": 0.20,
        "rarity": 0.20,
    }

    # Backwards-compatible class attribute.  Code that previously inspected
    # RankingService.WEIGHTS still sees the active default configuration.
    WEIGHTS = DEFAULT_WEIGHTS.copy()

    def __init__(
        self,
        weights: Mapping[str, float] | None = None,
        class_frequencies: Mapping[str, float] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        weights
            Optional component weights.  Missing keys inherit the default
            values.  Weights must be finite and non-negative.
        class_frequencies
            Optional mapping ``class_name -> frequency`` used to derive the
            rarity score.  Frequencies must lie in ``(0, 1]``.  If no
            distribution is supplied, rarity is considered unavailable and
            contributes neither credit nor penalty to the total score.
        """
        self.weights = self.WEIGHTS.copy()
        if weights is not None:
            unknown = set(weights) - set(self.DEFAULT_WEIGHTS)
            if unknown:
                raise ValueError(
                    "Unknown ranking component(s): "
                    + ", ".join(sorted(unknown))
                )
            self.weights.update(
                {key: float(value) for key, value in weights.items()}
            )

        for key, value in self.weights.items():
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(
                    f"Ranking weight '{key}' must be finite and >= 0."
                )

        self.class_frequencies: dict[str, float] | None = None
        self._rarity_norm: float | None = None
        if class_frequencies is not None:
            self.set_class_frequencies(class_frequencies)

    # ---------------------------------------------------------

    def set_class_frequencies(
        self,
        class_frequencies: Mapping[str, float],
    ) -> None:
        """Set the class distribution used to calculate data-driven rarity."""
        frequencies: dict[str, float] = {}

        for class_name, frequency in class_frequencies.items():
            value = float(frequency)
            if not math.isfinite(value) or not 0.0 < value <= 1.0:
                raise ValueError(
                    "Class frequencies must be finite and in the interval "
                    "(0, 1]."
                )
            frequencies[self._normalise_class_name(class_name)] = value

        if not frequencies:
            self.class_frequencies = None
            self._rarity_norm = None
            return

        self.class_frequencies = frequencies
        self._rarity_norm = max(-math.log(value) for value in frequencies.values())

    # ---------------------------------------------------------

    def run(
        self,
        candidate: Candidate,
    ) -> Candidate:
        candidate.ranking.classification = self.classification_score(candidate)
        candidate.ranking.lightcurve = self.lightcurve_score(candidate)
        candidate.ranking.temporal = self.temporal_score(candidate)
        candidate.ranking.host = self.host_score(candidate)
        candidate.ranking.agreement = self.agreement_score(candidate)
        candidate.ranking.rarity = self.rarity_score(candidate)
        candidate.ranking.total = self.total_score(candidate)

        return candidate

    # ---------------------------------------------------------

    def classification_score(
        self,
        candidate: Candidate,
    ) -> float:
        """Return the confidence of the final THOR consensus classification."""
        probability = candidate.classification.best_probability

        if probability is None:
            return 0.0

        return self._clip01(float(probability))

    # ---------------------------------------------------------

    def lightcurve_score(
        self,
        candidate: Candidate,
    ) -> float:
        """
        Return a simple photometric-sampling score.

        This is intentionally *not* described as a light-curve quality metric:
        it only measures the number of detections currently attached to the
        merged candidate and saturates at 20 detections.  Its default weight is
        zero until broker light curves are merged consistently.
        """
        ndet = candidate.ndet

        if ndet <= 0:
            return 0.0

        return self._clip01(ndet / 20.0)

    # ---------------------------------------------------------

    def temporal_score(
        self,
        candidate: Candidate,
    ) -> float:
        """
        Prefer young objects when a measured duration is available.

        Missing/non-finite duration is explicitly treated as unavailable and
        returns zero; it must never be interpreted as a newly discovered
        transient.  The score decreases linearly to zero over 30 days.
        """
        duration = candidate.features.get("duration")

        if duration is None:
            return 0.0

        try:
            duration = float(duration)
        except (TypeError, ValueError):
            return 0.0

        if not math.isfinite(duration) or duration < 0.0:
            return 0.0

        return self._clip01(1.0 - duration / 30.0)

    # ---------------------------------------------------------

    def host_score(
        self,
        candidate: Candidate,
    ) -> float:
        """
        Return the current experimental host-context score.

        The host term is retained for backwards compatibility and future
        extensions but has zero weight in the default ranking.  Its heuristic
        definition should not be interpreted as a validated science metric.
        """
        if candidate.host is None:
            return 0.0

        score = 0.5

        if candidate.host.redshift is not None:
            if candidate.host.redshift < 0.1:
                score += 0.3

        if candidate.host.separation_arcsec is not None:
            if candidate.host.separation_arcsec > 2:
                score += 0.2

        return self._clip01(score)

    # ---------------------------------------------------------

    def agreement_score(
        self,
        candidate: Candidate,
    ) -> float:
        """
        Return mean pairwise cosine similarity among broker probabilities.

        With fewer than two usable broker classifications agreement is not
        measurable, therefore the returned score is zero rather than a neutral
        pseudo-measurement that would artificially increase the total score.
        """
        classifications = [
            classification
            for classification in candidate.broker_classifications.values()
            if classification.probabilities
        ]

        if len(classifications) < 2:
            return 0.0

        similarities = [
            self._cosine_similarity(
                c1.probabilities,
                c2.probabilities,
            )
            for c1, c2 in combinations(classifications, 2)
        ]

        if not similarities:
            return 0.0

        return self._clip01(sum(similarities) / len(similarities))

    # ---------------------------------------------------------

    @staticmethod
    def _cosine_similarity(
        a: Mapping[str, float],
        b: Mapping[str, float],
    ) -> float:
        classes = set(a) | set(b)

        dot = sum(
            float(a.get(cls, 0.0)) * float(b.get(cls, 0.0))
            for cls in classes
        )

        norm_a = math.sqrt(sum(float(v) * float(v) for v in a.values()))
        norm_b = math.sqrt(sum(float(v) * float(v) for v in b.values()))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return max(0.0, min(1.0, dot / (norm_a * norm_b)))

    # ---------------------------------------------------------

    def rarity_score(
        self,
        candidate: Candidate,
    ) -> float:
        """
        Return a rarity score derived from an explicit class distribution.

        For a class with observed frequency ``f`` the unnormalised rarity is
        ``-log(f)``.  It is divided by the largest rarity in the supplied class
        distribution so that the result lies in [0, 1].

        No hard-coded scientific priority is used.  If the candidate class is
        absent from the supplied distribution, or no distribution has been
        configured, rarity is unavailable and the method returns zero.
        """
        if self.class_frequencies is None or self._rarity_norm is None:
            return 0.0

        best = candidate.classification.best_class
        if best is None:
            return 0.0

        frequency = self.class_frequencies.get(
            self._normalise_class_name(best)
        )
        if frequency is None:
            return 0.0

        if self._rarity_norm <= 0.0:
            # Degenerate distribution (all supplied frequencies are 1).
            return 0.0

        return self._clip01(-math.log(frequency) / self._rarity_norm)

    # ---------------------------------------------------------

    def total_score(
        self,
        candidate: Candidate,
    ) -> float:
        """
        Combine enabled *available* ranking components.

        The score is normalised by the sum of weights of available components.
        Consequently, missing information does not lower the score merely
        because a broker or contextual service did not provide that quantity.
        """
        r = candidate.ranking

        scores = {
            "classification": r.classification,
            "lightcurve": r.lightcurve,
            "temporal": r.temporal,
            "host": r.host,
            "agreement": r.agreement,
            "rarity": r.rarity,
        }

        available = self._component_availability(candidate)

        numerator = 0.0
        denominator = 0.0

        for component, score in scores.items():
            weight = self.weights[component]
            if weight <= 0.0 or not available[component]:
                continue

            numerator += weight * self._clip01(float(score))
            denominator += weight

        if denominator == 0.0:
            return 0.0

        return round(self._clip01(numerator / denominator), 4)

    # ---------------------------------------------------------

    def _component_availability(
        self,
        candidate: Candidate,
    ) -> dict[str, bool]:
        """Report whether each score is based on actual available information."""
        duration = candidate.features.get("duration")
        try:
            duration_available = (
                duration is not None
                and math.isfinite(float(duration))
                and float(duration) >= 0.0
            )
        except (TypeError, ValueError):
            duration_available = False

        usable_broker_classifications = sum(
            1
            for classification in candidate.broker_classifications.values()
            if classification.probabilities
        )

        best_class = candidate.classification.best_class
        rarity_available = (
            self.class_frequencies is not None
            and self._rarity_norm is not None
            and best_class is not None
            and self._normalise_class_name(best_class)
            in self.class_frequencies
        )

        return {
            "classification": candidate.classification.best_probability is not None,
            "lightcurve": candidate.ndet > 0,
            "temporal": duration_available,
            "host": candidate.host is not None,
            "agreement": usable_broker_classifications >= 2,
            "rarity": rarity_available,
        }

    # ---------------------------------------------------------

    @staticmethod
    def _normalise_class_name(class_name: str) -> str:
        return " ".join(str(class_name).strip().lower().split())

    # ---------------------------------------------------------

    @staticmethod
    def _clip01(value: float) -> float:
        if not math.isfinite(value):
            return 0.0
        return max(0.0, min(1.0, value))
