"""
THOR v2
========

Broker registry.

"""

from __future__ import annotations

from typing import Dict, Type

from .base import BaseBroker


_BROKERS: Dict[str, Type[BaseBroker]] = {}


def register(cls):

    _BROKERS[cls.name.lower()] = cls

    return cls


def get_broker(name: str, **kwargs) -> BaseBroker:

    broker = _BROKERS.get(name.lower())

    if broker is None:

        raise ValueError(
            f"Unknown broker '{name}'."
        )

    return broker(**kwargs)


def available_brokers():

    return sorted(_BROKERS.keys())
