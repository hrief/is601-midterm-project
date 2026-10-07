from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento, MementoCaretaker
from app.exceptions import CalculatorError
from app.history import AutoSaveObserver, History
from app.input_validators import validate_number, validate_operation
from app.operations import OperationFactory


class Calculator:
    """Facade providing a simplified interface to calculator subsystems."""

    def __init__(self, config: CalculatorConfig | None = None) -> None:
        self.config = config or CalculatorConfig.from_env()
        self.history = History()
        self.caretaker = MementoCaretaker()

        if self.config.auto_save:
            self.history.add_observer(
                AutoSaveObserver(self.config.history_file)
            )

        self.history.load(self.config.history_file)

    def _create_memento(self) -> CalculatorMemento:
        """Create a snapshot of the current calculator state."""
        return CalculatorMemento(self.history.dataframe)

    def _restore_memento(self, memento: CalculatorMemento) -> None:
        """Restore calculator history from a memento."""
        self.history.restore(memento.get_state())

    def calculate(
        self,
        operand1: str,
        operand2: str,
        operation: str,
    ) -> float:
        """Validate input, perform a calculation, and store it."""
        number1 = validate_number(operand1)
        number2 = validate_number(operand2)
        operation_name = validate_operation(operation)

        self.caretaker.save(self._create_memento())

        calculation = Calculation.create(
            number1,
            number2,
            operation_name,
        )

        self.history.add(calculation)
        return calculation.result

    def clear_history(self) -> None:
        """Clear calculator history while preserving undo state."""
        self.caretaker.save(self._create_memento())
        self.history.clear()

    def undo(self) -> bool:
        """Restore the previous calculator state."""
        memento = self.caretaker.undo(self._create_memento())

        if memento is None:
            return False

        self._restore_memento(memento)
        return True

    def redo(self) -> bool:
        """Restore the most recently undone calculator state."""
        memento = self.caretaker.redo(self._create_memento())

        if memento is None:
            return False

        self._restore_memento(memento)
        return True

    def save_history(self) -> None:
        """Manually save calculator history."""
        self.history.save(self.config.history_file)

    def load_history(self) -> None:
        """Manually load calculator history."""
        self.history.load(self.config.history_file)

    def get_history(self):
        """Return calculation history."""
        return self.history.dataframe

    def get_operations(self) -> tuple[str, ...]:
        """Return supported calculator operations."""
        return OperationFactory.supported_operations()


def print_help() -> None:
    """Display available calculator commands."""
    print(
        """
Available operations:
  add
  subtract
  multiply
  divide
  power
  root

Commands:
  help     Show this help message
  history  Show calculation history
  clear    Clear calculation history
  undo     Undo the last history change
  redo     Redo the last undone change
  save     Save history to disk
  load     Load history from disk
  exit     Exit the calculator

Calculation format:
  <operation> <number1> <number2>

Examples:
  add 5 3
  divide 10 2
  power 2 8
  root 25 2
"""
    )


def run_repl() -> None:
    """Run the calculator Read-Eval-Print Loop."""
    calculator = Calculator()

    print("Advanced Calculator")
    print("Type 'help' for available commands.")

    while True:
        try:
            user_input = input(">>> ").strip()

            if not user_input:
                continue

            parts = user_input.split()
            command = parts[0].lower()

            if command == "exit":
                print("Goodbye!")
                break

            if command == "help":
                print_help()
                continue

            if command == "history":
                history = calculator.get_history()

                if history.empty:
                    print("No calculations in history.")
                else:
                    print(history.to_string(index=False))
                continue

            if command == "clear":
                calculator.clear_history()
                print("History cleared.")
                continue

            if command == "undo":
                if calculator.undo():
                    print("Undo successful.")
                else:
                    print("Nothing to undo.")
                continue

            if command == "redo":
                if calculator.redo():
                    print("Redo successful.")
                else:
                    print("Nothing to redo.")
                continue

            if command == "save":
                calculator.save_history()
                print("History saved.")
                continue

            if command == "load":
                calculator.load_history()
                print("History loaded.")
                continue

            if command in calculator.get_operations():
                if len(parts) != 3:
                    print(
                        "Usage: <operation> <number1> <number2>"
                    )
                    continue

                result = calculator.calculate(
                    parts[1],
                    parts[2],
                    command,
                )
                print(f"Result: {result}")
                continue

            print(f"Unknown command: {command}")

        except CalculatorError as exc:
            print(f"Error: {exc}")
        except (ValueError, ZeroDivisionError) as exc:
            print(f"Error: {exc}")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break


if __name__ == "__main__": # pragma: no cover
    run_repl()