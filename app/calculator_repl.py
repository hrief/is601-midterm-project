import os
import sys

from colorama import Fore, Style, init

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento, MementoCaretaker
from app.exceptions import CalculatorError, HistoryError, OperationError
from app.history import AutoSaveObserver, History, LoggingObserver
from app.input_validators import validate_number, validate_operation
from app.operations import OperationFactory


OUTPUT_COLORS = {
    "success": Fore.GREEN,
    "error": Fore.RED,
    "warning": Fore.YELLOW,
    "info": Fore.CYAN,
    "history": Fore.BLUE,
}


def print_message(message: str, kind: str = "info") -> None:
    """Color terminal output while keeping redirected output readable."""
    use_color = (
        sys.stdout.isatty()
        and os.getenv("TERM") != "dumb"
        and "NO_COLOR" not in os.environ
    )
    if use_color:
        message = f"{OUTPUT_COLORS[kind]}{message}{Style.RESET_ALL}"
    print(message)


class Calculator:
    """Facade providing a simplified interface to calculator subsystems."""

    def __init__(self, config: CalculatorConfig | None = None) -> None:
        self.config = config or CalculatorConfig.from_env()
        self.history = History(self.config.max_history, self.config.default_encoding)
        self.logging_observer = LoggingObserver(
            self.config.log_path, self.config.default_encoding,
        )
        self.history.add_observer(self.logging_observer)
        self.caretaker = MementoCaretaker()

        if self.config.auto_save:
            self.history.add_observer(
                AutoSaveObserver(self.config.history_path)
            )

        try:
            self.history.load(self.config.history_path)
        except HistoryError as exc:
            self.logging_observer.logger.error("%s", exc)
            print_message(f"Error: {exc}", "error")

    def close(self) -> None:
        """Release resources owned by the calculator."""
        self.logging_observer.close()

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
        number1 = validate_number(operand1, self.config.max_input_value)
        number2 = validate_number(operand2, self.config.max_input_value)
        operation_name = validate_operation(operation)

        calculation = Calculation.create(
            number1,
            number2,
            operation_name,
        )

        calculation.result = round(calculation.result, self.config.precision)
        self.caretaker.save(self._create_memento())
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
        self.history.save(self.config.history_path)

    def load_history(self) -> None:
        """Manually load calculator history."""
        previous = self._create_memento()
        self.history.load(self.config.history_path)
        self.caretaker.save(previous)
        self.history.restore(self.history.dataframe)

    def get_history(self):
        """Return calculation history."""
        return self.history.dataframe

    def get_operations(self) -> tuple[str, ...]:
        """Return supported calculator operations."""
        return OperationFactory.supported_operations()


def print_help() -> None:
    """Display available calculator commands."""
    print_message(
        """
Available operations:
  add
  subtract
  multiply
  divide
  power
  root
  modulus
  int_divide
  percent
  abs_diff

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
    init()
    try:
        calculator = Calculator()
    except CalculatorError as exc:
        print_message(f"Error: {exc}", "error")
        return

    print_message("Advanced Calculator")
    print_message("Type 'help' for available commands.")

    while True:
        try:
            user_input = input(">>> ").strip()

            if not user_input:
                continue

            parts = user_input.split()
            command = parts[0].lower()

            if command == "exit":
                print_message("Goodbye!", "success")
                break

            if command == "help":
                print_help()
                continue

            if command == "history":
                history = calculator.get_history()

                if history.empty:
                    print_message("No calculations in history.", "warning")
                else:
                    print_message(history.to_string(index=False), "history")
                continue

            if command == "clear":
                calculator.clear_history()
                print_message("History cleared.", "success")
                continue

            if command == "undo":
                if calculator.undo():
                    print_message("Undo successful.", "success")
                else:
                    print_message("Nothing to undo.", "warning")
                continue

            if command == "redo":
                if calculator.redo():
                    print_message("Redo successful.", "success")
                else:
                    print_message("Nothing to redo.", "warning")
                continue

            if command == "save":
                calculator.save_history()
                print_message("History saved.", "success")
                continue

            if command == "load":
                calculator.load_history()
                print_message("History loaded.", "success")
                continue

            if command in calculator.get_operations():
                if len(parts) != 3:
                    print_message(
                        "Usage: <operation> <number1> <number2>", "error"
                    )
                    continue

                result = calculator.calculate(
                    parts[1],
                    parts[2],
                    command,
                )
                print_message(f"Result: {result}", "success")
                continue

            print_message(f"Unknown command: {command}", "error")

        except (OperationError, ValueError, ZeroDivisionError, OverflowError) as exc:
            calculator.logging_observer.logger.warning("%s", exc)
            print_message(f"Error: {exc}", "error")
        except CalculatorError as exc:
            calculator.logging_observer.logger.error("%s", exc)
            print_message(f"Error: {exc}", "error")
        except (EOFError, KeyboardInterrupt):
            print_message("\nGoodbye!", "success")
            break

    calculator.close()


if __name__ == "__main__": # pragma: no cover
    run_repl()