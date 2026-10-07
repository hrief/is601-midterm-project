import pytest

from app.exceptions import ValidationError
from app.input_validators import validate_number, validate_operation


@pytest.mark.parametrize(
    "value,expected",
    [
        ("10", 10.0),
        ("-5", -5.0),
        ("3.14", 3.14),
        ("0", 0.0),
        ("1e3", 1000.0),
    ],
)
def test_validate_number(value, expected):
    """Test valid numeric input."""
    assert validate_number(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "potato",
        "",
        "five",
        None,
    ],
)
def test_validate_invalid_number(value):
    """Test invalid numeric input."""
    with pytest.raises(ValidationError):
        validate_number(value)


@pytest.mark.parametrize(
    "operation,expected",
    [
        ("add", "add"),
        ("ADD", "add"),
        (" subtract ", "subtract"),
        ("multiply", "multiply"),
        ("divide", "divide"),
        ("power", "power"),
        ("root", "root"),
    ],
)
def test_validate_operation(operation, expected):
    """Test valid operation input."""
    assert validate_operation(operation) == expected


def test_validate_invalid_operation():
    """Test an unsupported operation."""
    with pytest.raises(
        ValidationError,
        match="Invalid operation: potato",
    ):
        validate_operation("potato")


@pytest.mark.parametrize(
    "value",
    [
        123,
        None,
        5.5,
    ],
)
def test_operation_must_be_string(value):
    """Test that operations must be strings."""
    with pytest.raises(
        ValidationError,
        match="Operation must be a string",
    ):
        validate_operation(value)