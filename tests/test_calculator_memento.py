import pandas as pd

from app.calculator_memento import (
    CalculatorMemento,
    MementoCaretaker,
)


def make_state(*results):
    """Create a simple DataFrame state for memento tests."""
    return pd.DataFrame({"result": list(results)})


def test_memento_returns_state():
    """Test retrieving state from a memento."""
    state = make_state(10, 20)
    memento = CalculatorMemento(state)

    restored = memento.get_state()

    pd.testing.assert_frame_equal(restored, state)


def test_memento_returns_copy():
    """Test that memento state cannot be modified externally."""
    state = make_state(10)
    memento = CalculatorMemento(state)

    restored = memento.get_state()
    restored.loc[0, "result"] = 999

    assert memento.get_state().loc[0, "result"] == 10


def test_new_caretaker_has_no_undo_or_redo():
    """Test the initial caretaker state."""
    caretaker = MementoCaretaker()

    assert caretaker.can_undo is False
    assert caretaker.can_redo is False


def test_save_enables_undo():
    """Test saving a memento."""
    caretaker = MementoCaretaker()
    memento = CalculatorMemento(make_state())

    caretaker.save(memento)

    assert caretaker.can_undo is True


def test_undo():
    """Test restoring the previous state."""
    caretaker = MementoCaretaker()

    previous = CalculatorMemento(make_state(10))
    current = CalculatorMemento(make_state(10, 20))

    caretaker.save(previous)

    restored = caretaker.undo(current)

    assert restored is previous
    assert caretaker.can_redo is True


def test_undo_with_empty_stack():
    """Test undo when no previous state exists."""
    caretaker = MementoCaretaker()
    current = CalculatorMemento(make_state())

    assert caretaker.undo(current) is None


def test_redo():
    """Test restoring an undone state."""
    caretaker = MementoCaretaker()

    previous = CalculatorMemento(make_state(10))
    current = CalculatorMemento(make_state(10, 20))

    caretaker.save(previous)
    caretaker.undo(current)

    restored = caretaker.redo(previous)

    assert restored is current
    assert caretaker.can_undo is True


def test_redo_with_empty_stack():
    """Test redo when no redo state exists."""
    caretaker = MementoCaretaker()
    current = CalculatorMemento(make_state())

    assert caretaker.redo(current) is None


def test_save_clears_redo_stack():
    """Test that a new action clears redo history."""
    caretaker = MementoCaretaker()

    first = CalculatorMemento(make_state())
    second = CalculatorMemento(make_state(10))
    third = CalculatorMemento(make_state(20))

    caretaker.save(first)
    caretaker.undo(second)

    assert caretaker.can_redo is True

    caretaker.save(third)

    assert caretaker.can_redo is False