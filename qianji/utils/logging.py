"""Logging configuration for qianji."""

import logging
import sys
from typing import Any

import structlog


def configure_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: str | None = None,
) -> None:
    """Configure structured logging for qianji.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: Whether to use JSON format
        log_file: Optional log file path
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Configure structlog
    shared_processors: list = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_format:
        # JSON format for production
        processors = shared_processors + [structlog.processors.JSONRenderer()]
    else:
        # Console format for development
        processors = shared_processors + [structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


class RequestLogger:
    """Logger for HTTP requests."""

    def __init__(self, logger: structlog.stdlib.BoundLogger):
        self.logger = logger

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **extra: Any,
    ) -> None:
        """Log an HTTP request.

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            **extra: Additional fields to log
        """
        log_data: dict[str, Any] = {
            "event": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
        }
        log_data.update(extra)

        if status_code >= 500:
            self.logger.error(**log_data)
        elif status_code >= 400:
            self.logger.warning(**log_data)
        else:
            self.logger.info(**log_data)
