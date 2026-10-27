from abc import ABC, abstractmethod
import math


class Operation(ABC):
    """Abstract strategy for calculator operations."""

    @abstractmethod
    def execute(self, a: float, b: float) -> float:
        """Execute the operation."""
        raise NotImplementedError # pragma: no cover


class Addition(Operation):
    def execute(self, a: float, b: float) -> float:
        return a + b


class Subtraction(Operation):
    def execute(self, a: float, b: float) -> float:
        return a - b


class Multiplication(Operation):
    def execute(self, a: float, b: float) -> float:
        return a * b


class Division(Operation):
    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        return a / b


class Power(Operation):
    def execute(self, a: float, b: float) -> float:
        return a ** b


class Root(Operation):
    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Root degree cannot be zero.")

        if a < 0:
            if not float(b).is_integer() or int(b) % 2 == 0:
                raise ValueError(
                    "Cannot calculate an even or non-integer root "
                    "of a negative number."
                )
            return -((-a) ** (1 / b))

        return a ** (1 / b)


class Modulus(Operation):
    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise ZeroDivisionError("Cannot calculate modulus by zero.")
        return a % b


class IntegerDivision(Operation):
    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        return a // b


class Percentage(Operation):
    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise ZeroDivisionError("Cannot calculate percentage with a zero denominator.")
        return (a / b) * 100


class AbsoluteDifference(Operation):
    def execute(self, a: float, b: float) -> float:
        return abs(a - b)


class OperationFactory:
    """Factory responsible for creating operation strategies."""

    _operations = {
        "add": Addition,
        "subtract": Subtraction,
        "multiply": Multiplication,
        "divide": Division,
        "power": Power,
        "root": Root,
        "modulus": Modulus,
        "int_divide": IntegerDivision,
        "percent": Percentage,
        "abs_diff": AbsoluteDifference,
    }

    @classmethod
    def supported_operations(cls) -> tuple[str, ...]:
        """Return the names of supported operations."""
        return tuple(cls._operations.keys())

    @classmethod
    def create_operation(cls, operation_name: str) -> Operation:
        """Create an operation based on its name."""
        try:
            operation_class = cls._operations[operation_name.lower()]
            return operation_class()
        except KeyError as exc:
            raise ValueError(
                f"Unknown operation: {operation_name}"
            ) from exc