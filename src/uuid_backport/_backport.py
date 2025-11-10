"""Backport implementation of Python 3.14 UUID features for Python 3.9-3.13"""

import os
import time
from uuid import UUID as Base_UUID
from uuid import SafeUUID, getnode

__all__ = ["uuid6", "uuid7", "uuid8", "NIL", "MAX"]

int_ = int  # The built-in int type
bytes_ = bytes  # The built-in bytes type

_UINT_128_MAX = (1 << 128) - 1

# 128-bit mask to clear the variant and version bits of a UUID integral value
_RFC_4122_CLEARFLAGS_MASK = ~((0xF000 << 64) | (0xC000 << 48))

# Constants from Python 3.14
_RFC_4122_VERSION_6_FLAGS = (6 << 76) | (0x8000 << 48)
_RFC_4122_VERSION_7_FLAGS = (7 << 76) | (0x8000 << 48)
_RFC_4122_VERSION_8_FLAGS = (8 << 76) | (0x8000 << 48)

# Global state for uuid6/uuid7
_last_timestamp_v6 = None
_last_timestamp_v7 = None
_last_counter_v7 = 0  # 42-bit counter


class UUID(Base_UUID):
    def __init__(
        self, hex=None, bytes=None, bytes_le=None, fields=None, int=None, version=None, *, is_safe=SafeUUID.unknown
    ):
        r"""Create a UUID from either a string of 32 hexadecimal digits,
        a string of 16 bytes as the 'bytes' argument, a string of 16 bytes
        in little-endian order as the 'bytes_le' argument, a tuple of six
        integers (32-bit time_low, 16-bit time_mid, 16-bit time_hi_version,
        8-bit clock_seq_hi_variant, 8-bit clock_seq_low, 48-bit node) as
        the 'fields' argument, or a single 128-bit integer as the 'int'
        argument.  When a string of hex digits is given, curly braces,
        hyphens, and a URN prefix are all optional.  For example, these
        expressions all yield the same UUID:

        UUID('{12345678-1234-5678-1234-567812345678}')
        UUID('12345678123456781234567812345678')
        UUID('urn:uuid:12345678-1234-5678-1234-567812345678')
        UUID(bytes='\x12\x34\x56\x78'*4)
        UUID(bytes_le='\x78\x56\x34\x12\x34\x12\x78\x56' +
                      '\x12\x34\x56\x78\x12\x34\x56\x78')
        UUID(fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678))
        UUID(int=0x12345678123456781234567812345678)

        Exactly one of 'hex', 'bytes', 'bytes_le', 'fields', or 'int' must
        be given.  The 'version' argument is optional; if given, the resulting
        UUID will have its variant and version set according to RFC 4122,
        overriding the given 'hex', 'bytes', 'bytes_le', 'fields', or 'int'.

        is_safe is an enum exposed as an attribute on the instance.  It
        indicates whether the UUID has been generated in a way that is safe
        for multiprocessing applications, via uuid_generate_time_safe(3).
        """

        if [hex, bytes, bytes_le, fields, int].count(None) != 4:
            raise TypeError("one of the hex, bytes, bytes_le, fields, or int arguments must be given")
        if int is not None:
            pass
        elif hex is not None:
            hex = hex.replace("urn:", "").replace("uuid:", "")
            hex = hex.strip("{}").replace("-", "")
            if len(hex) != 32:
                raise ValueError("badly formed hexadecimal UUID string")
            int = int_(hex, 16)
        elif bytes_le is not None:
            if len(bytes_le) != 16:
                raise ValueError("bytes_le is not a 16-char string")
            assert isinstance(bytes_le, bytes_), repr(bytes_le)
            bytes = bytes_le[4 - 1 :: -1] + bytes_le[6 - 1 : 4 - 1 : -1] + bytes_le[8 - 1 : 6 - 1 : -1] + bytes_le[8:]
            int = int_.from_bytes(bytes, byteorder="big")
        elif bytes is not None:
            if len(bytes) != 16:
                raise ValueError("bytes is not a 16-char string")
            assert isinstance(bytes, bytes_), repr(bytes)
            int = int_.from_bytes(bytes, byteorder="big")
        elif fields is not None:
            if len(fields) != 6:
                raise ValueError("fields is not a 6-tuple")
            (time_low, time_mid, time_hi_version, clock_seq_hi_variant, clock_seq_low, node) = fields
            if not 0 <= time_low < (1 << 32):
                raise ValueError("field 1 out of range (need a 32-bit value)")
            if not 0 <= time_mid < (1 << 16):
                raise ValueError("field 2 out of range (need a 16-bit value)")
            if not 0 <= time_hi_version < (1 << 16):
                raise ValueError("field 3 out of range (need a 16-bit value)")
            if not 0 <= clock_seq_hi_variant < (1 << 8):
                raise ValueError("field 4 out of range (need an 8-bit value)")
            if not 0 <= clock_seq_low < (1 << 8):
                raise ValueError("field 5 out of range (need an 8-bit value)")
            if not 0 <= node < (1 << 48):
                raise ValueError("field 6 out of range (need a 48-bit value)")
            clock_seq = (clock_seq_hi_variant << 8) | clock_seq_low
            int = (time_low << 96) | (time_mid << 80) | (time_hi_version << 64) | (clock_seq << 48) | node
        if not 0 <= int <= _UINT_128_MAX:
            raise ValueError("int is out of range (need a 128-bit value)")
        if version is not None:
            if not 1 <= version <= 8:
                raise ValueError("illegal version number")
            # clear the variant and the version number bits
            int &= _RFC_4122_CLEARFLAGS_MASK
            # Set the variant to RFC 4122/9562.
            int |= 0x8000_0000_0000_0000  # (0x8000 << 48)
            # Set the version number.
            int |= version << 76
        object.__setattr__(self, "int", int)
        object.__setattr__(self, "is_safe", is_safe)

    @classmethod
    def _from_int(cls, value):
        """Create a UUID from an integer *value*. Internal use only."""
        assert 0 <= value <= _UINT_128_MAX, repr(value)
        self = object.__new__(cls)
        object.__setattr__(self, "int", value)
        object.__setattr__(self, "is_safe", SafeUUID.unknown)
        return self

    @property
    def time(self):
        if self.version == 6:
            # time_hi (32) | time_mid (16) | ver (4) | time_lo (12) | ... (64)
            time_hi = self.int >> 96
            time_lo = (self.int >> 64) & 0x0FFF
            return time_hi << 28 | (self.time_mid << 12) | time_lo
        elif self.version == 7:
            # unix_ts_ms (48) | ... (80)
            return self.int >> 80
        else:
            # time_lo (32) | time_mid (16) | ver (4) | time_hi (12) | ... (64)
            #
            # For compatibility purposes, we do not warn or raise when the
            # version is not 1 (timestamp is irrelevant to other versions).
            time_hi = (self.int >> 64) & 0x0FFF
            time_lo = self.int >> 96
            return time_hi << 48 | (self.time_mid << 32) | time_lo


