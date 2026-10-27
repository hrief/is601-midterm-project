from abc import ABC, abstractmethod
from pathlib import Path
import logging
import math

from app.exceptions import HistoryError
from app.operations import OperationFactory

import pandas as pd

from app.calculation import Calculation


class HistoryObserver(ABC):
    """Abstract observer for history changes."""

    @abstractmethod
    def update(self, history: "History") -> None:
        """React to a history change."""
        raise NotImplementedError # pragma: no cover


class AutoSaveObserver(HistoryObserver):
    """Automatically save history when it changes."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def update(self, history: "History") -> None:
        history.save(self.file_path)


class LoggingObserver(HistoryObserver):
    """Write history changes to a dedicated file logger."""

    def __init__(self, file_path: str = "logs/calculator.log",
                 encoding: str = "utf-8") -> None:
        self.logger = logging.Logger(f"calculator.{id(self)}", logging.INFO)
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(path, encoding=encoding)
        except (OSError, ValueError) as exc:
            raise HistoryError(f"Cannot open calculation log '{file_path}': {exc}") from exc
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self.logger.addHandler(handler)

    def update(self, history: "History") -> None:
        if history.last_calculation is not None:
            row = history.last_calculation.to_dict()
            self.logger.info(
                "Calculation operation=%s operand1=%s operand2=%s result=%s timestamp=%s",
                row["operation"], row["operand1"], row["operand2"],
                row["result"], row["timestamp"],
            )
        else:
            self.logger.info("History updated. %s calculation(s) stored.", len(history))

    def close(self) -> None:
        """Release log file handles."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


class History:
    """Manage calculator history using a pandas DataFrame."""

    COLUMNS = ["operand1", "operand2", "operation", "result", "timestamp"]

    def __init__(self, max_history: int = 100, encoding: str = "utf-8") -> None:
        """Initialize history and its observers."""
        self.max_history = max_history
        self.encoding = encoding
        self.last_calculation = None
        self._history = pd.DataFrame(columns=self.COLUMNS)
        self._observers: list[HistoryObserver] = []

    @property
    def dataframe(self) -> pd.DataFrame:
        """Return a copy of the history DataFrame."""
        return self._history.copy()

    def add_observer(self, observer: HistoryObserver) -> None:
        """Register a history observer."""
        self._observers.append(observer)

    def remove_observer(self, observer: HistoryObserver) -> None:
        """Remove a registered observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self) -> None:
        """Notify all registered observers."""
        for observer in self._observers:
            observer.update(self)

    def add(self, calculation: Calculation) -> None:
        """Add a calculation and notify observers."""
        self.last_calculation = calculation
        new_row = pd.DataFrame([calculation.to_dict()])
        self._history = pd.concat(
            [self._history, new_row],
            ignore_index=True,
        )
        self._history = self._history.tail(self.max_history).reset_index(drop=True)
        self._notify_observers()

    def clear(self) -> None:
        """Clear calculation history and notify observers."""
        self.last_calculation = None
        self._history = pd.DataFrame(columns=self.COLUMNS)
        self._notify_observers()

    def restore(self, state: pd.DataFrame) -> None:
        """Restore history from a DataFrame state."""
        self.last_calculation = None
        self._history = state.tail(self.max_history).reset_index(drop=True).copy()
        self._notify_observers()

    def save(self, file_path: str) -> None:
        """Save calculation history to a CSV file."""
        path = Path(file_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self._history.to_csv(path, index=False, encoding=self.encoding)
        except (OSError, UnicodeError) as exc:
            raise HistoryError(f"Cannot save history to '{path}': {exc}") from exc

    def load(self, file_path: str) -> None:
        """Load validated CSV atomically; legacy rows have unknown timestamps."""
        path = Path(file_path)
        try:
            frame = pd.read_csv(path, encoding=self.encoding)
            required = set(self.COLUMNS) - {"timestamp"}
            if not required.issubset(frame.columns):
                raise ValueError("Missing required history columns.")
            for column in ("operand1", "operand2", "result"):
                frame[column] = pd.to_numeric(frame[column], errors="raise")
                if not frame[column].map(math.isfinite).all():
                    raise ValueError(f"Invalid finite numeric data in {column}.")
            if not frame["operation"].isin(OperationFactory.supported_operations()).all():
                raise ValueError("Invalid operation in history.")
            if "timestamp" not in frame:
                frame["timestamp"] = ""
            else:
                for value in frame["timestamp"].dropna():
                    pd.to_datetime(value, utc=True, errors="raise")
                frame["timestamp"] = frame["timestamp"].fillna("")
            self._history = frame[self.COLUMNS].tail(self.max_history).reset_index(drop=True)
            self.last_calculation = None
        except FileNotFoundError:
            self._history = pd.DataFrame(columns=self.COLUMNS)
            self.last_calculation = None
        except (OSError, ValueError, UnicodeError, pd.errors.ParserError) as exc:
            raise HistoryError(f"Cannot load history from '{path}': {exc}") from exc

    def __len__(self) -> int:
        """Return the number of calculations in history."""
        return len(self._history)