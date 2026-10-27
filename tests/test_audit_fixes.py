"""Regression tests for final assignment-criteria audit findings."""
from unittest.mock import Mock

import pandas as pd
import pytest

from app.calculation import Calculation
from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app import calculator_repl as repl
from app.exceptions import DivisionByZeroError, OperationError
from app.history import History
from app.logger import Logger


@pytest.fixture
def calculator(tmp_path):
    instance = Calculator(CalculatorConfig(
        history_file=str(tmp_path / "history.csv"),
        auto_save=True, max_history=100, log_dir=str(tmp_path),
    ))
    yield instance
    instance.close()


@pytest.mark.parametrize("first,second,operation", [
    ("-1", "0.5", "power"),
    ("1e100", "1e-300", "divide"),
    ("1e100", "1e-300", "percent"),
    ("1e100", "1e100", "power"),
    ("0", "-1", "power"),
])
def test_invalid_result_preserves_history_and_redo(
    calculator, first, second, operation,
):
    calculator.calculate("2", "3", "add")
    calculator.calculate("4", "5", "add")
    calculator.undo()
    previous = calculator.get_history()
    path = calculator.config.history_path
    with open(path, encoding="utf-8") as stream:
        saved = stream.read()
    with pytest.raises(OperationError):
        calculator.calculate(first, second, operation)
    pd.testing.assert_frame_equal(previous, calculator.get_history())
    with open(path, encoding="utf-8") as stream:
        assert stream.read() == saved
    loaded = History()
    loaded.load(path)
    assert loaded.dataframe.iloc[0]["result"] == 5
    assert calculator.redo()
    assert list(calculator.get_history()["result"]) == [5, 9]


@pytest.mark.parametrize("first,second,expected", [
    (2, -3, 0.125), (-2, -3, -0.125), (4, -0.5, 0.5),
])
def test_negative_exponents(calculator, first, second, expected):
    assert Calculation.create(first, second, "power").result == pytest.approx(expected)
    assert calculator.calculate(str(first), str(second), "power") == pytest.approx(expected)
    calculator.load_history()
    assert calculator.get_history().iloc[0]["result"] == pytest.approx(expected)


@pytest.mark.parametrize("first,second,expected", [
    (-10, 3, -4), (10, -3, -4), (-10, -3, 3), (10, 3, 3),
])
def test_integer_division_uses_python_floor_convention(
    calculator, first, second, expected,
):
    assert calculator.calculate(str(first), str(second), "int_divide") == expected


def test_custom_operation_exceptions_preserve_builtin_compatibility():
    with pytest.raises(DivisionByZeroError) as caught:
        Calculation.create(1, 0, "divide")
    assert isinstance(caught.value, OperationError)
    assert isinstance(caught.value, ZeroDivisionError)
    with pytest.raises(OperationError) as caught:
        Calculation.create(-4, 2, "root")
    assert isinstance(caught.value, ValueError)


def test_deserialization_preserves_saved_result_without_execution(monkeypatch, tmp_path):
    data = {
        "operand1": 1, "operand2": 3, "operation": "divide",
        "result": 0.33, "timestamp": "2026-10-27T12:00:00+00:00",
    }
    execute = Mock(side_effect=AssertionError("Saved calculations must not execute again"))
    monkeypatch.setattr("app.calculation.OperationFactory.create_operation", execute)
    calculation = Calculation.from_dict(data)
    assert calculation.to_dict() == data
    path = tmp_path / "history.csv"
    pd.DataFrame([data]).to_csv(path, index=False)
    history = History()
    history.load(str(path))
    loaded = history.calculations
    assert len(loaded) == 1
    assert isinstance(loaded[0], Calculation)
    assert loaded[0].to_dict() == data
    loaded[0].result = 999
    assert history.calculations[0].result == 0.33
    execute.assert_not_called()


def test_legacy_calculation_reconstruction():
    calculation = Calculation.from_dict({
        "operand1": 2, "operand2": 3, "operation": "add", "result": 5,
    })
    assert calculation.timestamp == ""
    assert calculation.result == 5


@pytest.mark.parametrize("setting,value,expected", [
    ("CALCULATOR_PRECISION", "-1", "CALCULATOR_PRECISION"),
    ("CALCULATOR_MAX_INPUT_VALUE", "nan", "CALCULATOR_MAX_INPUT_VALUE"),
    ("CALCULATOR_AUTO_SAVE", "maybe", "CALCULATOR_AUTO_SAVE"),
    ("CALCULATOR_LOG_DIR", None, "Cannot open calculation log"),
])
def test_startup_errors_are_readable(
    monkeypatch, tmp_path, capsys, setting, value, expected,
):
    monkeypatch.setattr("app.calculator_config.load_dotenv", lambda: None)
    for key in (
        "PRECISION", "MAX_INPUT_VALUE", "AUTO_SAVE", "MAX_HISTORY",
        "MAX_HISTORY_SIZE", "LOG_FILE", "DEFAULT_ENCODING",
    ):
        monkeypatch.delenv("CALCULATOR_" + key, raising=False)
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("CALCULATOR_HISTORY_FILE", str(tmp_path / "history.csv"))
    if value is None:
        blocker = tmp_path / "not-a-directory"
        blocker.write_text("Existing file")
        value = str(blocker)
    monkeypatch.setenv(setting, value)
    read_input = Mock(side_effect=AssertionError("Startup should not enter the REPL"))
    monkeypatch.setattr("builtins.input", read_input)
    repl.run_repl()
    output = capsys.readouterr()
    assert "Error:" in output.out
    assert expected in output.out
    assert "Traceback" not in output.out + output.err
    read_input.assert_not_called()


def test_repl_recovers_after_complex_and_nonfinite_results(
    monkeypatch, calculator, capsys,
):
    monkeypatch.setattr(repl, "Calculator", lambda: calculator)
    commands = iter([
        "power -1 0.5", "divide 1e100 1e-300",
        "power 1e100 1e100", "add 2 3", "exit",
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(commands))
    repl.run_repl()
    output = capsys.readouterr().out
    assert output.count("Error: Calculation result must be a finite real number.") == 2
    assert "Error:" in output
    assert "Result: 5.0" in output
    assert "Goodbye!" in output
    assert len(calculator.history) == 1
    history = History()
    history.load(calculator.config.history_path)
    assert history.calculations[0].result == 5


def test_logger_owns_and_releases_file_handler(tmp_path):
    path = tmp_path / "nested" / "audit.log"
    logger = Logger(str(path))
    logger.info("information")
    logger.warning("warning")
    logger.error("error")
    logger.close()
    logger.close()
    output = path.read_text()
    for level, message in (("INFO", "information"), ("WARNING", "warning"), ("ERROR", "error")):
        assert f"{level} {message}" in output
    assert logger.handlers == []


@pytest.mark.parametrize("operation", [
    "add", "subtract", "multiply", "divide", "power",
    "root", "modulus", "int_divide", "percent", "abs_diff",
])
def test_every_operation_uses_logger(calculator, operation):
    assert isinstance(calculator.logging_observer.logger, Logger)
    calculator.calculate("8", "2", operation)
    with open(calculator.config.log_path, encoding="utf-8") as stream:
        output = stream.read()
    assert f"INFO Calculation operation={operation}" in output
    assert "operand1=8.0 operand2=2.0 result=" in output
    assert calculator.get_history().iloc[0]["timestamp"] in output