def uuid6(node=None, clock_seq=None):
    """Similar to :func:`uuid1` but where fields are ordered differently
    for improved DB locality.

    More precisely, given a 60-bit timestamp value as specified for UUIDv1,
    for UUIDv6 the first 48 most significant bits are stored first, followed
    by the 4-bit version (same position), followed by the remaining 12 bits
    of the original 60-bit timestamp.
    """
    global _last_timestamp_v6
    import time

    nanoseconds = time.time_ns()
    # 0x01b21dd213814000 is the number of 100-ns intervals between the
    # UUID epoch 1582-10-15 00:00:00 and the Unix epoch 1970-01-01 00:00:00.
    timestamp = nanoseconds // 100 + 0x01B21DD213814000
    if _last_timestamp_v6 is not None and timestamp <= _last_timestamp_v6:
        timestamp = _last_timestamp_v6 + 1
    _last_timestamp_v6 = timestamp
    if clock_seq is None:
        import random

        clock_seq = random.getrandbits(14)  # instead of stable storage
    time_hi_and_mid = (timestamp >> 12) & 0xFFFF_FFFF_FFFF
    time_lo = timestamp & 0x0FFF  # keep 12 bits and clear version bits
    clock_s = clock_seq & 0x3FFF  # keep 14 bits and clear variant bits
    if node is None:
        node = getnode()
    # --- 32 + 16 ---   -- 4 --   -- 12 --  -- 2 --   -- 14 ---    48
    # time_hi_and_mid | version | time_lo | variant | clock_seq | node
    int_uuid_6 = time_hi_and_mid << 80
    int_uuid_6 |= time_lo << 64
    int_uuid_6 |= clock_s << 48
    int_uuid_6 |= node & 0xFFFF_FFFF_FFFF
    # by construction, the variant and version bits are already cleared
    int_uuid_6 |= _RFC_4122_VERSION_6_FLAGS
    return UUID._from_int(int_uuid_6)


