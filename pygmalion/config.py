"""
Configuration management for Pygmalion.

Phase 4: Permission modes and autonomy configuration.

AUTONOMY MODES EXPLAINED:
-------------------------
The Claude Agent SDK supports different levels of autonomy that control
how much Claude can do without asking for permission:

1. APPROVAL MODE (default) - "default"
   - Claude asks permission before file edits and potentially dangerous actions
   - Safest option for learning or when you want to review changes
   - Good for: New users, sensitive projects, learning the tool

2. AUTO MODE - "acceptEdits"
   - Claude automatically proceeds with file edits
   - Still asks for permission on truly dangerous operations
   - Good for: Experienced users, rapid prototyping, trusted workflows

3. FULL AUTO MODE - "bypassPermissions"
   - Claude proceeds with all operations without asking
   - Use with caution! No safety prompts.
   - Good for: Automated scripts, CI/CD, when you fully trust the workflow

CHOOSING A MODE:
----------------
  ┌─────────────────────────────────────────────────────────────┐
  │  "I want to review everything"     → APPROVAL (default)    │
  │  "Auto-approve file edits"         → AUTO (acceptEdits)    │
  │  "Just do it, I trust you"         → FULL AUTO (bypass)    │
  └─────────────────────────────────────────────────────────────┘

GUI ACTIONS:
------------
Even in AUTO mode, actions that open GUI applications (like Inkscape)
should require confirmation since they affect the user's desktop.
This is handled by the DesignSession's permission handler.

ENVIRONMENT VARIABLES:
----------------------
You can set defaults via environment variables:
  PYGMALION_AUTONOMY_MODE=auto     # Set default autonomy mode
  PYGMALION_GEMINI_ENABLED=true    # Enable Gemini integration (Phase 8)
  GEMINI_API_KEY=...               # Gemini API key (Phase 8)
"""

import os
from enum import Enum
from typing import Literal


class AutonomyMode(Enum):
    """
    Autonomy levels for the design session.

    These map to the SDK's permission_mode values:
    - APPROVAL -> "default" (ask before edits)
    - AUTO -> "acceptEdits" (auto-approve file changes)
    - FULL_AUTO -> "bypassPermissions" (no prompts at all)
    """

    APPROVAL = "default"
    AUTO = "acceptEdits"
    FULL_AUTO = "bypassPermissions"

    @classmethod
    def from_string(cls, value: str) -> "AutonomyMode":
        """
        Parse autonomy mode from string (case-insensitive).

        Accepts:
          - "approval", "default" -> APPROVAL
          - "auto", "acceptEdits" -> AUTO
          - "full_auto", "full-auto", "bypass", "bypassPermissions" -> FULL_AUTO
        """
        value = value.lower().replace("-", "_").replace(" ", "_")

        if value in ("approval", "default"):
            return cls.APPROVAL
        elif value in ("auto", "acceptedits"):
            return cls.AUTO
        elif value in ("full_auto", "fullauto", "bypass", "bypasspermissions"):
            return cls.FULL_AUTO
        else:
            raise ValueError(
                f"Unknown autonomy mode: {value}. "
                f"Expected: approval, auto, or full_auto"
            )


# Type alias for permission mode strings (what the SDK expects)
PermissionMode = Literal["default", "acceptEdits", "bypassPermissions"]


def get_default_autonomy_mode() -> AutonomyMode:
    """
    Get the default autonomy mode from environment or fallback to APPROVAL.

    Checks PYGMALION_AUTONOMY_MODE environment variable.
    """
    env_value = os.environ.get("PYGMALION_AUTONOMY_MODE", "").strip()

    if env_value:
        try:
            return AutonomyMode.from_string(env_value)
        except ValueError:
            # Invalid value in env var, use default
            pass

    return AutonomyMode.APPROVAL


def is_gemini_enabled() -> bool:
    """
    Check if Gemini integration is enabled via environment variable.

    Returns True if PYGMALION_GEMINI_ENABLED is set to a truthy value
    AND GEMINI_API_KEY is present.
    """
    enabled = os.environ.get("PYGMALION_GEMINI_ENABLED", "").lower()
    has_key = bool(os.environ.get("GEMINI_API_KEY", "").strip())

    return enabled in ("true", "1", "yes", "on") and has_key


def is_figma_enabled() -> bool:
    """
    Check if Figma MCP integration is enabled via environment variable.

    Returns True if PYGMALION_FIGMA_ENABLED is set to a truthy value
    AND FIGMA_ACCESS_TOKEN is present.

    Note: Figma MCP server (GLips/Figma-Context-MCP) must be installed separately.
    """
    enabled = os.environ.get("PYGMALION_FIGMA_ENABLED", "").lower()
    has_token = bool(os.environ.get("FIGMA_ACCESS_TOKEN", "").strip())

    return enabled in ("true", "1", "yes", "on") and has_token
