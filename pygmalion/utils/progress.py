"""
Progress indicators and feedback utilities for Pygmalion.

This module provides:
- Spinner for long-running operations
- Tool execution feedback
- Progress status updates
"""

import sys
import threading
import time
from typing import Optional


class Spinner:
    """
    A simple terminal spinner for indicating progress.

    Usage:
        with Spinner("Loading..."):
            # Long running operation
            time.sleep(5)
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Working...", stream=None):
        """
        Initialize the spinner.

        Args:
            message: Message to display next to spinner
            stream: Output stream (default: sys.stderr)
        """
        self.message = message
        self.stream = stream or sys.stderr
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._frame_idx = 0

    def _spin(self):
        """Internal method to animate the spinner."""
        while not self._stop_event.is_set():
            frame = self.FRAMES[self._frame_idx % len(self.FRAMES)]
            self.stream.write(f"\r{frame} {self.message}")
            self.stream.flush()
            self._frame_idx += 1
            time.sleep(0.1)

    def start(self):
        """Start the spinner animation."""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()

    def stop(self, clear: bool = True):
        """
        Stop the spinner animation.

        Args:
            clear: If True, clear the spinner line
        """
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=0.5)
            if clear:
                # Clear the line
                self.stream.write("\r" + " " * (len(self.message) + 3) + "\r")
                self.stream.flush()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


def show_tool_execution(tool_name: str, args: Optional[str] = None):
    """
    Display tool execution feedback.

    Args:
        tool_name: Name of the tool being executed
        args: Optional arguments/description
    """
    if args:
        print(f"🔧 Executing: {tool_name} ({args})", file=sys.stderr)
    else:
        print(f"🔧 Executing: {tool_name}", file=sys.stderr)


def show_tool_result(tool_name: str, success: bool = True, message: str = ""):
    """
    Display tool execution result.

    Args:
        tool_name: Name of the tool
        success: Whether execution succeeded
        message: Optional result message
    """
    if success:
        status = "✓"
        msg = f"{status} {tool_name} completed"
    else:
        status = "✗"
        msg = f"{status} {tool_name} failed"

    if message:
        msg += f": {message}"

    print(msg, file=sys.stderr)


def show_status(message: str, emoji: str = "ℹ️"):
    """
    Display a status message.

    Args:
        message: Status message to display
        emoji: Emoji to prefix the message with
    """
    print(f"{emoji} {message}", file=sys.stderr)
