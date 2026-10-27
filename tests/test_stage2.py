"""Stage 2 configuration, persistence, and state regression tests."""
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_repl import Calculator, run_repl
from app.exceptions import ConfigurationError, HistoryError, ValidationError
from app.history import History, LoggingObserver


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    for key in (
        "LOG_DIR", "HISTORY_DIR", "LOG_FILE", "HISTORY_FILE",
        "MAX_HISTORY", "MAX_HISTORY_SIZE", "AUTO_SAVE", "PRECISION",
        "MAX_INPUT_VALUE", "DEFAULT_ENCODING",
    ):
        monkeypatch.delenv("CALCULATOR_" + key, raising=False)
    monkeypatch.setattr("app.calculator_config.load_dotenv", lambda: None)


@pytest.fixture
def calculator(tmp_path):
    instance = Calculator(CalculatorConfig(
        history_file=str(tmp_path / "history.csv"),
        auto_save=True, max_history=2, log_dir=str(tmp_path / "logs"),
        precision=2, max_input_value=100,
    ))
    yield instance
    instance.close()


def test_timestamp_round_trip_and_bounded_mementos(calculator):
    before = datetime.now(timezone.utc)
    calculator.calculate("1", "3", "divide")
    first = calculator.get_history().iloc[0]
    assert before <= datetime.fromisoformat(first["timestamp"]) <= datetime.now(timezone.utc)
    assert first["result"] == 0.33
    calculator.calculate("2", "3", "add")
    previous = calculator.get_history()
    calculator.calculate("3", "3", "multiply")
    bounded = calculator.get_history()
    assert list(bounded["result"]) == [5, 9]
    assert calculator.undo()
    pd.testing.assert_frame_equal(calculator.get_history(), previous)
    assert calculator.redo()
    pd.testing.assert_frame_equal(calculator.get_history(), bounded)
    saved = History()
    saved.load(calculator.config.history_path)
    assert list(saved.dataframe["timestamp"]) == list(bounded["timestamp"])
    assert list(saved.dataframe["result"]) == [5, 9]


def test_failed_calculation_preserves_redo(calculator):
    calculator.calculate("1", "2", "add")
    calculator.undo()
    with pytest.raises(ZeroDivisionError):
        calculator.calculate("1", "0", "divide")
    assert calculator.redo()
    assert len(calculator.history) == 1


@pytest.mark.parametrize("value", ["101", "-101", "nan", "inf", "-inf"])
def test_input_bounds(calculator, value):
    with pytest.raises(ValidationError):
        calculator.calculate(value, "1", "add")
    assert not calculator.caretaker.can_undo


def test_successful_load_is_undoable(calculator):
    calculator.calculate("1", "2", "add")
    calculator.save_history()
    calculator.history.clear()
    # clear auto-saves; write a separate valid persisted state.
    frame = pd.DataFrame([Calculation.create(3, 4, "add").to_dict()])
    frame.to_csv(calculator.config.history_path, index=False)
    calculator.load_history()
    assert len(calculator.history) == 1
    assert calculator.undo()
    assert calculator.history.dataframe.empty
    assert calculator.redo()
    assert calculator.get_history().iloc[0]["timestamp"] == frame.iloc[0]["timestamp"]


@pytest.mark.parametrize("key,value", [
    ("LOG_DIR", " "), ("HISTORY_DIR", ""), ("LOG_FILE", ""),
    ("DEFAULT_ENCODING", ""), ("DEFAULT_ENCODING", "unknown-codec"),
    ("PRECISION", "no"), ("PRECISION", "-1"), ("PRECISION", "16"),
    ("MAX_INPUT_VALUE", "no"), ("MAX_INPUT_VALUE", "0"),
    ("MAX_INPUT_VALUE", "nan"), ("MAX_INPUT_VALUE", "inf"),
    ("MAX_HISTORY_SIZE", "no"), ("MAX_HISTORY_SIZE", "0"),
])
def test_invalid_configuration(monkeypatch, key, value):
    monkeypatch.setenv("CALCULATOR_" + key, value)
    with pytest.raises(ConfigurationError, match="CALCULATOR_" + key):
        CalculatorConfig.from_env()


def test_configuration_defaults_and_paths(monkeypatch, tmp_path):
    config = CalculatorConfig.from_env()
    assert config.history_path == str(Path("data") / "history.csv")
    assert config.log_path == str(Path("logs") / "calculator.log")
    assert (config.precision, config.max_input_value, config.default_encoding) == (10, 1e100, "utf-8")
    for key, value in {
        "LOG_DIR": str(tmp_path), "HISTORY_DIR": str(tmp_path),
        "LOG_FILE": "audit.log", "HISTORY_FILE": "calculations.csv",
        "MAX_HISTORY_SIZE": "3", "MAX_HISTORY": "999",
        "AUTO_SAVE": "false", "PRECISION": "0",
        "MAX_INPUT_VALUE": "50", "DEFAULT_ENCODING": "utf-16",
    }.items():
        monkeypatch.setenv("CALCULATOR_" + key, value)
    config = CalculatorConfig.from_env()
    assert config.max_history == 3
    assert config.precision == 0
    assert config.history_path == str(tmp_path / "calculations.csv")
    assert config.log_path == str(tmp_path / "audit.log")
    assert not config.auto_save
    assert config.max_input_value == 50
    history = History(3, config.default_encoding)
    history.add(Calculation.create(1, 2, "add"))
    history.save(config.history_path)
    history.load(config.history_path)
    assert len(history) == 1


