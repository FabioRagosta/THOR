"""
Coordinates parser.
"""

from __future__ import annotations

from thor.model import Coordinates

from .base import BaseParser


class CoordinatesParser(BaseParser):

    def parse(
        self,
        raw,
        *,
        ra_key="ra",
        dec_key="dec",
    ):

        return Coordinates(

            ra=float(raw[ra_key]),

            dec=float(raw[dec_key]),
        )
