import pytest

from app.operations import (
    Addition,
    Division,
    Multiplication,
    Operation,
    OperationFactory,
    Power,
    Root,
    Subtraction,
    Modulus,
    IntegerDivision,
    Percentage,
    AbsoluteDifference
)


@pytest.mark.parametrize(
    "operation,a,b,expected",
    [
        (Addition(), 5, 3, 8),
        (Addition(), -5, 3, -2),
        (Subtraction(), 5, 3, 2),
        (Subtraction(), 3, 5, -2),
        (Multiplication(), 5, 3, 15),
        (Multiplication(), -5, 3, -15),
        (Division(), 10, 2, 5),
        (Division(), 5, 2, 2.5),
        (Power(), 2, 3, 8),
        (Power(), 5, 0, 1),
        (Root(), 25, 2, 5),
        (Root(), 27, 3, 3),
        (Root(), -27, 3, -3),
        (Modulus(), 10, 3, 1),
        (Modulus(), 15, 4, 3),
        (IntegerDivision(), 10, 3, 3),
        (IntegerDivision(), 15, 4, 3),
        (Percentage(), 25, 200, 12.5),
        (Percentage(), 50, 200, 25.0),
        (AbsoluteDifference(), 5, 12, 7),
        (AbsoluteDifference(), 12, 5, 7),
    ],
)
def test_operations(operation, a, b, expected):
    """Test calculator arithmetic operations."""
    assert operation.execute(a, b) == pytest.approx(expected)


def test_division_by_zero():
    """Test division by zero."""
    with pytest.raises(
        ZeroDivisionError,
        match="Cannot divide by zero",
    ):
        Division().execute(10, 0)


def test_zero_degree_root():
    """Test that a zero-degree root is rejected."""
    with pytest.raises(
        ValueError,
        match="Root degree cannot be zero",
    ):
        Root().execute(25, 0)


@pytest.mark.parametrize(
    "number,degree",
    [
        (-16, 2),
        (-16, 2.5),
    ],
)
def test_invalid_negative_roots(number, degree):
    """Test invalid roots of negative numbers."""
    with pytest.raises(ValueError):
        Root().execute(number, degree)


@pytest.mark.parametrize(
    "name,expected_type",
    [
        ("add", Addition),
        ("subtract", Subtraction),
        ("multiply", Multiplication),
        ("divide", Division),
        ("power", Power),
        ("root", Root),
        ("ADD", Addition),
        ("SUBTRACT", Subtraction),
        ("MULTIPLY", Multiplication),
        ("DIVIDE", Division),
        ("POWER", Power),
        ("ROOT", Root),
        ("modulus", Modulus),
        ("int_divide", IntegerDivision),
        ("percent", Percentage),
        ("abs_diff", AbsoluteDifference)
    ],
)
def test_operation_factory(name, expected_type):
    """Test operation creation through the factory."""
    operation = OperationFactory.create_operation(name)
    assert isinstance(operation, expected_type)


def test_invalid_factory_operation():
    """Test requesting an unsupported operation."""
    with pytest.raises(
        ValueError,
        match="Unknown operation: potato",
    ):
        OperationFactory.create_operation("potato")


def test_supported_operations():
    """Test the supported operation names."""
    assert OperationFactory.supported_operations() == (
        "add",
        "subtract",
        "multiply",
        "divide",
        "power",
        "root",
        "modulus",
        "int_divide",
        "percent",
        "abs_diff"
    )


def test_abstract_operation():
    """Test that Operation cannot be instantiated."""
    with pytest.raises(TypeError):
        Operation()
@pytest.mark.parametrize(
    "operation",
    [
        Modulus(),
        IntegerDivision(),
        Percentage(),
    ],
)
def test_division_by_zero_operations(operation):
    """Test division by zero for operations that involve division."""
    with pytest.raises(
        ZeroDivisionError,
        match="Cannot",
    ):
        operation.execute(10, 0)