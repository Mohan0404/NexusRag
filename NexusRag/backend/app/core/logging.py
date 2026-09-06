import logging
from pathlib import Path
import re
import sys
from typing import Any, Optional


class SensitiveDataFilter(logging.Filter):
    """Logging filter and utility that redacts API keys, tokens, passwords, and sensitive credentials."""

    # Regex patterns matching sensitive formats and key-value declarations
    PATTERNS = [
        # Google/Gemini API key pattern (AIzaSy...)
        re.compile(r"(AIzaSy[0-9A-Za-z_\-]{20,})"),
        # OpenRouter / OpenAI API key pattern (sk-or-..., sk-...)
        re.compile(r"(sk-[a-zA-Z0-9_\-]{20,})"),
        # Authorization Bearer tokens
        re.compile(r"(Bearer\s+)([a-zA-Z0-9_\-\.]{15,})", re.IGNORECASE),
        # Generic key=value or "key": "value" pairs
        re.compile(
            r"((?:api[_-]?key|password|secret|token|auth|authorization)\s*[:=]\s*['\"]?)([^'\"\s,\}\]]+)",
            re.IGNORECASE,
        ),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitizes the log record message and arguments before formatting."""
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._redact_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._redact_value(arg) for arg in record.args)
            elif isinstance(record.args, list):
                record.args = [self._redact_value(arg) for arg in record.args]

        return True

    @classmethod
    def redact(cls, text: str) -> str:
        """Applies sensitive patterns to redact secrets with [REDACTED]."""
        for pattern in cls.PATTERNS:

            def replace_fn(match: re.Match) -> str:
                if match.lastindex and match.lastindex >= 2:
                    return f"{match.group(1)}[REDACTED]"
                return "[REDACTED]"

            text = pattern.sub(replace_fn, text)
        return text

    @classmethod
    def _redact_value(cls, val: Any) -> Any:
        if isinstance(val, str):
            return cls.redact(val)
        return val


class SensitiveDataFormatter(logging.Formatter):
    """Formatter that guarantees any sensitive content in the rendered string is redacted."""

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return SensitiveDataFilter.redact(formatted)


def setup_logging(
    log_level: str = "INFO", log_file_path: Optional[str] = None
) -> logging.Logger:
    """Configures centralized structured logging with sensitive data redaction.

    Args:
        log_level: Desired log level string (e.g. 'DEBUG', 'INFO', 'WARNING', 'ERROR').
        log_file_path: Optional destination file path for persistent logs.

    Returns:
        The configured root logger instance.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = SensitiveDataFormatter(fmt=log_format, datefmt=date_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    sensitive_filter = SensitiveDataFilter()

    # Reconfigure or attach handlers
    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)

        if log_file_path:
            file_path = Path(log_file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(str(file_path), encoding="utf-8")
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(sensitive_filter)
            root_logger.addHandler(file_handler)
    else:
        for handler in root_logger.handlers:
            handler.setLevel(numeric_level)
            handler.setFormatter(formatter)
            if not any(isinstance(f, SensitiveDataFilter) for f in handler.filters):
                handler.addFilter(sensitive_filter)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Returns a named logger instance for the calling module."""
    return logging.getLogger(name)
