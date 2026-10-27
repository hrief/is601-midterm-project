import math

from app.exceptions import ValidationError
from app.operations import OperationFactory


def validate_number(value: str, max_value: float = float("inf")) -> float:
    """Validate and convert a string to a float."""
    try:
        number = float(value)
        if not math.isfinite(number) or abs(number) > max_value:
            raise ValueError("Number must be finite and within the configured maximum.")
        return number
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            f"Invalid number: {value}"
        ) from exc


def validate_operation(operation: str) -> str:
    """Validate a calculator operation."""
    if not isinstance(operation, str):
        raise ValidationError("Operation must be a string.")

    operation = operation.strip().lower()

    if operation not in OperationFactory.supported_operations():
        raise ValidationError(
            f"Invalid operation: {operation}"
        )

    return operation