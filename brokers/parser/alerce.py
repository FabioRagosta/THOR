"""
THOR v2

ALeRCE parser.
"""

from __future__ import annotations

from .base import BaseParser

from thor.model import (
    BrokerInfo,
    Candidate,
    Classification,
    Coordinates,
)


class AlerceParser(BaseParser):
    """
    Convert ALeRCE JSON objects into THOR Candidates.
    """

    # ---------------------------------------------------------

    def parse(self, raw):
        """
        Entry point required by BaseParser.
        """

        return self.parse_candidates(raw)

    # ---------------------------------------------------------

    def parse_candidates(self, data):
        """
        Parse ALeRCE responses.
        """

        if isinstance(data, dict):

            if "items" in data:
                data = data["items"]

            else:
                data = [data]

        return [
            self.parse_candidate(row)
            for row in data
        ]

    # ---------------------------------------------------------

    def parse_candidate(self, raw: dict):
        """
        Convert one ALeRCE record into a THOR Candidate.
        """

        classification = Classification(
            source="ALeRCE"
        )


        # -----------------------------------------------------
        # Classification response
        # -----------------------------------------------------

        if "classifier_name" in raw:

            class_name = raw.get("class_name")
            probability = raw.get("probability")

            if (
                class_name is not None
                and probability is not None
            ):

                probability = float(probability)

                classification.probabilities[class_name] = max(
                    classification.probabilities.get(
                        class_name,
                        0.0
                    ),
                    probability
                )

            classification.classifier = raw.get(
                "classifier_name"
            )

            classification.confidence = probability


        # -----------------------------------------------------
        # Object response
        # -----------------------------------------------------

        else:

            classifier = raw.get("classifier")
            probability = raw.get("probability")

            if (
                classifier is not None
                and probability is not None
            ):

                classification.probabilities[
                    raw.get(
                        "class",
                        classifier
                    )
                ] = float(probability)

            classification.classifier = classifier


        # -----------------------------------------------------
        # Coordinates
        # -----------------------------------------------------

        ra = raw.get("meanra")
        dec = raw.get("meandec")


        if ra is None or dec is None:

            raise ValueError(
                "Missing coordinates in ALeRCE object: "
                f"{raw.keys()}"
            )


        # -----------------------------------------------------
        # Broker information
        # -----------------------------------------------------

        broker = BrokerInfo(
            broker="ALeRCE",
            object_id=raw.get(
                "oid",
                ""
            ),
            raw=raw,
        )


        # -----------------------------------------------------
        # Candidate
        # -----------------------------------------------------

        candidate = Candidate(
            coordinates=Coordinates(
                ra=float(ra),
                dec=float(dec),
            ),
            classification=classification,
        )


        candidate.add_broker(broker)


        # store broker-specific classification
        candidate.broker_classifications["ALeRCE"] = classification


        return candidate