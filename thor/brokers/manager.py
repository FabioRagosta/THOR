"""
THOR v2
========

Broker manager.

"""

from __future__ import annotations

from typing import Dict, List

from .registry import (
    available_brokers,
    get_broker,
)

from .base import BaseBroker


class BrokerManager:

    """
    Manage all broker instances.
    """

    def __init__(self):

        self._brokers: Dict[str, BaseBroker] = {}

    # -------------------------------------------------

    def load(
        self,
        name: str,
        **kwargs,
    ) -> BaseBroker:

        broker = get_broker(
            name,
            **kwargs,
        )

        self._brokers[name.lower()] = broker

        return broker

    # -------------------------------------------------

    def get(self, name):

        return self._brokers.get(
            name.lower()
        )

    # -------------------------------------------------

    def remove(self, name):

        self._brokers.pop(
            name.lower(),
            None,
        )

    # -------------------------------------------------

    def clear(self):

        self._brokers.clear()

    # -------------------------------------------------

    @property
    def brokers(self):

        return list(
            self._brokers.keys()
        )

    # -------------------------------------------------

    
    def available(self):

        return available_brokers()

    # -------------------------------------------------

    def __contains__(self, name):

        return name.lower() in self._brokers