def _uuid7_get_counter_and_tail():
    rand = int.from_bytes(os.urandom(10), byteorder="big")
    # 42-bit counter with MSB set to 0
    counter = (rand >> 32) & 0x1FF_FFFF_FFFF
    # 32-bit random data
    tail = rand & 0xFFFF_FFFF
    return counter, tail


def uuid7():
    """Generate a UUID from a Unix timestamp in milliseconds and random bits.

    UUIDv7 objects feature monotonicity within a millisecond.
    """
    # --- 48 ---   -- 4 --   --- 12 ---   -- 2 --   --- 30 ---   - 32 -
    # unix_ts_ms | version | counter_hi | variant | counter_lo | random
    #
    # 'counter = counter_hi | counter_lo' is a 42-bit counter constructed
    # with Method 1 of RFC 9562, §6.2, and its MSB is set to 0.
    #
    # 'random' is a 32-bit random value regenerated for every new UUID.
    #
    # If multiple UUIDs are generated within the same millisecond, the LSB
    # of 'counter' is incremented by 1. When overflowing, the timestamp is
    # advanced and the counter is reset to a random 42-bit integer with MSB
    # set to 0.

    global _last_timestamp_v7
    global _last_counter_v7

    nanoseconds = time.time_ns()
    timestamp_ms = nanoseconds // 1_000_000

    if _last_timestamp_v7 is None or timestamp_ms > _last_timestamp_v7:
        counter, tail = _uuid7_get_counter_and_tail()
    else:
        if timestamp_ms < _last_timestamp_v7:
            timestamp_ms = _last_timestamp_v7 + 1
        # advance the 42-bit counter
        counter = _last_counter_v7 + 1
        if counter > 0x3FF_FFFF_FFFF:
            # advance the 48-bit timestamp
            timestamp_ms += 1
            counter, tail = _uuid7_get_counter_and_tail()
        else:
            # 32-bit random data
            tail = int.from_bytes(os.urandom(4), byteorder="big")

    unix_ts_ms = timestamp_ms & 0xFFFF_FFFF_FFFF
    counter_msbs = counter >> 30
    # keep 12 counter's MSBs and clear variant bits
    counter_hi = counter_msbs & 0x0FFF
    # keep 30 counter's LSBs and clear version bits
    counter_lo = counter & 0x3FFF_FFFF
    # ensure that the tail is always a 32-bit integer (by construction,
    # it is already the case, but future interfaces may allow the user
    # to specify the random tail)
    tail &= 0xFFFF_FFFF

    int_uuid_7 = unix_ts_ms << 80
    int_uuid_7 |= counter_hi << 64
    int_uuid_7 |= counter_lo << 32
    int_uuid_7 |= tail
    # by construction, the variant and version bits are already cleared
    int_uuid_7 |= _RFC_4122_VERSION_7_FLAGS
    res = UUID._from_int(int_uuid_7)

    # defer global update until all computations are done
    _last_timestamp_v7 = timestamp_ms
    _last_counter_v7 = counter
    return res


def uuid8(a=None, b=None, c=None):
    """Generate a UUID from three custom blocks.

    * 'a' is the first 48-bit chunk of the UUID (octets 0-5);
    * 'b' is the mid 12-bit chunk (octets 6-7);
    * 'c' is the last 62-bit chunk (octets 8-15).

    When a value is not specified, a pseudo-random value is generated.
    """
    if a is None:
        import random

        a = random.getrandbits(48)
    if b is None:
        import random

        b = random.getrandbits(12)
    if c is None:
        import random

        c = random.getrandbits(62)
    int_uuid_8 = (a & 0xFFFF_FFFF_FFFF) << 80
    int_uuid_8 |= (b & 0xFFF) << 64
    int_uuid_8 |= c & 0x3FFF_FFFF_FFFF_FFFF
    # by construction, the variant and version bits are already cleared
    int_uuid_8 |= _RFC_4122_VERSION_8_FLAGS
    return UUID._from_int(int_uuid_8)


# RFC 9562 Sections 5.9 and 5.10 define the special Nil and Max UUID formats.
NIL = UUID("00000000-0000-0000-0000-000000000000")
MAX = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
