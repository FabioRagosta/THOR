"""
Host parser.
"""

from __future__ import annotations

from thor.model import HostGalaxy

from .base import BaseParser


class HostParser(BaseParser):

    def parse(
        self,
        raw,
    ):

        return HostGalaxy(

            name=raw.get("name"),

            redshift=raw.get("redshift"),

            separation_arcsec=raw.get("separation_arcsec"),

            catalog=raw.get("catalog"),
        )
