"""
THOR v2

Utilities to convert broker rows into THOR models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
import numbers
import pandas as pd

from thor.model import (
    BrokerInfo,
    Candidate,
    Classification,
    Coordinates,
    Detection,
    FeatureVector,
    HostGalaxy,
)

FILTER_MAP = {
    1: "g",
    2: "r",
    3: "i",
}

# ==========================================================
# Coordinates
# ==========================================================

class CoordinatesMixin:

    @staticmethod
    def from_series(row: pd.Series) -> Coordinates:

        return Coordinates(
            ra=float(row["ra"]),
            dec=float(row["dec"]),
        )


# ==========================================================
# Broker information
# ==========================================================

class BrokerInfoMixin:

    @staticmethod
    def from_series(
        row: pd.Series,
        broker: str,
    ) -> BrokerInfo:

        return BrokerInfo(
            broker=broker,
            object_id=str(row["objectId"]),
            raw=row.to_dict(),
        )


# ==========================================================
# Detection
# ==========================================================

class DetectionMixin:

    @staticmethod
    def from_series(row: pd.Series) -> list[Detection]:

        detections = []

        if "jd" in row:

            mjd = float(row["jd"]) - 2400000.5

        elif "mjd" in row:

            mjd = float(row["mjd"])

        else:

            return detections

        mag = row.get("magpsf", row.get("mag", None))

        if mag is None:

            return detections
        fid = row.get("fid")

        if fid is not None:
            filt = FILTER_MAP.get(fid, str(fid))
        else:
            filt = str(row.get("filter", ""))
        detections.append(
                    Detection(
                        mjd=mjd,
                        mag=float(mag),
                        magerr=float(
                            row.get("sigmapsf", row.get("magerr", 0.0))
                        ),
                        filt=filt,
                        snr=row.get("snr"),
                    )
                )

        return detections


# ==========================================================
# Classification
# ==========================================================

class ClassificationMixin:

    @staticmethod
    def from_series(
        row: pd.Series,
        classifier: str | None = None,
    ) -> Classification:

        probabilities = {}

        #
        # Every numeric probability column beginning
        # with "v:" is interpreted as a class.
        #

        for key, value in row.items():

            if not key.startswith("v:"):

                continue

            if value is None:

                continue

            try:

                probabilities[key[2:]] = float(value)

            except Exception:

                pass

        return Classification(
                probabilities=probabilities,
                classifier=classifier,
            )


# ==========================================================
# Host
# ==========================================================

class HostMixin:

    @staticmethod
    def from_series(
        row: pd.Series,
    ) -> HostGalaxy | None:

        if "host_name" not in row:

            return None

        return HostGalaxy(

            name=row.get("host_name"),

            redshift=row.get("host_redshift"),

            separation_arcsec=row.get("host_sep"),

            catalog=row.get("host_catalog"),
        )


# ==========================================================
# Features
# ==========================================================

class FeatureMixin:

    @staticmethod
    def from_series(row: pd.Series) -> FeatureVector:

        fv = FeatureVector()

        #
        # Copy all numeric columns that are not part
        # of the core Candidate model.
        #

        ignore = {

            "objectId",

            "ra",

            "dec",

            "jd",

            "mjd",

            "mag",

            "magpsf",

            "sigmapsf",

        }

        for key, value in row.items():

            if key in ignore:

                continue

            if key.startswith("v:"):

                continue

            if isinstance(value, numbers.Real):
                fv.add(key, float(value))

        return fv


# ==========================================================
# Candidate
# ==========================================================

class CandidateMixin:

    @staticmethod
    def from_series(
        row: pd.Series,
        broker: str = "Fink",
    ) -> Candidate:

        return Candidate(

            coordinates=CoordinatesMixin.from_series(row),

            broker_info=[
                BrokerInfoMixin.from_series(
                    row,
                    broker,
                )
            ],

            detections=DetectionMixin.from_series(row),

            classification=ClassificationMixin.from_series(
                                row,
                                classifier=broker,
                            ),

            features=FeatureMixin.from_series(row),

            host=HostMixin.from_series(row),

            discovered=datetime.utcnow(),

            last_update=datetime.utcnow(),
        )