import pytest

from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError


def test_config_from_environment(monkeypatch):
    """Test loading valid configuration from environment variables."""
    monkeypatch.setenv(
        "CALCULATOR_HISTORY_FILE",
        "test/history.csv",
    )
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", "false")
    monkeypatch.setenv("CALCULATOR_MAX_HISTORY", "50")

    config = CalculatorConfig.from_env()

    assert config.history_file == "test/history.csv"
    assert config.auto_save is False
    assert config.max_history == 50


def test_config_auto_save_true(monkeypatch):
    """Test true auto-save configuration."""
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", "TRUE")

    config = CalculatorConfig.from_env()

    assert config.auto_save is True


@pytest.mark.parametrize(
    "value",
    [
        "yes",
        "no",
        "potato",
        "1",
    ],
)
def test_invalid_auto_save(monkeypatch, value):
    """Test invalid auto-save values."""
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", value)

    with pytest.raises(
        ConfigurationError,
        match="CALCULATOR_AUTO_SAVE must be 'true' or 'false'",
    ):
        CalculatorConfig.from_env()


def test_invalid_max_history(monkeypatch):
    """Test nonnumeric maximum history."""
    monkeypatch.setenv("CALCULATOR_MAX_HISTORY", "potato")

    with pytest.raises(
        ConfigurationError,
        match="CALCULATOR_MAX_HISTORY must be an integer",
    ):
        CalculatorConfig.from_env()


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
        "-100",
    ],
)
def test_nonpositive_max_history(monkeypatch, value):
    """Test invalid maximum history ranges."""
    monkeypatch.setenv("CALCULATOR_MAX_HISTORY", value)

    with pytest.raises(
        ConfigurationError,
        match="CALCULATOR_MAX_HISTORY must be greater than zero",
    ):
        CalculatorConfig.from_env()


def test_empty_history_file(monkeypatch):
    """Test an empty history file configuration."""
    monkeypatch.setenv("CALCULATOR_HISTORY_FILE", "   ")

    with pytest.raises(
        ConfigurationError,
        match="CALCULATOR_HISTORY_FILE cannot be empty",
    ):
        CalculatorConfig.from_env()