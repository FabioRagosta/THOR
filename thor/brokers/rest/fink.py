"""
REST client for the Fink broker.
"""

from __future__ import annotations

from .base import BaseRESTClient


class FinkREST(BaseRESTClient):
    """
    Thin wrapper around the Fink REST API.

    This class only performs HTTP requests.
    No parsing or Candidate creation is done here.
    """

    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "THOR/2.0",
    }

    def __init__(
        self,
        survey: str = "ztf",
        timeout: int = 30,
        retries: int = 3,
    ):

        survey = survey.lower()

        if survey == "ztf":

            base_url = "https://api.ztf.fink-portal.org"

        elif survey == "lsst":

            base_url = "https://api.lsst.fink-portal.org"

        else:

            raise ValueError(
                f"Unsupported survey: {survey}"
            )

        super().__init__(
            base_url=base_url,
            timeout=timeout,
            retries=retries,
            headers=self.DEFAULT_HEADERS,
        )

        self.survey = survey

    # ---------------------------------------------------------

    def get_object(
        self,
        object_id: str,
    ):

        return self.post(
            "/api/v1/objects",
            {
                "objectId": object_id,
                "output-format": "json",
            },
        )

    # ---------------------------------------------------------

    def lightcurve(
        self,
        object_id: str,
    ):

        return self.get_object(object_id)

    # ---------------------------------------------------------

    def cone_search(
        self,
        ra: float,
        dec: float,
        radius_arcsec: float,
        n: int = 100,
    ):

        return self.post(
            "/api/v1/conesearch",
            {
                "ra": ra,
                "dec": dec,
                "radius": radius_arcsec,
                "n": n,
                "output-format": "json",
            },
        )

    # ---------------------------------------------------------

    def latest(
                self,
                classifier: str,
                n: int = 100,
            ):

        if self.survey == "ztf":

            endpoint = "/api/v1/latests"
    
            payload = {
                "class": classifier,
                "n": n,
                "output-format": "json",
            }
    
        elif self.survey == "lsst":
    
            endpoint = "/api/v1/tags"
    
            payload = {
                "tag": classifier,
                "n": n,
                "output-format": "json",
            }
    
        else:
    
            raise ValueError(
                f"Unsupported survey: {self.survey}"
            )
    
        return self.post(
            endpoint,
            payload,
        )

    # ---------------------------------------------------------

    def query(
        self,
        endpoint: str,
        payload: dict,
    ):

        return self.post(
            endpoint,
            payload,
        )
