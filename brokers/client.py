"""
THOR v2
========

Generic HTTP client used by all brokers.

Provides:

- persistent sessions
- retries
- timeout handling
- optional cache
- JSON download

Author:
Fabio Ragosta et al.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests

from thor.cache import MemoryCache
from thor.exception import BrokerError


class BrokerClient:

    def __init__(
        self,
        timeout: int = 30,
        retries: int = 3,
        cache: bool = True,
        headers: Optional[Dict[str, str]] = None,
    ):

        self.timeout = timeout

        self.retries = retries

        self.session = requests.Session()

        self.session.headers.update(
            headers or {}
        )

        self.cache = MemoryCache() if cache else None

    # -----------------------------------------------------

    def get(
        self,
        url: str,
        *,
        params: Optional[Dict] = None,
        use_cache: bool = False,
    ) -> requests.Response:

        cache_key = None

        if use_cache and self.cache is not None:

            cache_key = (
                url,
                tuple(sorted((params or {}).items()))
            )

            cached = self.cache.get(cache_key)

            if cached is not None:

                return cached

        last_exception = None

        for _ in range(self.retries + 1):

            try:

                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )

                response.raise_for_status()

                if cache_key is not None:

                    self.cache.set(
                        cache_key,
                        response,
                        ttl=3600,
                    )

                return response

            except requests.RequestException as exc:

                last_exception = exc

                time.sleep(1)

        raise BrokerError(last_exception)

    # -----------------------------------------------------

    def post(
        self,
        url: str,
        *,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> requests.Response:

        last_exception = None

        for _ in range(self.retries + 1):

            try:

                response = self.session.post(
                    url,
                    json=json,
                    data=data,
                    timeout=self.timeout,
                )
                
                #response.raise_for_status()

                return response

            except Exception as exc:

                last_exception = exc

                time.sleep(1)

        raise BrokerError(last_exception)

    # -----------------------------------------------------

    def get_json(
        self,
        url: str,
        **kwargs,
    ) -> Any:

        return self.get(
            url,
            **kwargs,
        ).json()

    # -----------------------------------------------------

    def get_text(
        self,
        url: str,
        **kwargs,
    ) -> str:

        return self.get(
            url,
            **kwargs,
        ).text

    # -----------------------------------------------------

    def close(self):

        self.session.close()
