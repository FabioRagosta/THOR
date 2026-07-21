"""
THOR v2

REST client for the Lasair broker.
"""

from __future__ import annotations
from lasair.lasair import lasair_client
from .base import BaseRESTClient
from thor.config import CONFIG

class LasairREST(BaseRESTClient):
    
            
    BASE_URLS = {
        "ztf": "https://lasair-ztf.lsst.ac.uk",
        "lsst": "https://lasair.lsst.ac.uk",
    }

    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "THOR/2.0",
    }

    def __init__(
        self,
        token: str | None = None,
        survey: str = "ztf",
        timeout: int = 30,
        retries: int = 3,
    ):

        self._survey = survey
        self.token_ztf = CONFIG.lasair_token_ztf
        self.token_lsst = CONFIG.lasair_token_lsst
        headers = dict(self.DEFAULT_HEADERS)

        if token:
            headers["Authorization"] = f"Token {token}"
        
        super().__init__(
            base_url="https://lasair-ztf.lsst.ac.uk",
            timeout=timeout,
            retries=retries,
            headers=headers,
        )
        
        self.survey = survey
    @property
    def survey(self):
        return self._survey
    
    
    @survey.setter
    def survey(self, value):
    
        self._survey = value.lower()
    
        if self._survey == "ztf":

            self.api = lasair_client(
                token=self.token_ztf,
            )
        
        else:
        
            self.api = lasair_client(
                token=self.token_lsst,
                endpoint="https://lasair.lsst.ac.uk/api",
            )

    # ---------------------------------------------------------
        
    def get_object(
        self,
        object_id: str,
    ):

        return self.api.object(object_id)

    # ---------------------------------------------------------

    def lightcurve(
        self,
        object_id: str,
    ):

        return self.api.lightcurves([object_id])

    # ---------------------------------------------------------

    def cone_search(
        self,
        ra: float,
        dec: float,
        radius_arcsec: float,
        limit: int = 100,
    ):

        return self.api.cone(
                    ra,
                    dec,
                    radius_arcsec,
                )
        

    # ---------------------------------------------------------

    def search(
            self,
            selected="*",
            tables="objects",
            conditions="1",
            limit=100,
        ):
            return self.api.query(
                    selected=selected,
                    tables=tables,
                    conditions=conditions,
                    limit=limit,
                )

    # ---------------------------------------------------------

    def query(
        self,
        endpoint: str,
        params: dict | None = None,
    ):

        return self.get(
                    "/api/query/",
                    **params,
                )