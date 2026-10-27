import codecs
import math
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from app.exceptions import ConfigurationError


@dataclass
class CalculatorConfig:
    """Manage calculator configuration settings."""

    history_file: str
    auto_save: bool
    max_history: int
    log_dir: str = "logs"
    history_dir: str = "data"
    log_file: str = "calculator.log"
    precision: int = 10
    max_input_value: float = 1e100
    default_encoding: str = "utf-8"

    @property
    def history_path(self) -> str:
        """Keep explicit paths compatible with Stage 1."""
        path = Path(self.history_file)
        return str(path if path.parent != Path(".") else Path(self.history_dir) / path)

    @property
    def log_path(self) -> str:
        """Resolve the configured log destination."""
        return str(Path(self.log_dir) / self.log_file)


    @classmethod
    def from_env(cls) -> "CalculatorConfig":
        """Load and validate configuration from environment variables."""
        load_dotenv()

        history_file = os.getenv(
            "CALCULATOR_HISTORY_FILE",
            "history.csv",
        )

        auto_save_value = os.getenv(
            "CALCULATOR_AUTO_SAVE",
            "true",
        ).lower()

        history_key = (
            "CALCULATOR_MAX_HISTORY_SIZE"
            if "CALCULATOR_MAX_HISTORY_SIZE" in os.environ
            else "CALCULATOR_MAX_HISTORY"
        )
        max_history_value = os.getenv(
            history_key,
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
                f"{history_key} must be an integer."
            ) from exc

        if max_history <= 0:
            raise ConfigurationError(
                f"{history_key} must be greater than zero."
            )

        if not history_file.strip():
            raise ConfigurationError(
                "CALCULATOR_HISTORY_FILE cannot be empty."
            )

        settings = {}
        for name, default in (
            ("LOG_DIR", "logs"), ("HISTORY_DIR", "data"),
            ("LOG_FILE", "calculator.log"), ("DEFAULT_ENCODING", "utf-8"),
        ):
            value = os.getenv("CALCULATOR_" + name, default).strip()
            if not value:
                raise ConfigurationError(f"CALCULATOR_{name} cannot be empty.")
            settings[name.lower()] = value
        try:
            precision = int(os.getenv("CALCULATOR_PRECISION", "10"))
            if not 0 <= precision <= 15:
                raise ValueError("must be between 0 and 15")
        except ValueError as exc:
            raise ConfigurationError("CALCULATOR_PRECISION must be an integer between 0 and 15.") from exc
        try:
            maximum = float(os.getenv("CALCULATOR_MAX_INPUT_VALUE", "1e100"))
            if not math.isfinite(maximum) or maximum <= 0:
                raise ValueError("must be finite and positive")
        except ValueError as exc:
            raise ConfigurationError("CALCULATOR_MAX_INPUT_VALUE must be finite and greater than zero.") from exc
        try:
            codecs.lookup(settings["default_encoding"])
        except LookupError as exc:
            raise ConfigurationError("CALCULATOR_DEFAULT_ENCODING is not a recognized encoding.") from exc

        return cls(
            **settings,
            precision=precision,
            max_input_value=maximum,
            history_file=history_file,
            auto_save=auto_save_value == "true",
            max_history=max_history,
        )