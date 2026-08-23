"""Tests for core validation helpers in base module."""

import pytest

from unifont_utils.base import Validator


def test_code_point_accepts_int_and_str():
    """Accept ints/strs and normalize, reject invalid types/values."""
    assert Validator.code_point(0x20) == "0020"
    assert Validator.code_point("1f600") == "01F600"

    with pytest.raises(TypeError):
        Validator.code_point(3.14)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        Validator.code_point("ZZ")


def test_code_points_normalize_and_deduplicate():
    """Normalize all code points and deduplicate results."""
    result = Validator.code_points(["20", "0020", 0x20, "0041"])

    assert result == ["0020", "0041"]


def test_code_points_accept_generators_and_reject_scalar_strings():
    """Accept general iterables while preserving order and rejecting scalar strings."""
    assert Validator.code_points(code_point for code_point in ["41", "42", "41"]) == [
        "0041",
        "0042",
    ]
    with pytest.raises(TypeError):
        Validator.code_points("0041")


@pytest.mark.parametrize("code_point", [-1, 0x110000])
def test_code_point_rejects_out_of_range_values(code_point):
    """Reject negative integers and values beyond the Unicode range."""
    with pytest.raises(ValueError):
        Validator.code_point(code_point)


def test_code_point_rejects_bool():
    """Booleans are not valid integer code points."""
    with pytest.raises(TypeError):
        Validator.code_point(True)


def test_hex_str_validation():
    """Uppercase valid hex strings, allow empty, reject bad lengths/chars."""
    assert Validator.hex_str("a" * 32) == "A" * 32
    assert Validator.hex_str(None) == ""

    with pytest.raises(ValueError):
        Validator.hex_str("1" * 10)
    with pytest.raises(ValueError):
        Validator.hex_str("G" * 32)
    with pytest.raises(TypeError):
        Validator.hex_str(123)  # type: ignore[arg-type]


def test_file_path_accepts_str_and_path(tmp_path):
    """Accept str or Path inputs and reject other types."""
    path = tmp_path / "file.txt"
    assert Validator.file_path(path) == path
    assert Validator.file_path(str(path)) == path

    with pytest.raises(TypeError):
        Validator.file_path(123)  # type: ignore[arg-type]
