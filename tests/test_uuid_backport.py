"""Tests for uuid-backport package"""

import sys
import time as time_module

import pytest

from uuid_backport import MAX, NIL, RFC_4122, UUID, uuid6, uuid7, uuid8

# Mark to skip tests on Python 3.14+ (uses standard library)
skip_on_py314 = pytest.mark.skipif(
    sys.version_info >= (3, 14), reason="Python 3.14+ uses standard library, not backport implementation"
)


class TestUUID6:
    """Tests for UUID version 6"""

    def test_uuid6_basic(self):
        """Test basic UUID v6 generation"""
        u = uuid6()
        assert isinstance(u, UUID)
        assert u.version == 6
        assert u.variant == RFC_4122

    def test_uuid6_with_params(self):
        """Test UUID v6 with explicit node and clock_seq"""
        node = 0x123456789ABC
        clock_seq = 0x1234
        u = uuid6(node=node, clock_seq=clock_seq)
        assert u.node == node
        assert u.clock_seq == clock_seq

    def test_uuid6_monotonic(self):
        """Test UUID v6 monotonicity"""
        u1 = uuid6()
        u2 = uuid6()
        assert u2 > u1, "UUID v6 should be monotonic"

    def test_uuid6_time_property(self):
        """Test UUID v6 time property"""
        u = uuid6()
        assert isinstance(u.time, int)
        assert u.time > 0


class TestUUID7:
    """Tests for UUID version 7"""

    def test_uuid7_basic(self):
        """Test basic UUID v7 generation"""
        u = uuid7()
        assert isinstance(u, UUID)
        assert u.version == 7
        assert u.variant == RFC_4122

    def test_uuid7_monotonic_same_ms(self):
        """Test UUID v7 monotonicity within same millisecond"""
        uuids = [uuid7() for _ in range(100)]
        # All should be monotonically increasing
        for i in range(len(uuids) - 1):
            assert uuids[i] < uuids[i + 1], f"UUID v7 should be monotonic: {uuids[i]} >= {uuids[i + 1]}"

    def test_uuid7_time_property(self):
        """Test UUID v7 time property (unix timestamp in ms)"""
        before_ms = time_module.time_ns() // 1_000_000
        u = uuid7()
        after_ms = time_module.time_ns() // 1_000_000

        # time property should return millisecond timestamp
        assert before_ms <= u.time <= after_ms

    def test_uuid7_timestamp_progression(self):
        """Test UUID v7 timestamp increases with time"""
        u1 = uuid7()
        time_module.sleep(0.002)  # Sleep 2ms
        u2 = uuid7()

        # u2 should have a later timestamp
        assert u2.time > u1.time


class TestUUID8:
    """Tests for UUID version 8"""

    def test_uuid8_basic(self):
        """Test basic UUID v8 generation (random)"""
        u = uuid8()
        assert isinstance(u, UUID)
        assert u.version == 8
        assert u.variant == RFC_4122

    def test_uuid8_with_custom_blocks(self):
        """Test UUID v8 with custom blocks"""
        a = 0xAABBCCDDEEFF  # 48-bit
        b = 0x123  # 12-bit
        c = 0x156789ABCDEF0123  # 62-bit (MSB cleared for variant)

        u = uuid8(a=a, b=b, c=c)
        assert u.version == 8
        assert u.variant == RFC_4122

        # Verify the custom blocks are preserved (with version/variant bits set)
        int_val = u.int
        extracted_a = (int_val >> 80) & 0xFFFF_FFFF_FFFF
        extracted_b = (int_val >> 64) & 0xFFF
        extracted_c = int_val & 0x3FFF_FFFF_FFFF_FFFF

        assert extracted_a == a
        assert extracted_b == b
        # c is masked to 62-bit in uuid8(), so we need to mask the expected value too
        assert extracted_c == (c & 0x3FFF_FFFF_FFFF_FFFF)

    def test_uuid8_randomness(self):
        """Test that random UUID v8 generates different values"""
        uuids = [uuid8() for _ in range(10)]
        # All should be unique
        assert len(set(uuids)) == 10


class TestNilMax:
    """Tests for NIL and MAX UUIDs"""

    def test_nil_uuid(self):
        """Test NIL UUID constant"""
        assert str(NIL) == "00000000-0000-0000-0000-000000000000"
        assert NIL.int == 0
        assert isinstance(NIL, UUID)

    def test_max_uuid(self):
        """Test MAX UUID constant"""
        assert str(MAX) == "ffffffff-ffff-ffff-ffff-ffffffffffff"
        assert MAX.int == (1 << 128) - 1
        assert isinstance(MAX, UUID)

    def test_nil_max_comparison(self):
        """Test NIL and MAX comparison"""
        assert NIL < MAX
        u = uuid7()
        assert NIL < u < MAX


