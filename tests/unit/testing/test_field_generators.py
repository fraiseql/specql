"""Tests for field value generators component"""

import pytest
from src.testing.seed.field_generators import FieldValueGenerator


def test_generate_email():
    """Test email generation"""
    gen = FieldValueGenerator(seed=42)  # Deterministic
    mapping = {"field_type": "email", "generator_type": "random"}

    email = gen.generate(mapping)
    assert "@" in email
    assert "." in email


def test_generate_phone():
    """Test phone number generation"""
    gen = FieldValueGenerator(seed=42)
    mapping = {"field_type": "phoneNumber", "generator_type": "random"}

    phone = gen.generate(mapping)
    assert isinstance(phone, str)
    assert len(phone) > 0


def test_generate_enum():
    """Test enum generation"""
    gen = FieldValueGenerator(seed=42)
    mapping = {"field_type": "enum(lead, qualified, customer)", "generator_type": "random"}

    status = gen.generate(mapping)
    assert status in ["lead", "qualified", "customer"]


def test_generate_from_examples():
    """Test generation from example values"""
    gen = FieldValueGenerator(seed=42)
    mapping = {
        "field_type": "text",
        "generator_type": "random",
        "example_values": ["red", "green", "blue"],
    }

    color = gen.generate(mapping)
    assert color in ["red", "green", "blue"]


def test_generate_integer():
    """Test integer generation with distribution"""
    gen = FieldValueGenerator(seed=42)
    mapping = {
        "field_type": "integer",
        "generator_type": "random",
        "seed_distribution": {"min": 10, "max": 100},
    }

    value = gen.generate(mapping)
    assert isinstance(value, int)
    assert 10 <= value <= 100


def test_generate_boolean():
    """Test boolean generation"""
    gen = FieldValueGenerator(seed=42)
    mapping = {"field_type": "boolean", "generator_type": "random"}

    value = gen.generate(mapping)
    assert isinstance(value, bool)


def test_generate_fixed():
    """Test fixed value generation"""
    gen = FieldValueGenerator()
    mapping = {
        "field_type": "text",
        "generator_type": "fixed",
        "generator_params": {"fixed_value": "constant"},
    }

    value = gen.generate(mapping)
    assert value == "constant"


def test_generate_sequence():
    """Test sequence generation"""
    gen = FieldValueGenerator()
    mapping = {
        "field_type": "integer",
        "generator_type": "sequence",
        "generator_params": {"start": 100, "step": 5},
    }
    context = {"instance_num": 3}

    value = gen.generate(mapping, context)
    assert value == 100 + (3 - 1) * 5  # 110


def test_generate_text():
    """Test text generation"""
    gen = FieldValueGenerator(seed=42)
    mapping = {"field_type": "text", "generator_type": "random"}

    value = gen.generate(mapping)
    assert isinstance(value, str)
    assert len(value) > 0


def test_generate_money():
    """Test money generation"""
    gen = FieldValueGenerator(seed=42)
    mapping = {"field_type": "money", "generator_type": "random"}

    value = gen.generate(mapping)
    assert isinstance(value, float)
    assert 10 <= value <= 10000


def test_generate_percentage():
    """Test percentage generation"""
    gen = FieldValueGenerator(seed=42)
    mapping = {"field_type": "percentage", "generator_type": "random"}

    value = gen.generate(mapping)
    assert isinstance(value, float)
    assert 0 <= value <= 100


def test_generate_date():
    """Test date generation"""
    gen = FieldValueGenerator(seed=42)
    mapping = {"field_type": "date", "generator_type": "random"}

    value = gen.generate(mapping)
    assert hasattr(value, "year")  # datetime.date or datetime.datetime


def test_generate_timestamptz():
    """Test timestamp generation"""
    gen = FieldValueGenerator(seed=42)
    mapping = {"field_type": "timestamptz", "generator_type": "random"}

    value = gen.generate(mapping)
    assert hasattr(value, "year") and hasattr(value, "hour")
