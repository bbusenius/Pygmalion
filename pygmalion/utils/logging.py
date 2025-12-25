"""
Logging utilities for Pygmalion.

This module provides:
- Structured logging with rotating file handlers
- Debug mode support
- User-friendly console output
- Separate logs for different components
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Log levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Default log directory
DEFAULT_LOG_DIR = Path.home() / ".pygmalion" / "logs"

# Global flag for debug mode
_DEBUG_MODE = False


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return _DEBUG_MODE


def setup_logging(
    debug: bool = False,
    log_dir: Optional[Path] = None,
    log_to_file: bool = True,
) -> None:
    """
    Set up logging for Pygmalion.

    Args:
        debug: Enable debug mode (verbose logging)
        log_dir: Directory for log files (default: ~/.pygmalion/logs)
        log_to_file: Whether to log to files (default: True)
    """
    global _DEBUG_MODE
    _DEBUG_MODE = debug

    # Determine log level
    level = DEBUG if debug else INFO

    # Create log directory if needed
    if log_to_file:
        log_dir = log_dir or DEFAULT_LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers = []

    # Console handler - user-friendly output
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    if debug:
        # Detailed format for debug mode
        console_format = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        # Simple format for normal mode
        console_format = logging.Formatter("%(levelname)s: %(message)s")

    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler - detailed logs with rotation
    if log_to_file:
        file_handler = RotatingFileHandler(
            log_dir / "pygmalion.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        file_handler.setLevel(DEBUG)  # Always log everything to file
        file_format = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers unless in debug mode
    if not debug:
        logging.getLogger("urllib3").setLevel(WARNING)
        logging.getLogger("httpx").setLevel(WARNING)
        logging.getLogger("anthropic").setLevel(WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class UserFacingError(Exception):
    """
    Exception for user-facing errors with helpful messages.

    These exceptions are caught and displayed nicely to users
    instead of showing full tracebacks.
    """

    def __init__(self, message: str, suggestion: Optional[str] = None):
        """
        Initialize user-facing error.

        Args:
            message: Error message to display
            suggestion: Optional suggestion for how to fix
        """
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)

    def __str__(self) -> str:
        """Format error for display."""
        if self.suggestion:
            return f"{self.message}\n\nSuggestion: {self.suggestion}"
        return self.message


def format_error_for_user(error: Exception) -> str:
    """
    Format an exception for user-friendly display.

    Args:
        error: The exception to format

    Returns:
        User-friendly error message
    """
    if isinstance(error, UserFacingError):
        return str(error)

    # Map common errors to helpful messages
    error_type = type(error).__name__
    error_msg = str(error)

    if "ANTHROPIC_API_KEY" in error_msg or "authentication" in error_msg.lower():
        return (
            "Authentication failed: Missing or invalid API key.\n\n"
            "Suggestion: Set your API key with:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-api03-...\n"
            "Or create a .env file with ANTHROPIC_API_KEY=..."
        )

    if "connection" in error_msg.lower() or "network" in error_msg.lower():
        return (
            f"Network error: {error_msg}\n\n"
            "Suggestion: Check your internet connection and try again."
        )

    if "permission denied" in error_msg.lower():
        return (
            f"Permission error: {error_msg}\n\n"
            "Suggestion: Check file permissions or run with appropriate access."
        )

    if "not found" in error_msg.lower() and any(
        tool in error_msg.lower() for tool in ["inkscape", "convert", "gimp"]
    ):
        tool_name = (
            "inkscape"
            if "inkscape" in error_msg.lower()
            else "imagemagick" if "convert" in error_msg.lower() else "gimp"
        )
        return (
            f"Tool not found: {tool_name} is not installed.\n\n"
            f"Suggestion: Install {tool_name}:\n"
            f"  sudo apt install {tool_name}  # Ubuntu/Debian\n"
            f"  brew install {tool_name}      # macOS"
        )

    # For unknown errors, show type and message in debug mode
    if is_debug_mode():
        import traceback

        return f"{error_type}: {error_msg}\n\n{traceback.format_exc()}"

    # In normal mode, just show the error message
    return f"{error_type}: {error_msg}\n\nTip: Run with --debug for more details."
