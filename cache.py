"""
THOR v2
=======

Simple in-memory cache.

"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

class MemoryCache:

    def __init__(self):

        self._cache: dict[Any, tuple[Any, datetime | None]] = {}

    def set(
        self,
        key,
        value,
        ttl=None,
    )-> None:
        """
        ttl in seconds.
        """

        expire = None

        if ttl is not None:

            expire = datetime.utcnow() + timedelta(seconds=ttl)

        self._cache[key] = (
            value,
            expire,
        )

    def get(self, key)-> Any | None:

        if key not in self._cache:

            return None

        value, expire = self._cache[key]

        if expire is not None:

            if datetime.utcnow() > expire:

                del self._cache[key]

                return None

        return value

    def delete(self, key)-> None:

        self._cache.pop(key, None)

    def clear(self)-> None:

        self._cache.clear()

    def __contains__(self, key)-> bool:

        return self.get(key) is not None
    def __len__(self) -> int:

        return len(self._cache)