class TestUUIDClassExtensions:
    """Tests for UUID class extensions"""

    def test_version_1_to_8_support(self):
        """Test that UUID constructor supports version 1-8"""
        for version in range(1, 9):
            u = UUID(int=12345, version=version)
            assert u.version == version
            assert u.variant == RFC_4122

    def test_time_property_v1(self):
        """Test time property for UUID v1 (backward compatibility)"""
        from uuid import uuid1

        u = uuid1()
        # Should work without error
        assert isinstance(u.time, int)
        assert u.time > 0

    def test_time_property_v6(self):
        """Test time property for UUID v6"""
        u = uuid6()
        assert isinstance(u.time, int)
        assert u.time > 0

    def test_time_property_v7(self):
        """Test time property for UUID v7"""
        u = uuid7()
        assert isinstance(u.time, int)
        assert u.time > 0


class TestBackwardCompatibility:
    """Tests for backward compatibility with standard uuid module"""

    def test_import_standard_functions(self):
        """Test that standard uuid functions are available"""
        from uuid_backport import NAMESPACE_DNS, NAMESPACE_URL, uuid1, uuid3, uuid4, uuid5

        # Should all work
        u1 = uuid1()
        u3 = uuid3(NAMESPACE_DNS, "example.com")
        u4 = uuid4()
        u5 = uuid5(NAMESPACE_URL, "https://example.com")

        assert u1.version == 1
        assert u3.version == 3
        assert u4.version == 4
        assert u5.version == 5


class TestUUIDClassCompatibility:
    """Strict tests for UUID class compatibility with standard uuid module"""

    def test_isinstance_check(self):
        """Test that uuid_backport.UUID is instance of uuid.UUID"""
        import uuid as std_uuid

        u_backport = UUID("12345678-1234-5678-1234-567812345678")
        assert isinstance(u_backport, std_uuid.UUID), "uuid_backport.UUID must be instance of uuid.UUID"

    def test_all_constructor_forms(self):
        """Test all UUID constructor forms match standard uuid"""
        import uuid as std_uuid

        test_uuid = "12345678-1234-5678-1234-567812345678"
        test_bytes = b"\x12\x34\x56\x78\x12\x34\x56\x78\x12\x34\x56\x78\x12\x34\x56\x78"
        test_int = 0x12345678123456781234567812345678

        # Test hex string
        u1 = UUID(test_uuid)
        u2 = std_uuid.UUID(test_uuid)
        assert u1.int == u2.int

        # Test bytes
        u3 = UUID(bytes=test_bytes)
        u4 = std_uuid.UUID(bytes=test_bytes)
        assert u3.int == u4.int

        # Test int
        u5 = UUID(int=test_int)
        u6 = std_uuid.UUID(int=test_int)
        assert u5.int == u6.int

        # Test fields
        fields = (0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678)
        u7 = UUID(fields=fields)
        u8 = std_uuid.UUID(fields=fields)
        assert u7.int == u8.int

    def test_all_properties(self):
        """Test all UUID properties match standard uuid"""
        import uuid as std_uuid

        test_uuid = "12345678-1234-5678-1234-567812345678"
        u_backport = UUID(test_uuid)
        u_std = std_uuid.UUID(test_uuid)

        # Test all properties
        assert u_backport.int == u_std.int
        assert u_backport.bytes == u_std.bytes
        assert u_backport.bytes_le == u_std.bytes_le
        assert u_backport.fields == u_std.fields
        assert u_backport.time_low == u_std.time_low
        assert u_backport.time_mid == u_std.time_mid
        assert u_backport.time_hi_version == u_std.time_hi_version
        assert u_backport.clock_seq_hi_variant == u_std.clock_seq_hi_variant
        assert u_backport.clock_seq_low == u_std.clock_seq_low
        assert u_backport.clock_seq == u_std.clock_seq
        assert u_backport.node == u_std.node
        assert u_backport.hex == u_std.hex
        assert u_backport.urn == u_std.urn
        assert u_backport.variant == u_std.variant
        assert u_backport.version == u_std.version

    def test_string_representations(self):
        """Test string representations match"""
        import uuid as std_uuid

        test_uuid = "12345678-1234-5678-1234-567812345678"
        u_backport = UUID(test_uuid)
        u_std = std_uuid.UUID(test_uuid)

        assert str(u_backport) == str(u_std)
        assert repr(u_backport) == repr(u_std)

    def test_comparison_operators(self):
        """Test all comparison operators"""
        u1 = UUID("00000000-0000-0000-0000-000000000001")
        u2 = UUID("00000000-0000-0000-0000-000000000002")
        u3 = UUID("00000000-0000-0000-0000-000000000001")

        assert u1 == u3
        assert u1 != u2
        assert u1 < u2
        assert u2 > u1
        assert u1 <= u3
        assert u1 >= u3
        assert u2 >= u1

    def test_hash_compatibility(self):
        """Test that hash works and is consistent"""
        u1 = UUID("12345678-1234-5678-1234-567812345678")
        u2 = UUID("12345678-1234-5678-1234-567812345678")

        assert hash(u1) == hash(u2)

        # Can be used in sets and dicts
        uuid_set = {u1, u2}
        assert len(uuid_set) == 1

        uuid_dict = {u1: "value"}
        assert uuid_dict[u2] == "value"

    def test_immutability(self):
        """Test that UUID is immutable"""
        u = UUID("12345678-1234-5678-1234-567812345678")

        try:
            u.int = 999
            assert False, "Should not be able to set attribute"
        except TypeError:
            pass

    def test_pickle_compatibility(self):
        """Test pickle serialization/deserialization"""
        import pickle

        u_original = uuid7()

        # Pickle and unpickle
        pickled = pickle.dumps(u_original)
        u_restored = pickle.loads(pickled)

        assert u_original == u_restored
        assert u_original.int == u_restored.int
        assert u_original.is_safe == u_restored.is_safe

    def test_cross_compatibility_with_std_uuid(self):
        """Test that backport UUIDs work with standard uuid UUIDs"""
        import uuid as std_uuid

        u_std = std_uuid.uuid4()
        u_backport = uuid7()

        # Should be comparable
        assert isinstance(u_std < u_backport, bool)
        assert isinstance(u_std == u_backport, bool)

        # Can mix in sets
        mixed_set = {u_std, u_backport}
        assert len(mixed_set) == 2

        # Can mix in comparisons
        all_uuids = sorted([u_std, u_backport, NIL, MAX])
        assert len(all_uuids) == 4
        assert all_uuids[0] == NIL
        assert all_uuids[-1] == MAX

    def test_int_conversion(self):
        """Test int() conversion"""
        u = UUID("12345678-1234-5678-1234-567812345678")
        assert int(u) == 0x12345678123456781234567812345678
        assert int(u) == u.int

    def test_version_validation(self):
        """Test version parameter validation"""
        # Valid versions 1-8
        for version in range(1, 9):
            u = UUID(int=12345, version=version)
            assert u.version == version

        # Invalid version should raise
        with pytest.raises(ValueError):
            UUID(int=12345, version=0)

        with pytest.raises(ValueError):
            UUID(int=12345, version=9)


