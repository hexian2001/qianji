"""Custom exceptions for qianji."""


class QianjiError(Exception):
    """Base exception for qianji."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class BrowserError(QianjiError):
    """Browser-related errors."""

    def __init__(self, message: str, code: str = "BROWSER_ERROR") -> None:
        super().__init__(message, code)


class BrowserNotStartedError(BrowserError):
    """Browser not started error."""

    def __init__(self, message: str = "Browser is not started") -> None:
        super().__init__(message, "BROWSER_NOT_STARTED")


class BrowserLaunchError(BrowserError):
    """Browser launch error."""

    def __init__(self, message: str = "Failed to launch browser") -> None:
        super().__init__(message, "BROWSER_LAUNCH_FAILED")


class NavigationError(BrowserError):
    """Navigation error."""

    def __init__(self, message: str = "Navigation failed") -> None:
        super().__init__(message, "NAVIGATION_FAILED")


class ElementNotFoundError(BrowserError):
    """Element not found error."""

    def __init__(self, ref: str) -> None:
        super().__init__(f"Element not found: {ref}", "ELEMENT_NOT_FOUND")
        self.ref = ref


class ActionError(BrowserError):
    """Action execution error."""

    def __init__(self, message: str = "Action failed") -> None:
        super().__init__(message, "ACTION_FAILED")


class ConfigError(QianjiError):
    """Configuration error."""

    def __init__(self, message: str = "Invalid configuration") -> None:
        super().__init__(message, "CONFIG_ERROR")


class ValidationError(QianjiError):
    """Validation error."""

    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message, "VALIDATION_ERROR")
