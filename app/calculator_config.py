import os
from dataclasses import dataclass

from dotenv import load_dotenv

from app.exceptions import ConfigurationError


@dataclass
class CalculatorConfig:
    """Manage calculator configuration settings."""

    history_file: str
    auto_save: bool
    max_history: int

    @classmethod
    def from_env(cls) -> "CalculatorConfig":
        """Load and validate configuration from environment variables."""
        load_dotenv()

        history_file = os.getenv(
            "CALCULATOR_HISTORY_FILE",
            "data/history.csv",
        )

        auto_save_value = os.getenv(
            "CALCULATOR_AUTO_SAVE",
            "true",
        ).lower()

        max_history_value = os.getenv(
            "CALCULATOR_MAX_HISTORY",
            "100",
        )

        if auto_save_value not in {"true", "false"}:
            raise ConfigurationError(
                "CALCULATOR_AUTO_SAVE must be 'true' or 'false'."
            )

        try:
            max_history = int(max_history_value)
        except ValueError as exc:
            raise ConfigurationError(
                "CALCULATOR_MAX_HISTORY must be an integer."
            ) from exc

        if max_history <= 0:
            raise ConfigurationError(
                "CALCULATOR_MAX_HISTORY must be greater than zero."
            )

        if not history_file.strip():
            raise ConfigurationError(
                "CALCULATOR_HISTORY_FILE cannot be empty."
            )

        return cls(
            history_file=history_file,
            auto_save=auto_save_value == "true",
            max_history=max_history,
        )