class TestUUIDConstructorErrors:
    """Tests for UUID constructor error cases"""

    def test_no_arguments_error(self):
        """Test that UUID constructor requires at least one argument"""
        with pytest.raises(TypeError):
            UUID()

    def test_multiple_arguments_error(self):
        """Test that UUID constructor rejects multiple arguments"""
        with pytest.raises(TypeError):
            UUID(hex="12345678-1234-5678-1234-567812345678", int=12345)

    def test_badly_formed_hex_string(self):
        """Test that badly formed hex strings are rejected"""
        with pytest.raises(ValueError):
            UUID(hex="12345678-1234-5678-1234-56781234567")  # too short

        with pytest.raises(ValueError):
            UUID(hex="not-a-valid-uuid-string")

    def test_bytes_wrong_length(self):
        """Test that bytes argument must be exactly 16 bytes"""
        with pytest.raises(ValueError):
            UUID(bytes=b"\x12\x34\x56\x78" * 3)  # 12 bytes

    def test_bytes_le_constructor(self):
        """Test UUID construction with bytes_le parameter"""
        test_bytes_le = b"\x78\x56\x34\x12\x34\x12\x78\x56\x12\x34\x56\x78\x12\x34\x56\x78"
        u = UUID(bytes_le=test_bytes_le)
        assert isinstance(u, UUID)
        # Verify it's a valid UUID
        assert u.int > 0

    def test_bytes_le_wrong_length(self):
        """Test that bytes_le argument must be exactly 16 bytes"""
        with pytest.raises(ValueError):
            UUID(bytes_le=b"\x12\x34\x56\x78" * 3)  # 12 bytes

    def test_fields_wrong_tuple_size(self):
        """Test that fields argument must be a 6-tuple"""
        with pytest.raises(ValueError):
            UUID(fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34))  # only 5 elements

    def test_fields_out_of_range(self):
        """Test field value range validation"""
        # field 1 (time_low) out of range
        with pytest.raises(ValueError):
            UUID(fields=(1 << 32, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678))

        # field 2 (time_mid) out of range
        with pytest.raises(ValueError):
            UUID(fields=(0x12345678, 1 << 16, 0x5678, 0x12, 0x34, 0x567812345678))

        # field 3 (time_hi_version) out of range
        with pytest.raises(ValueError):
            UUID(fields=(0x12345678, 0x1234, 1 << 16, 0x12, 0x34, 0x567812345678))

        # field 4 (clock_seq_hi_variant) out of range
        with pytest.raises(ValueError):
            UUID(fields=(0x12345678, 0x1234, 0x5678, 1 << 8, 0x34, 0x567812345678))

        # field 5 (clock_seq_low) out of range
        with pytest.raises(ValueError):
            UUID(fields=(0x12345678, 0x1234, 0x5678, 0x12, 1 << 8, 0x567812345678))

        # field 6 (node) out of range
        with pytest.raises(ValueError):
            UUID(fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34, 1 << 48))

    def test_int_out_of_range(self):
        """Test that int argument must be a valid 128-bit value"""
        with pytest.raises(ValueError):
            UUID(int=-1)

        with pytest.raises(ValueError):
            UUID(int=(1 << 128))


