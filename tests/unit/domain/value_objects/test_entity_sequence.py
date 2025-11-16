"""Tests for EntitySequence value object"""

import pytest
from src.domain.value_objects import EntitySequence


class TestEntitySequence:
    """Test EntitySequence value object"""

    def test_valid_sequences(self):
        """Test valid entity sequences"""
        # Single digit (0-9)
        seq1 = EntitySequence(1)
        assert seq1.value == 1
        assert str(seq1) == "1"

        # Zero
        seq0 = EntitySequence(0)
        assert seq0.value == 0

        # Max single digit
        seq9 = EntitySequence(9)
        assert seq9.value == 9

    def test_invalid_sequences(self):
        """Test invalid entity sequences"""
        # Negative
        with pytest.raises(ValueError, match="must be between 0 and 9"):
            EntitySequence(-1)

        # Too large
        with pytest.raises(ValueError, match="must be between 0 and 9"):
            EntitySequence(10)

    def test_sequence_equality(self):
        """Test value object equality"""
        seq1 = EntitySequence(1)
        seq2 = EntitySequence(1)
        seq3 = EntitySequence(2)

        assert seq1 == seq2
        assert seq1 != seq3
        assert hash(seq1) == hash(seq2)

    def test_sequence_comparison(self):
        """Test sequence ordering"""
        seq1 = EntitySequence(1)
        seq5 = EntitySequence(5)
        seq9 = EntitySequence(9)

        assert seq1 < seq5
        assert seq5 < seq9
        assert seq9 > seq1

    def test_next_sequence(self):
        """Test getting next sequence"""
        seq1 = EntitySequence(1)
        seq2 = seq1.next()
        assert seq2.value == 2

        # At boundary
        seq9 = EntitySequence(9)
        with pytest.raises(ValueError, match="No next sequence"):
            seq9.next()

    def test_previous_sequence(self):
        """Test getting previous sequence"""
        seq5 = EntitySequence(5)
        seq4 = seq5.previous()
        assert seq4.value == 4

        # At boundary
        seq0 = EntitySequence(0)
        with pytest.raises(ValueError, match="No previous sequence"):
            seq0.previous()

    def test_to_hex(self):
        """Test hexadecimal representation"""
        seq0 = EntitySequence(0)
        assert seq0.to_hex() == "0"

        seq9 = EntitySequence(9)
        assert seq9.to_hex() == "9"

        seq5 = EntitySequence(5)
        assert seq5.to_hex() == "5"
