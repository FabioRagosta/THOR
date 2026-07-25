"""
Photometry parser.
"""

from __future__ import annotations

from thor.model import Detection

from .base import BaseParser


class DetectionParser(BaseParser):

    def parse(
        self,
        raw,
        *,
        mjd_key="mjd",
        mag_key="mag",
        err_key="magerr",
        filter_key="filter",
        snr_key=None,
    ):

        return Detection(

            mjd=float(raw[mjd_key]),

            mag=float(raw[mag_key]),

            magerr=float(raw[err_key]),

            filt=str(raw[filter_key]),

            snr=None if snr_key is None else raw.get(snr_key),
        )
