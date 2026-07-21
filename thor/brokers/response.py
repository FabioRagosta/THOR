"""
THOR v2
========

Standard broker response objects.

Every HTTP transaction performed by a broker is wrapped
inside a BrokerResponse object, independently of the
underlying HTTP library.

Author:
Fabio Ragosta et al.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(slots=True)
class BrokerResponse:
    """
    Generic broker response.
    """

    status_code: int

    payload: Any = None

    url: Optional[str] = None

    headers: Dict[str, str] = field(default_factory=dict)

    elapsed: Optional[float] = None

    broker: Optional[str] = None

    retrieved_at: datetime = field(default_factory=datetime.utcnow)

    message: Optional[str] = None

    # --------------------------------------------------

    @property
    def ok(self) -> bool:

        return 200 <= self.status_code < 300

    # --------------------------------------------------

    def json(self):

        return self.payload

    # --------------------------------------------------

    def __bool__(self):

        return self.ok

    # --------------------------------------------------

    def __repr__(self):

        return (
            f"<BrokerResponse "
            f"status={self.status_code} "
            f"broker={self.broker}>"
        )
