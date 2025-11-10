# uuid-backport

Backport of Python 3.14's UUID module (RFC 9562) for Python 3.9+

## Features

-   **UUID v6**: Reordered timestamp UUID for improved database locality
-   **UUID v7**: Timestamp-based UUID with millisecond precision and monotonicity
-   **UUID v8**: Custom 3-block UUID for application-specific use cases
-   **NIL/MAX UUID**: Special UUID constants defined in RFC 9562

## Installation

```bash
pip install uuid-backport
```

Or with uv:

```bash
uv add uuid-backport
```

## Usage

### UUID v6 - Improved Database Locality

```python
from uuid_backport import uuid6

# Similar to UUID v1 but with reordered timestamp fields
id = uuid6()
print(id)  # Example: 1ef4a7c8-9b2c-6000-8000-0242ac120002

# Maintains time-based ordering
ids = [uuid6() for _ in range(5)]
assert ids == sorted(ids)
```

### UUID v7 - Timestamp + Monotonicity

```python
from uuid_backport import uuid7

# Millisecond-precision timestamp with guaranteed monotonicity
id1 = uuid7()
id2 = uuid7()
assert id1 < id2  # Always true, even within the same millisecond

# Ideal for distributed systems
ids = [uuid7() for _ in range(1000)]
assert ids == sorted(ids)
```

### UUID v8 - Custom UUID

```python
from uuid_backport import uuid8

# Create UUID with custom 3-block structure
# a: 48-bit, b: 12-bit, c: 62-bit
custom_id = uuid8(
    a=0x123456789ABC,      # Application prefix
    b=0xDEF,                # Type identifier
    c=0x123456789ABCDEF0    # Sequence number
)

# Generate random UUID v8
random_id = uuid8()
```

### NIL/MAX UUID

```python
from uuid_backport import NIL, MAX

print(NIL)  # 00000000-0000-0000-0000-000000000000
print(MAX)  # ffffffff-ffff-ffff-ffff-ffffffffffff

# Useful for validation
def is_valid_uuid(uuid):
    return NIL < uuid < MAX
```

## Compatibility with Standard Library

```python
import uuid
from uuid_backport import uuid6, uuid7, uuid8, NIL, MAX

# Use standard library for v1-v5
v1 = uuid.uuid1()
v4 = uuid.uuid4()
v5 = uuid.uuid5(uuid.NAMESPACE_DNS, 'example.com')

# Use backport for v6-v8
v6 = uuid6()
v7 = uuid7()
v8 = uuid8()

# All are instances of uuid.UUID
assert isinstance(v6, uuid.UUID)
assert isinstance(v7, uuid.UUID)
```

## UUID Version Selection Guide

-   **UUID v1/v6**: MAC address + timestamp based

    -   v1: Legacy, poor database locality
    -   v6: Improved v1, optimized for database indexes

-   **UUID v4**: Fully random

    -   Most widely used
    -   No inherent ordering
    -   Extremely low collision probability

-   **UUID v7**: Timestamp + random + monotonic

    -   **Recommended** for most new projects
    -   Time-ordered and sortable
    -   Ideal for distributed systems
    -   Efficient database indexing

-   **UUID v8**: Custom structure
    -   For specialized requirements only
    -   Application-specific optimizations

## Development

### Setup

```bash
git clone https://github.com/line1029/uuid-backport.git
cd uuid-backport

# Install test dependencies
uv sync --group test

# Install lint tools
uv sync --group lint
```

### Testing

```bash
# Test with current Python version
uv run pytest tests/ -v

# Test with all Python versions (3.9-3.13) + lint + typing
tox

# Test specific environment
tox -e py311          # Python 3.11 only
tox -e lint           # Linting only
tox -e typing         # Type checking only
```

### Code Quality

```bash
# Run linting and format checking
tox -e lint

# Run type checking
tox -e typing

# Or run directly
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```

### Formatting

```bash
uv run ruff format .
```

## License

This project is licensed under the terms of the MIT License.

However, this package contains code that has been backported from the Python 3.14 standard library's `uuid` module. The original code from the Python standard library is licensed under the **Python Software Foundation License Version 2**.

For clarity:

-   The backporting effort, modifications, and any additional code written specifically for this project are covered by the MIT License.
-   The underlying algorithms and code structure originating from the Python standard library are subject to the terms of the PSF License.

A copy of the MIT License can be found in the `LICENSE` file, and a copy of the PSF License is included as `LICENSE.PSF`.

## References

-   [RFC 9562 - Universally Unique IDentifiers (UUID)](https://www.rfc-editor.org/rfc/rfc9562.html)
-   [Python 3.14 What's New](https://docs.python.org/3.14/whatsnew/3.14.html)
-   [Python uuid Module Documentation](https://docs.python.org/3/library/uuid.html)
