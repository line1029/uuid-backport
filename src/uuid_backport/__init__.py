"""Backport of Python 3.14 UUID module (RFC 9562) for Python 3.9+

This module provides UUID v6, v7, v8 support and NIL/MAX constants
that were introduced in Python 3.14, compatible with Python 3.9-3.13.
For Python 3.14+, it directly uses the standard library implementation.
"""

import sys
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("uuid-backport")
except PackageNotFoundError:
    __version__ = "unknown"

# Re-export commonly used items from standard library
from uuid import (
    NAMESPACE_DNS,
    NAMESPACE_OID,
    NAMESPACE_URL,
    NAMESPACE_X500,
    RESERVED_FUTURE,
    RESERVED_MICROSOFT,
    RESERVED_NCS,
    RFC_4122,
    SafeUUID,
    getnode,
    uuid1,
    uuid3,
    uuid4,
    uuid5,
)

__all__ = [
    # Standard library exports
    "UUID",
    "SafeUUID",
    "getnode",
    "uuid1",
    "uuid3",
    "uuid4",
    "uuid5",
    "NAMESPACE_DNS",
    "NAMESPACE_URL",
    "NAMESPACE_OID",
    "NAMESPACE_X500",
    "RESERVED_NCS",
    "RFC_4122",
    "RESERVED_MICROSOFT",
    "RESERVED_FUTURE",
    # New in Python 3.14 / RFC 9562
    "uuid6",
    "uuid7",
    "uuid8",
    "NIL",
    "MAX",
]

# Python 3.14+ has native support for UUID v6/v7/v8 and NIL/MAX
if sys.version_info >= (3, 14):
    from uuid import MAX, NIL, UUID, uuid6, uuid7, uuid8
else:
    # Use backport implementation for Python 3.9-3.13
    from uuid_backport._backport import MAX, NIL, UUID, uuid6, uuid7, uuid8
