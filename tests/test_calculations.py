import pytest

from app.calculation import Calculation


@pytest.mark.parametrize(
    "operand1,operand2,operation,expected",
    [
        (5, 3, "add", 8),
        (5, 3, "subtract", 2),
        (5, 3, "multiply", 15),
        (10, 2, "divide", 5),
        (2, 3, "power", 8),
        (25, 2, "root", 5),
    ],
)
def test_create_calculation(
    operand1,
    operand2,
    operation,
    expected,
):
    """Test creating calculations with different operations."""
    calculation = Calculation.create(
        operand1,
        operand2,
        operation,
    )

    assert calculation.operand1 == operand1
    assert calculation.operand2 == operand2
    assert calculation.operation_name == operation
    assert calculation.result == pytest.approx(expected)


def test_operation_name_normalized():
    """Test that operation names are normalized to lowercase."""
    calculation = Calculation.create(5, 3, "ADD")

    assert calculation.operation_name == "add"
    assert calculation.result == 8


def test_calculation_to_dict():
    """Test converting a calculation to a dictionary."""
    calculation = Calculation.create(10, 5, "add")

    assert calculation.to_dict() == {
        "operand1": 10,
        "operand2": 5,
        "operation": "add",
        "result": 15,
    }


def test_calculation_invalid_operation():
    """Test an invalid calculation operation."""
    with pytest.raises(
        ValueError,
        match="Unknown operation: potato",
    ):
        Calculation.create(5, 3, "potato")


def test_calculation_division_by_zero():
    """Test division by zero through Calculation."""
    with pytest.raises(
        ZeroDivisionError,
        match="Cannot divide by zero",
    ):
        Calculation.create(10, 0, "divide")