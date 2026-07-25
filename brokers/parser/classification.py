"""
Classification parser.
"""

from __future__ import annotations

from thor.model import Classification

from .base import BaseParser


class ClassificationParser(BaseParser):

    def parse(
        self,
        probabilities,
        *,
        classifier=None,
        calibrated=False,
        source=None,
    ):

        return Classification(

            probabilities=probabilities,

            classifier=classifier,

            calibrated=calibrated,

            source=source,
        )
