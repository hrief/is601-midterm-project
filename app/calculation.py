from dataclasses import dataclass, field
from datetime import datetime, timezone

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
        result = operation.execute(operand1, operand2)

        return cls(
            operand1=operand1,
            operand2=operand2,
            operation_name=operation_name.lower(),
            result=result,
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