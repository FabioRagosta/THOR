"""
THOR v2
========

Feature extraction service.

"""

from __future__ import annotations

from thor.model import Candidate
from .base import BaseService
import statistics

class FeatureExtractor(BaseService):

    name = "FeatureExtractor"

    def run(
        self,
        candidate: Candidate,
    ) -> Candidate:

        if candidate.ndet == 0:

            return candidate

        self.basic_statistics(candidate)

        self.time_features(candidate)

        self.photometric_features(candidate)

        return candidate

    # -----------------------------------------------------

    def basic_statistics(
        self,
        candidate: Candidate,
    ):

        mags = [
                    d.mag
                    for d in candidate.detections
                    if d.mag is not None
                ]
        
        if not mags:
            return

        candidate.features["n_detections"] = len(mags)

        candidate.features["min_mag"] = min(mags)

        candidate.features["max_mag"] = max(mags)

        candidate.features["amplitude"] = max(mags) - min(mags)

        candidate.features["mean_mag"] = (
                                            sum(mags) / len(mags)
                                        )
        
        candidate.features["std_mag"] = (
                                            statistics.pstdev(mags)
                                            if len(mags) > 1
                                            else 0.0
                                        )

    # -----------------------------------------------------

    def time_features(
        self,
        candidate: Candidate,
    ):

        mjd = [
                d.mjd
                for d in candidate.detections
                if d.mjd is not None
            ]
        
        if len(mjd) < 2:
            return

        candidate.features["duration"] = max(mjd) - min(mjd)
        candidate.features["cadence"] = (
                                            candidate.features["duration"]
                                            / max(candidate.ndet - 1, 1)
                                        )
    # -----------------------------------------------------

    def photometric_features(
        self,
        candidate: Candidate,
    ):

        if candidate.ndet < 2:

            return

        first = candidate.first_detection.mag

        last = candidate.last_detection.mag

        candidate.features["delta_mag"] = last - first