@pytest.mark.parametrize("content", [
    "", "wrong,columns\n1,2\n",
    'operand1,operand2,operation,result\n"unterminated',
    "operand1,operand2,operation,result\nx,2,add,3\n",
    "operand1,operand2,operation,result\ninf,2,add,3\n",
    "operand1,operand2,operation,result\n1,2,unknown,3\n",
    "operand1,operand2,operation,result,timestamp\n1,2,add,3,bad-date\n",
])
def test_invalid_csv_preserves_state(tmp_path, content):
    path = tmp_path / "bad.csv"
    path.write_text(content)
    history = History()
    history.add(Calculation.create(1, 2, "add"))
    previous = history.dataframe
    with pytest.raises(HistoryError, match="Cannot load history"):
        history.load(str(path))
    pd.testing.assert_frame_equal(history.dataframe, previous)


def test_permission_errors(tmp_path, monkeypatch):
    history = History()
    def denied(*args, **kwargs):
        raise PermissionError("Permission denied")
    monkeypatch.setattr(pd.DataFrame, "to_csv", denied)
    with pytest.raises(HistoryError, match="Cannot save history.*Permission denied"):
        history.save(str(tmp_path / "history.csv"))
    monkeypatch.setattr(pd, "read_csv", denied)
    with pytest.raises(HistoryError, match="Cannot load history.*Permission denied"):
        history.load(str(tmp_path / "history.csv"))
    monkeypatch.setattr("app.history.logging.FileHandler", denied)
    with pytest.raises(HistoryError, match="Cannot open calculation log"):
        LoggingObserver(str(tmp_path / "audit.log"))


def test_load_limit_and_legacy_timestamps(tmp_path):
    path = tmp_path / "legacy.csv"
    pd.DataFrame([Calculation.create(i, 1, "add").to_dict() for i in range(5)]).drop(
        columns="timestamp",
    ).to_csv(path, index=False)
    history = History(2)
    history.load(str(path))
    assert list(history.dataframe["result"]) == [4, 5]
    assert list(history.dataframe["timestamp"]) == ["", ""]
    history.save(str(path))
    history.load(str(path))
    assert list(history.dataframe["timestamp"]) == ["", ""]


def test_empty_history_round_trip(tmp_path):
    path = str(tmp_path / "empty.csv")
    history = History()
    history.save(path)
    history.load(path)
    assert history.dataframe.empty
    assert list(history.dataframe.columns) == History.COLUMNS


def test_log_details(calculator):
    calculator.calculate("2", "3", "add")
    output = Path(calculator.config.log_path).read_text()
    assert "INFO Calculation operation=add operand1=2.0 operand2=3.0 result=5.0 timestamp=" in output
    assert calculator.get_history().iloc[0]["timestamp"] in output


def test_repl_recovers_from_csv_errors(monkeypatch, tmp_path, capsys):
    history_path = tmp_path / "bad.csv"
    history_path.write_text("invalid")
    monkeypatch.setenv("CALCULATOR_HISTORY_FILE", str(history_path))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", "false")
    commands = iter(["load", "divide 1 0", "add 1 2", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(commands))
    run_repl()
    output = capsys.readouterr().out
    assert output.count("Cannot load history") == 2
    assert "Result: 3.0" in output
    assert "Goodbye!" in output
    log = (tmp_path / "calculator.log").read_text()
    assert "ERROR Cannot load history" in log
    assert "WARNING Cannot divide by zero" in log


def test_failed_load_keeps_undo_state(calculator):
    calculator.calculate("1", "2", "add")
    previous = calculator.get_history()
    Path(calculator.config.history_path).write_text("broken")
    with pytest.raises(HistoryError):
        calculator.load_history()
    pd.testing.assert_frame_equal(calculator.get_history(), previous)
    assert calculator.undo()
    assert calculator.get_history().empty


def test_new_calculation_clears_redo(calculator):
    calculator.calculate("1", "2", "add")
    calculator.undo()
    calculator.calculate("3", "4", "add")
    assert not calculator.redo()


def test_autosave_failure_remains_undoable(calculator, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("read-only history")
    monkeypatch.setattr(pd.DataFrame, "to_csv", denied)
    with pytest.raises(HistoryError, match="read-only history"):
        calculator.calculate("1", "2", "add")
    assert len(calculator.history) == 1
    assert calculator.caretaker.can_undo
    # Removing the failed autosaver allows recovery through the same memento.
    calculator.history.remove_observer(calculator.history._observers[-1])
    assert calculator.undo()
    assert calculator.history.dataframe.empty


def test_repl_recovers_from_save_permission_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("CALCULATOR_HISTORY_FILE", str(tmp_path / "history.csv"))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path))
    def denied(*args, **kwargs):
        raise PermissionError("read-only history")
    monkeypatch.setattr(pd.DataFrame, "to_csv", denied)
    commands = iter(["add 1 2", "history", "save", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(commands))
    run_repl()
    output = capsys.readouterr().out
    assert output.count("Cannot save history") == 2
    assert "add" in output
    assert "Goodbye!" in output
