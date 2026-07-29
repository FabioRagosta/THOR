"""
THOR v2
=======

General utility functions.

"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np

def get_object_id(alert):

    return (
        alert.get("objectId")        # ZTF
        or alert.get("i:objectId") 
        or alert.get("diaObjectId")  # LSST (Lasair)
        or alert.get("r:diaSourceId")  # LSST (Fink)
    )


def get_ra(alert):

    return (
        alert.get("ra")
        or alert.get("ramean")
        or alert.get("r:ra")
        or alert.get("i:ra")
    )


def get_dec(alert):

    return (
        alert.get("dec")
        or alert.get("decmean")
        or alert.get("decl")
        or alert.get("r:dec")
        or alert.get("i:dec")
    )


def get_mjd(alert):

    # ZTF
    if alert.get("i:jd"):
        return safe_float(alert["i:jd"]) - 2400000.5

    # LSST Lasair object alert
    for key in [
        "i_latestMJD",
        "r_latestMJD",
        "lastDiaSourceMjdTai",
        "firstDiaSourceMjdTai",
    ]:
        if alert.get(key):
            return safe_float(alert[key])

    # LSST Fink detection alert
    for key in [
        "r:midpointMjdTai",
        "i:midpointMjdTai",
    ]:
        if alert.get(key):
            return safe_float(alert[key])

    return None


def get_filter(alert):

    # ZTF
    if alert.get("i:fid"):
        fid = alert["i:fid"]
        return {
            1:"g",
            2:"r",
            3:"i"
        }.get(fid)

    # LSST Fink
    if alert.get("r:band"):
        return alert["r:band"]

    if alert.get("i:band"):
        return alert["i:band"]

    # LSST Lasair object summary
    bands = []

    for b in ["g", "r", "i", "z", "y", "u"]:
        if alert.get(f"{b}_psfFluxNdata",0) > 0:
            bands.append(b)

    if len(bands)==1:
        return bands[0]

    if len(bands)>1:
        return bands   # oppure None

    return None


def get_snr(alert):

    # già presente
    for key in [
        "i:snr",
        "r:snr",
    ]:
        if alert.get(key):
            return safe_float(alert[key])


    # Lasair LSST
    for band in ["g","r","i","z","y"]:

        flux = alert.get(f"{band}_psfFlux")
        err = alert.get(f"{band}_psfFluxErrMean")

        if flux is not None and err is not None and err > 0:
            return flux / err

    return None


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
