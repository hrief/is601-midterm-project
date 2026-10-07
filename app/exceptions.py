class CalculatorError(Exception):
    """Base exception for calculator errors."""


class ConfigurationError(CalculatorError):
    """Raised when calculator configuration is invalid."""


class ValidationError(CalculatorError):
    """Raised when user input is invalid."""


class OperationError(CalculatorError):
    """Raised when a calculator operation fails."""