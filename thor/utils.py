"""
THOR v2
=======

General utility functions.

"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np


def safe_float(value, default=None):
    """
    Convert a value to float.
    """

    try:
        if value is None:
            return default

        if np.isnan(value):
            return default

        return float(value)

    except Exception:
        return default


def safe_int(value, default=None):
    """
    Convert a value to int.
    """

    try:
        return int(value)

    except Exception:
        return default


def safe_str(value, default=""):
    """
    Convert to string.
    """

    if value is None:
        return default

    return str(value)


def safe_datetime(value):
    """
    Convert ISO string or datetime to datetime.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def arcsec_to_deg(value):

    return value / 3600.


def deg_to_arcsec(value):

    return value * 3600.


def mjd_to_datetime(mjd):
    """
    Placeholder.
    Later this can use astropy.
    """

    try:
        from astropy.time import Time

        return Time(mjd, format="mjd").datetime

    except Exception:
        return None
