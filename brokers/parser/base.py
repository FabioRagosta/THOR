"""
THOR v2
========

Base parser.

All parsers inherit from this class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseParser(ABC):

    """
    Generic parser interface.
    """

    @abstractmethod
    def parse(self, raw):
        """
        Parse broker-specific data.
        """
        raise NotImplementedError
