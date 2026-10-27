import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.exceptions import DivisionByZeroError, OperationError
from app.operations import Operation, OperationFactory


@dataclass
class Calculation:
    """Represents a single calculator calculation."""

    operand1: float
    operand2: float
    operation_name: str
    result: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        operand1: float,
        operand2: float,
        operation_name: str,
    ) -> "Calculation":
        """Create and execute a calculation."""
        operation: Operation = OperationFactory.create_operation(operation_name)
        try:
            result = operation.execute(operand1, operand2)
            finite_real = not isinstance(result, complex) and math.isfinite(result)
        except ZeroDivisionError as exc:
            raise DivisionByZeroError(str(exc)) from exc
        except (ValueError, OverflowError) as exc:
            raise OperationError(str(exc)) from exc
        if not finite_real:
            raise OperationError("Calculation result must be a finite real number.")

        return cls(
            operand1=operand1,
            operand2=operand2,
            operation_name=operation_name.lower(),
            result=result,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Calculation":
        """Reconstruct a saved calculation without recomputing its result."""
        return cls(
            operand1=data["operand1"],
            operand2=data["operand2"],
            operation_name=data["operation"],
            result=data["result"],
            timestamp=data.get("timestamp", ""),
        )

    def to_dict(self) -> dict:
        """Convert the calculation to a dictionary for storage."""
        return {
            "operand1": self.operand1,
            "operand2": self.operand2,
            "operation": self.operation_name,
            "result": self.result,
            "timestamp": self.timestamp,
        }