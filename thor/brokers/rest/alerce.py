"""
THOR v2

REST client for the ALeRCE broker.
"""

from __future__ import annotations

from .base import BaseRESTClient

from alerce.core import Alerce


class AlerceREST:

    def __init__(
        self,
        survey="ztf",
        timeout=30,
        retries=3,
    ):

        self.survey = survey.lower()

        self.timeout = timeout
        self.retries = retries

        self.client = Alerce()

    # ---------------------------------------------------------
    @property
    def survey(self):
        return self._survey
    
    @survey.setter
    def survey(self, value):
        self._survey = value.lower()
    
    def get_object(self, oid):

        return self.client.query_object(
            oid=oid,
        )

    # ---------------------------------------------------------

    def lightcurve(self, oid):

        return self.client.query_detections(
            oid=oid,
            survey=self._survey,
        )

    # ---------------------------------------------------------

    def probabilities(self, oid):

        return self.client.query_probabilities(
            oid=oid,
        )

    # ---------------------------------------------------------

   

    def search(
        self,
        **kwargs,
    ):
    
        return self.client.query_objects(
            survey=self._survey,
            format="json",
            **kwargs,
        )

    # ---------------------------------------------------------

    def query(
        self,
        endpoint: str,
        params: dict | None = None,
    ):

        return self.get(
            endpoint,
            params=params,
        )