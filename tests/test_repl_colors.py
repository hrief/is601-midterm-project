"""Terminal-independent tests for REPL presentation colors."""
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest
from colorama import Fore, Style

from app import calculator_repl as repl


@pytest.fixture
def terminal(monkeypatch, tmp_path, capsys):
    """Simulate a color terminal without changing the real console."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("CALCULATOR_LOG_FILE", "calculator.log")
    monkeypatch.setenv("CALCULATOR_HISTORY_FILE", str(tmp_path / "history.csv"))
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", "true")
    monkeypatch.setattr(
        repl, "sys", SimpleNamespace(stdout=SimpleNamespace(isatty=lambda: True)),
    )
    initialize = Mock()
    monkeypatch.setattr(repl, "init", initialize)
    return initialize


@pytest.mark.parametrize("kind,color", [
    ("success", Fore.GREEN), ("error", Fore.RED), ("warning", Fore.YELLOW),
    ("info", Fore.CYAN), ("history", Fore.BLUE),
])
def test_message_colors_and_reset(terminal, capsys, kind, color):
    repl.print_message("Message", kind)
    print("Plain output")
    assert capsys.readouterr().out == (
        f"{color}Message{Style.RESET_ALL}\nPlain output\n"
    )


@pytest.mark.parametrize("mode", ["redirected", "dumb", "no_color"])
def test_plain_text_fallback(terminal, monkeypatch, capsys, mode):
    if mode == "redirected":
        monkeypatch.setattr(repl.sys.stdout, "isatty", lambda: False)
    elif mode == "dumb":
        monkeypatch.setenv("TERM", "dumb")
    else:
        monkeypatch.setenv("NO_COLOR", "")
    for kind in repl.OUTPUT_COLORS:
        repl.print_message("Readable message", kind)
    assert capsys.readouterr().out == "Readable message\n" * 5


def test_help_is_cyan(terminal, capsys):
    repl.print_help()
    output = capsys.readouterr().out
    assert output.startswith(Fore.CYAN)
    assert output.endswith(Style.RESET_ALL + "\n")
    assert "Available operations:" in output
    assert "Commands:" in output
    for operation in repl.OperationFactory.supported_operations():
        assert operation in output


@pytest.mark.parametrize("commands,color,message", [
    (["add 5 3"], Fore.GREEN, "Result: 8.0"),
    (["clear"], Fore.GREEN, "History cleared."),
    (["add 5 3", "undo"], Fore.GREEN, "Undo successful."),
    (["add 5 3", "undo", "redo"], Fore.GREEN, "Redo successful."),
    (["save"], Fore.GREEN, "History saved."),
    (["save", "load"], Fore.GREEN, "History loaded."),
    ([], Fore.GREEN, "Goodbye!"),
    ([], Fore.CYAN, "Advanced Calculator"),
    ([], Fore.CYAN, "Type 'help' for available commands."),
    (["unknown"], Fore.RED, "Unknown command: unknown"),
    (["add 5"], Fore.RED, "Usage: <operation> <number1> <number2>"),
    (["add potato 3"], Fore.RED, "Error: Invalid number: potato"),
    (["divide 10 0"], Fore.RED, "Error: Cannot divide by zero."),
    (["root -4 2"], Fore.RED,
     "Error: Cannot calculate an even or non-integer root of a negative number."),
    (["history"], Fore.YELLOW, "No calculations in history."),
    (["undo"], Fore.YELLOW, "Nothing to undo."),
    (["redo"], Fore.YELLOW, "Nothing to redo."),
])
def test_repl_message_colors(terminal, monkeypatch, capsys, commands, color, message):
    inputs = iter([*commands, "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    repl.run_repl()
    terminal.assert_called_once_with()
    assert f"{color}{message}{Style.RESET_ALL}" in capsys.readouterr().out


def test_history_blue_and_persistence_plain(terminal, monkeypatch, tmp_path, capsys):
    # A second REPL session exercises previously saved results and timestamps.
    inputs = iter(["add 5 3", "exit", "history", "divide 1 0", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    repl.run_repl()
    capsys.readouterr()
    repl.run_repl()
    output = capsys.readouterr().out
    history_output = output.split(Fore.BLUE, 1)[1].split(Style.RESET_ALL, 1)[0]
    assert "operand1" in history_output
    assert "timestamp" in history_output
    assert "add" in history_output
    assert "8.0" in history_output
    csv = (tmp_path / "history.csv").read_text()
    log = (tmp_path / "calculator.log").read_text()
    assert "\x1b" not in csv
    assert "\x1b" not in log
    saved = pd.read_csv(tmp_path / "history.csv")
    assert saved.iloc[0]["result"] == 8
    assert saved.iloc[0]["timestamp"] in history_output
    assert "INFO Calculation operation=add" in log
    assert "WARNING Cannot divide by zero" in log


def test_startup_and_manual_load_errors_red(terminal, monkeypatch, tmp_path, capsys):
    (tmp_path / "history.csv").write_text("invalid csv")
    inputs = iter(["load", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    repl.run_repl()
    output = capsys.readouterr().out
    assert output.count(Fore.RED + "Error: Cannot load history") == 2
    assert output.count(Fore.RED) == 2


@pytest.mark.parametrize("exception", [EOFError, KeyboardInterrupt])
def test_interrupt_exit_color(terminal, monkeypatch, capsys, exception):
    def interrupt(_):
        raise exception
    monkeypatch.setattr("builtins.input", interrupt)
    repl.run_repl()
    assert Fore.GREEN + "\nGoodbye!" + Style.RESET_ALL in capsys.readouterr().out