@skip_on_py314
class TestUUID6EdgeCases:
    """Tests for UUID v6 edge cases (backport implementation only)"""

    def test_uuid6_timestamp_monotonicity_same_time(self):
        """Test uuid6 timestamp is incremented when generated at same time"""
        import time

        import uuid_backport._backport as bp

        # Save and reset state
        original = bp._last_timestamp_v6

        try:
            # Calculate a future timestamp that will trigger monotonicity check
            future_timestamp = time.time_ns() // 100 + 0x01B21DD213814000 + 1_000_000
            bp._last_timestamp_v6 = future_timestamp

            uuid6()

            # timestamp should be incremented by 1
            assert bp._last_timestamp_v6 == future_timestamp + 1
        finally:
            # Restore state
            bp._last_timestamp_v6 = original


@skip_on_py314
class TestUUID7EdgeCases:
    """Tests for UUID v7 edge cases (backport implementation only)"""

    def test_uuid7_counter_overflow(self):
        """Test uuid7 counter overflow behavior"""
        import uuid_backport._backport as bp

        # Reset state
        bp._last_timestamp_v7 = None
        bp._last_counter_v7 = 0

        # Generate first UUID
        _ = uuid7()
        current_ts = bp._last_timestamp_v7

        # Set counter to max value (42-bit: 0x3FF_FFFF_FFFF)
        bp._last_counter_v7 = 0x3FF_FFFF_FFFF

        # Generate next UUID - should overflow counter and increment timestamp
        _ = uuid7()

        # Timestamp should be incremented
        assert bp._last_timestamp_v7 > current_ts
        # Counter should be reset to a new random value < max
        assert bp._last_counter_v7 < 0x3FF_FFFF_FFFF

    def test_uuid7_backward_time(self):
        """Test uuid7 handles backward time movement"""
        import uuid_backport._backport as bp

        # Reset state
        bp._last_timestamp_v7 = None
        bp._last_counter_v7 = 0

        _ = uuid7()
        last_ts = bp._last_timestamp_v7

        # Simulate backward time by setting last timestamp to future
        bp._last_timestamp_v7 = last_ts + 1000

        u2 = uuid7()
        # Should use last_timestamp + 1
        assert u2.time >= last_ts + 1000


class TestUUIDTimeProperty:
    """Tests for UUID time property with different versions"""

    def test_time_property_uuid_v1(self):
        """Test time property works for UUID v1"""
        from uuid import uuid1 as std_uuid1

        u = std_uuid1()
        # Create our UUID from the same int
        u_backport = UUID(int=u.int)
        assert u_backport.time == u.time


class TestPackageVersion:
    """Tests for package version handling"""

    def test_version_exists(self):
        """Test that __version__ is defined"""
        import uuid_backport

        assert hasattr(uuid_backport, "__version__")
        assert isinstance(uuid_backport.__version__, str)
        assert len(uuid_backport.__version__) > 0

    def test_version_fallback_on_package_not_found(self):
        """Test that __version__ falls back to 'unknown' when package metadata is not found"""
        import importlib
        from importlib.metadata import PackageNotFoundError
        from unittest.mock import patch

        # Mock the version function to raise PackageNotFoundError
        with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
            # Reload the module to trigger the exception handler
            import uuid_backport

            importlib.reload(uuid_backport)
            assert uuid_backport.__version__ == "unknown"
