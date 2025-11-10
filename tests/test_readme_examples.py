"""Test code examples from README.md to ensure they work correctly"""

import uuid

from uuid_backport import MAX, NIL, uuid6, uuid7, uuid8


class TestReadmeExamples:
    """Test all code examples from README.md"""

    def test_uuid6_example(self):
        """Test UUID v6 example from README"""
        # Similar to UUID v1 but with reordered timestamp fields
        id = uuid6()
        assert str(id)  # Should be a valid UUID string

        # Maintains time-based ordering
        ids = [uuid6() for _ in range(5)]
        assert ids == sorted(ids)

    def test_uuid7_example(self):
        """Test UUID v7 example from README"""
        # Millisecond-precision timestamp with guaranteed monotonicity
        id1 = uuid7()
        id2 = uuid7()
        assert id1 < id2  # Always true, even within the same millisecond

        # Ideal for distributed systems
        ids = [uuid7() for _ in range(1000)]
        assert ids == sorted(ids)

    def test_uuid8_example(self):
        """Test UUID v8 example from README"""
        # Create UUID with custom 3-block structure
        # a: 48-bit, b: 12-bit, c: 62-bit
        custom_id = uuid8(
            a=0x123456789ABC,  # Application prefix
            b=0xDEF,  # Type identifier
            c=0x123456789ABCDEF0,  # Sequence number
        )
        assert custom_id.version == 8

        # Generate random UUID v8
        random_id = uuid8()
        assert random_id.version == 8

    def test_nil_max_example(self):
        """Test NIL/MAX example from README"""
        assert str(NIL) == "00000000-0000-0000-0000-000000000000"
        assert str(MAX) == "ffffffff-ffff-ffff-ffff-ffffffffffff"

        # Useful for validation
        def is_valid_uuid(uuid_obj):
            return NIL < uuid_obj < MAX

        test_uuid = uuid7()
        assert is_valid_uuid(test_uuid)

    def test_compatibility_example(self):
        """Test compatibility example from README"""
        from uuid_backport import uuid6, uuid7, uuid8

        # Use standard library for v1-v5
        v1 = uuid.uuid1()
        v4 = uuid.uuid4()
        v5 = uuid.uuid5(uuid.NAMESPACE_DNS, "example.com")

        # Use backport for v6-v8
        v6 = uuid6()
        v7 = uuid7()
        v8 = uuid8()

        # All are instances of uuid.UUID
        assert isinstance(v1, uuid.UUID)
        assert isinstance(v4, uuid.UUID)
        assert isinstance(v5, uuid.UUID)
        assert isinstance(v6, uuid.UUID)
        assert isinstance(v7, uuid.UUID)
        assert isinstance(v8, uuid.UUID)
