"""
THOR v2
========

Authentication helpers.

"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Authentication(ABC):
    """
    Base authentication class.
    """

    @abstractmethod
    def apply(self, headers: dict):

        raise NotImplementedError


# ----------------------------------------------------------


class NoAuthentication(Authentication):

    def apply(self, headers):

        return headers


# ----------------------------------------------------------


class ApiKey(Authentication):

    def __init__(
        self,
        key: str,
        header: str = "Authorization",
        prefix: str = "",
    ):

        self.key = key

        self.header = header

        self.prefix = prefix

    def apply(self, headers):

        headers[self.header] = f"{self.prefix}{self.key}"

        return headers


# ----------------------------------------------------------


class BearerToken(ApiKey):

    def __init__(self, token):

        super().__init__(
            token,
            header="Authorization",
            prefix="Bearer ",
        )
