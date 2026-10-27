"""File logging shared by calculation observers and the REPL."""
import logging
from pathlib import Path

from app.exceptions import HistoryError


class Logger(logging.Logger):
    """Own a configured file handler without modifying the root logger."""

    def __init__(self, file_path: str, encoding: str = "utf-8") -> None:
        super().__init__(f"calculator.{id(self)}", logging.INFO)
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(path, encoding=encoding)
        except (OSError, ValueError) as exc:
            raise HistoryError(
                f"Cannot open calculation log '{file_path}': {exc}"
            ) from exc
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        self.addHandler(handler)

    def close(self) -> None:
        """Release file handles; safe to call more than once."""
        for handler in self.handlers[:]:
            handler.close()
            self.removeHandler(handler)
