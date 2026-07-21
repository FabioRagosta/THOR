"""
THOR v2

Probability calibration service.

This service is responsible for calibrating the classification
probabilities produced by the broker fusion stage.

Current implementation
----------------------

No calibration is applied.

The service simply stores the raw broker probability as the
confidence score.

Future versions will support:

- isotonic regression
- Platt scaling
- beta calibration
- broker-specific calibration
- survey-specific calibration
"""

from __future__ import annotations

from thor.model import Candidate

from .base import BaseService


class CalibrationService(BaseService):

    name = "Calibration"

    def run(
        self,
        candidate: Candidate,
    ) -> Candidate:

        probability = (
            candidate.classification.best_probability
        )

        if probability is None:

            candidate.classification.confidence = None

            return candidate

        #
        # Placeholder.
        #
        # No statistical calibration is currently
        # applied.
        #

        candidate.classification.confidence = float(
            probability
        )

        return candidate