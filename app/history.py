from abc import ABC, abstractmethod
from pathlib import Path

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
    """Log history changes to the console."""

    def update(self, history: "History") -> None:
        print(f"History updated. {len(history)} calculation(s) stored.")


class History:
    """Manage calculator history using a pandas DataFrame."""

    COLUMNS = ["operand1", "operand2", "operation", "result"]

    def __init__(self) -> None:
        """Initialize history and its observers."""
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
        new_row = pd.DataFrame([calculation.to_dict()])
        self._history = pd.concat(
            [self._history, new_row],
            ignore_index=True,
        )
        self._notify_observers()

    def clear(self) -> None:
        """Clear calculation history and notify observers."""
        self._history = pd.DataFrame(columns=self.COLUMNS)
        self._notify_observers()

    def restore(self, state: pd.DataFrame) -> None:
        """Restore history from a DataFrame state."""
        self._history = state.copy()
        self._notify_observers()

    def save(self, file_path: str) -> None:
        """Save calculation history to a CSV file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._history.to_csv(path, index=False)

    def load(self, file_path: str) -> None:
        """Load calculation history from a CSV file."""
        path = Path(file_path)

        if not path.exists():
            self._history = pd.DataFrame(columns=self.COLUMNS)
            return

        self._history = pd.read_csv(path)

    def __len__(self) -> int:
        """Return the number of calculations in history."""
        return len(self._history)