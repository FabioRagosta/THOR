"""
Common REST client.
"""

from __future__ import annotations

from typing import Any
import json, ast
from thor.brokers.client import BrokerClient
from thor.exception import BrokerError


class BaseRESTClient:

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        retries: int = 3,
        headers: dict[str, str] | None = None,
    ):

        self.base_url = base_url.rstrip("/")

        self.client = BrokerClient(
            timeout=timeout,
            retries=retries,
        )

        if headers:
            self.client.session.headers.update(headers)
        
    # -----------------------------------------------------

    def get(
        self,
        endpoint: str,
        **params: Any,
    ) -> Any:

        response = self.client.get(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            params=params,
        )

        return self._decode(response)

    # -----------------------------------------------------

    def post(
        self,
        endpoint: str,
        payload: dict,
    ) -> Any:

        response = self.client.post(
            f"{self.base_url}/{endpoint.lstrip('/')}",
            json=payload,
        )

        return self._decode(response)

    # -----------------------------------------------------

    @staticmethod
    def _decode(response):
    
        if response is None:
            raise BrokerError("Empty response.")
    
        text = response.text.strip()
    
        if not text:
            return None
    
        #
        # JSON standard
        #
    
        try:
            return response.json()
    
        except Exception:
            pass
    
        #
        # Python dict (Fink sometimes does this)
        #
    
        try:
            return ast.literal_eval(text)
    
        except Exception:
            pass
    
        raise BrokerError(
            f"Invalid response returned by broker:\n{text}"
        )
        #try:
        #    return response.json()

        #except Exception as exc:

        #    raise BrokerError(
        #        "Invalid JSON returned by broker."
        #    ) from exc
