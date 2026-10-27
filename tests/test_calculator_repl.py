import pandas as pd
import pytest

from app.calculator_config import CalculatorConfig
from app.calculator_repl import Calculator, print_help, run_repl


@pytest.fixture
def config(tmp_path):
    """Create isolated calculator configuration."""
    return CalculatorConfig(
        history_file=str(tmp_path / "history.csv"),
        auto_save=True,
        max_history=100,
    )


@pytest.fixture
def calculator(config):
    """Create an isolated calculator."""
    return Calculator(config)


@pytest.mark.parametrize(
    "a,b,operation,expected",
    [
        ("5", "3", "add", 8),
        ("5", "3", "subtract", 2),
        ("5", "3", "multiply", 15),
        ("10", "2", "divide", 5),
        ("2", "8", "power", 256),
        ("25", "2", "root", 5),
        ("10", "3", "modulus", 1),
        ("10", "3", "int_divide", 3),
        ("25", "200", "percent", 12.5),
        ("5", "12", "abs_diff", 7),
    ],
)
def test_calculator_operations(calculator, a, b, operation, expected):
    """Test calculations through the facade."""
    result = calculator.calculate(a, b, operation)

    assert result == pytest.approx(expected)
    assert len(calculator.history) == 1


def test_calculator_without_autosave(tmp_path):
    """Test calculator when auto-save is disabled."""
    config = CalculatorConfig(
        history_file=str(tmp_path / "history.csv"),
        auto_save=False,
        max_history=100,
    )

    calculator = Calculator(config)

    assert len(calculator.history) == 0


def test_calculator_loads_existing_history(tmp_path):
    """Test loading history during initialization."""
    file_path = tmp_path / "history.csv"

    dataframe = pd.DataFrame(
        [
            {
                "operand1": 5,
                "operand2": 3,
                "operation": "add",
                "result": 8,
            }
        ]
    )
    dataframe.to_csv(file_path, index=False)

    config = CalculatorConfig(
        history_file=str(file_path),
        auto_save=False,
        max_history=100,
    )

    calculator = Calculator(config)

    assert len(calculator.history) == 1


def test_clear_history(calculator):
    """Test clearing history through the facade."""
    calculator.calculate("5", "3", "add")

    calculator.clear_history()

    assert calculator.get_history().empty


def test_undo(calculator):
    """Test undo through the facade."""
    calculator.calculate("5", "3", "add")
    calculator.calculate("10", "2", "divide")

    assert len(calculator.history) == 2

    assert calculator.undo() is True
    assert len(calculator.history) == 1


def test_undo_when_unavailable(calculator):
    """Test undo with no saved states."""
    assert calculator.undo() is False


def test_redo(calculator):
    """Test redo through the facade."""
    calculator.calculate("5", "3", "add")

    assert calculator.undo() is True
    assert calculator.redo() is True
    assert len(calculator.history) == 1


def test_redo_when_unavailable(calculator):
    """Test redo with no undone state."""
    assert calculator.redo() is False


def test_save_and_load_history(tmp_path):
    """Test manual save and load."""
    config = CalculatorConfig(
        history_file=str(tmp_path / "history.csv"),
        auto_save=False,
        max_history=100,
    )

    calculator = Calculator(config)

    calculator.calculate("5", "3", "add")
    calculator.save_history()

    calculator.clear_history()
    assert calculator.get_history().empty

    calculator.load_history()

    assert len(calculator.history) == 1
    assert calculator.get_history().iloc[0]["result"] == 8


def test_get_operations(calculator):
    """Test retrieving supported operations."""
    assert calculator.get_operations() == (
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


def test_invalid_number(calculator):
    """Test invalid numeric input."""
    with pytest.raises(Exception):
        calculator.calculate("potato", "3", "add")


def test_division_by_zero(calculator):
    """Test division by zero."""
    with pytest.raises(ZeroDivisionError):
        calculator.calculate("10", "0", "divide")


def test_print_help(capsys):
    """Test help output."""
    print_help()

    output = capsys.readouterr().out

    assert "Available operations:" in output
    assert "add" in output
    assert "history" in output
    assert "undo" in output
    assert "redo" in output
    assert "exit" in output

def test_repl_exit(monkeypatch, tmp_path, capsys):
    """Test exiting the REPL."""
    monkeypatch.setenv(
        "CALCULATOR_HISTORY_FILE",
        str(tmp_path / "history.csv"),
    )

    inputs = iter(["exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_repl()

    output = capsys.readouterr().out

    assert "Advanced Calculator" in output
    assert "Goodbye!" in output


def test_repl_calculation_and_history(monkeypatch, tmp_path, capsys):
    """Test calculation and history commands."""
    monkeypatch.setenv(
        "CALCULATOR_HISTORY_FILE",
        str(tmp_path / "history.csv"),
    )

    inputs = iter(
        [
            "add 5 3",
            "history",
            "exit",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_repl()

    output = capsys.readouterr().out

    assert "Result: 8.0" in output
    assert "add" in output
    assert "Goodbye!" in output


def test_repl_commands(monkeypatch, tmp_path, capsys):
    """Test standard REPL commands."""
    monkeypatch.setenv(
        "CALCULATOR_HISTORY_FILE",
        str(tmp_path / "history.csv"),
    )

    inputs = iter(
        [
            "",
            "help",
            "history",
            "add 5 3",
            "save",
            "clear",
            "undo",
            "redo",
            "load",
            "exit",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_repl()

    output = capsys.readouterr().out

    assert "Available operations:" in output
    assert "No calculations in history." in output
    assert "Result: 8.0" in output
    assert "History saved." in output
    assert "History cleared." in output
    assert "Undo successful." in output
    assert "Redo successful." in output
    assert "History loaded." in output


def test_repl_empty_undo_redo(monkeypatch, tmp_path, capsys):
    """Test unavailable undo and redo commands."""
    monkeypatch.setenv(
        "CALCULATOR_HISTORY_FILE",
        str(tmp_path / "history.csv"),
    )

    inputs = iter(
        [
            "undo",
            "redo",
            "exit",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_repl()

    output = capsys.readouterr().out

    assert "Nothing to undo." in output
    assert "Nothing to redo." in output


def test_repl_invalid_input(monkeypatch, tmp_path, capsys):
    """Test invalid REPL inputs."""
    monkeypatch.setenv(
        "CALCULATOR_HISTORY_FILE",
        str(tmp_path / "history.csv"),
    )

    inputs = iter(
        [
            "potato",
            "add 5",
            "add potato 3",
            "divide 10 0",
            "exit",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_repl()

    output = capsys.readouterr().out

    assert "Unknown command: potato" in output
    assert "Usage: <operation> <number1> <number2>" in output
    assert "Error: Invalid number: potato" in output
    assert "Error: Cannot divide by zero." in output


def test_repl_keyboard_interrupt(monkeypatch, tmp_path, capsys):
    """Test graceful handling of Ctrl+C."""
    monkeypatch.setenv(
        "CALCULATOR_HISTORY_FILE",
        str(tmp_path / "history.csv"),
    )

    def interrupt(_):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", interrupt)

    run_repl()

    output = capsys.readouterr().out

    assert "Goodbye!" in output


def test_repl_eof(monkeypatch, tmp_path, capsys):
    """Test graceful handling of EOF."""
    monkeypatch.setenv(
        "CALCULATOR_HISTORY_FILE",
        str(tmp_path / "history.csv"),
    )

    def eof(_):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)

    run_repl()

    output = capsys.readouterr().out

    assert "Goodbye!" in output