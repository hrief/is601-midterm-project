import pandas as pd
import pytest

from app.calculation import Calculation
from app.history import (
    AutoSaveObserver,
    History,
    HistoryObserver,
    LoggingObserver,
)


def test_new_history_is_empty():
    """Test that a new history is empty."""
    history = History()

    assert len(history) == 0
    assert history.dataframe.empty
    assert list(history.dataframe.columns) == History.COLUMNS


def test_add_calculation():
    """Test adding a calculation to history."""
    history = History()
    calculation = Calculation.create(5, 3, "add")

    history.add(calculation)

    assert len(history) == 1

    row = history.dataframe.iloc[0]

    assert row["operand1"] == 5
    assert row["operand2"] == 3
    assert row["operation"] == "add"
    assert row["result"] == 8


@pytest.mark.parametrize(
    "a,b,operation,expected",
    [
        (5, 3, "add", 8),
        (10, 4, "subtract", 6),
        (3, 4, "multiply", 12),
    ],
)
def test_multiple_history_entries(a, b, operation, expected):
    """Test different calculations stored in history."""
    history = History()

    history.add(Calculation.create(a, b, operation))

    row = history.dataframe.iloc[0]
    assert row["result"] == expected


def test_dataframe_returns_copy():
    """Test that dataframe does not expose internal history."""
    history = History()
    history.add(Calculation.create(5, 3, "add"))

    dataframe = history.dataframe
    dataframe.loc[0, "result"] = 999

    assert history.dataframe.loc[0, "result"] == 8


def test_clear_history():
    """Test clearing calculation history."""
    history = History()
    history.add(Calculation.create(5, 3, "add"))

    history.clear()

    assert len(history) == 0
    assert history.dataframe.empty


def test_save_and_load_history(tmp_path):
    """Test saving and loading history from CSV."""
    file_path = tmp_path / "history.csv"

    history = History()
    history.add(Calculation.create(5, 3, "add"))
    history.add(Calculation.create(10, 2, "divide"))

    history.save(str(file_path))

    assert file_path.exists()

    loaded = History()
    loaded.load(str(file_path))

    assert len(loaded) == 2
    assert loaded.dataframe.iloc[0]["result"] == 8
    assert loaded.dataframe.iloc[1]["result"] == 5


def test_save_creates_parent_directory(tmp_path):
    """Test that saving creates missing directories."""
    file_path = tmp_path / "nested" / "folder" / "history.csv"

    history = History()
    history.add(Calculation.create(2, 2, "add"))

    history.save(str(file_path))

    assert file_path.exists()


def test_load_missing_file(tmp_path):
    """Test loading a nonexistent history file."""
    file_path = tmp_path / "does-not-exist.csv"

    history = History()
    history.add(Calculation.create(5, 3, "add"))

    history.load(str(file_path))

    assert len(history) == 0
    assert history.dataframe.empty


def test_restore_history():
    """Test restoring history from a DataFrame."""
    history = History()

    state = pd.DataFrame(
        [
            {
                "operand1": 10,
                "operand2": 5,
                "operation": "subtract",
                "result": 5,
            }
        ]
    )

    history.restore(state)

    assert len(history) == 1
    assert history.dataframe.iloc[0]["result"] == 5


def test_restore_uses_copy():
    """Test that restored state is copied."""
    history = History()

    state = pd.DataFrame(
        [
            {
                "operand1": 1,
                "operand2": 1,
                "operation": "add",
                "result": 2,
            }
        ]
    )

    history.restore(state)
    state.loc[0, "result"] = 999

    assert history.dataframe.loc[0, "result"] == 2


def test_logging_observer(tmp_path):
    """Test the logging observer."""
    history = History()
    observer = LoggingObserver(str(tmp_path / "calculator.log"))

    history.add_observer(observer)
    history.add(Calculation.create(5, 3, "add"))

    observer.close()
    output = (tmp_path / "calculator.log").read_text()

    assert "operation=add operand1=5 operand2=3 result=8 timestamp=" in output


def test_autosave_observer(tmp_path):
    """Test automatic history saving."""
    file_path = tmp_path / "autosave.csv"

    history = History()
    observer = AutoSaveObserver(str(file_path))

    history.add_observer(observer)
    history.add(Calculation.create(5, 3, "add"))

    assert file_path.exists()

    saved = pd.read_csv(file_path)
    assert len(saved) == 1
    assert saved.iloc[0]["result"] == 8


def test_remove_observer(capsys):
    """Test removing an observer."""
    history = History()
    observer = LoggingObserver()

    history.add_observer(observer)
    history.remove_observer(observer)

    history.add(Calculation.create(5, 3, "add"))

    captured = capsys.readouterr()

    assert captured.out == ""


def test_remove_unregistered_observer():
    """Test removing an observer that was never registered."""
    history = History()
    observer = LoggingObserver()

    history.remove_observer(observer)

    assert len(history) == 0


def test_clear_notifies_observer(tmp_path):
    """Test that clearing history notifies observers."""
    history = History()
    observer = LoggingObserver(str(tmp_path / "calculator.log"))

    history.add(Calculation.create(5, 3, "add"))
    history.add_observer(observer)

    history.clear()

    observer.close()
    output = (tmp_path / "calculator.log").read_text()

    assert "History updated. 0 calculation(s) stored." in output


def test_restore_notifies_observer(tmp_path):
    """Test that restoring history notifies observers."""
    history = History()
    observer = LoggingObserver(str(tmp_path / "calculator.log"))
    history.add_observer(observer)

    state = pd.DataFrame(
        [
            {
                "operand1": 2,
                "operand2": 3,
                "operation": "add",
                "result": 5,
            }
        ]
    )

    history.restore(state)

    observer.close()
    output = (tmp_path / "calculator.log").read_text()

    assert "History updated. 1 calculation(s) stored." in output


def test_abstract_history_observer():
    """Test that HistoryObserver cannot be instantiated."""
    with pytest.raises(TypeError):
        HistoryObserver()