from dataclasses import dataclass

import pandas as pd


@dataclass
class CalculatorMemento:
    """Store a snapshot of calculator history."""

    history: pd.DataFrame

    def get_state(self) -> pd.DataFrame:
        """Return a copy of the stored history state."""
        return self.history.copy()


class MementoCaretaker:
    """Manage calculator mementos for undo and redo operations."""

    def __init__(self) -> None:
        self._undo_stack: list[CalculatorMemento] = []
        self._redo_stack: list[CalculatorMemento] = []

    def save(self, memento: CalculatorMemento) -> None:
        """Save a state to the undo stack."""
        self._undo_stack.append(memento)
        self._redo_stack.clear()

    def undo(
        self,
        current_state: CalculatorMemento,
    ) -> CalculatorMemento | None:
        """Return the previous state and preserve the current state for redo."""
        if not self._undo_stack:
            return None

        previous_state = self._undo_stack.pop()
        self._redo_stack.append(current_state)
        return previous_state

    def redo(
        self,
        current_state: CalculatorMemento,
    ) -> CalculatorMemento | None:
        """Restore the most recently undone state."""
        if not self._redo_stack:
            return None

        next_state = self._redo_stack.pop()
        self._undo_stack.append(current_state)
        return next_state

    @property
    def can_undo(self) -> bool:
        """Return whether an undo operation is available."""
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        """Return whether a redo operation is available."""
        return bool(self._redo_stack)