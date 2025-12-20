"""
Pygmalion CLI - Main entry point.

Phase 4: Permission modes and autonomy configuration.

This module provides a command-line interface for Pygmalion that:
- Maintains conversation context across multiple exchanges
- Enables Claude to create and edit files in your working directory
- Allows Claude to run shell commands (Inkscape, ImageMagick, etc.)
- Supports configurable autonomy levels for different workflows

AUTONOMY MODES:
---------------
Control how much Claude can do without asking permission:

  APPROVAL (default):
    Claude asks before making file changes.
    Best for: Learning, reviewing changes, sensitive projects

  AUTO:
    Claude automatically proceeds with file edits.
    Best for: Rapid prototyping, experienced users

  FULL_AUTO:
    No permission prompts at all.
    Best for: Automation, scripts (use with caution!)

Usage:
  $ pygmalion                    # Start with default (approval) mode
  $ pygmalion --mode auto        # Start with auto mode
  $ PYGMALION_AUTONOMY_MODE=auto pygmalion  # Via environment

Commands:
  /mode [approval|auto|full_auto]  - View or change autonomy mode
  /status                          - Show session info including mode
"""

import asyncio
import os
import sys

from pygmalion.agent import AutonomyMode, DesignSession
from pygmalion.config import get_default_autonomy_mode


def print_banner():
    """Display the Pygmalion welcome banner."""
    banner = """
╔═════════════════════════════════════════════════════════════════════════════════╗
║                                                                                 ║
║   ██████╗ ██╗   ██╗ ██████╗ ███╗   ███╗ █████╗ ██╗     ██╗ ██████╗ ███╗   ██╗   ║
║   ██╔══██╗╚██╗ ██╔╝██╔════╝ ████╗ ████║██╔══██╗██║     ██║██╔═══██╗████╗  ██║   ║
║   ██████╔╝ ╚████╔╝ ██║  ███╗██╔████╔██║███████║██║     ██║██║   ██║██╔██╗ ██║   ║
║   ██╔═══╝   ╚██╔╝  ██║   ██║██║╚██╔╝██║██╔══██║██║     ██║██║   ██║██║╚██╗██║   ║
║   ██║        ██║   ╚██████╔╝██║ ╚═╝ ██║██║  ██║███████╗██║╚██████╔╝██║ ╚████║   ║
║   ╚═╝        ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ║
║                                                                                 ║
║                      AI-Powered Design Assistant v0.1.0                         ║
║                                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help():
    """Display available commands."""
    help_text = """
Available Commands:
  /help     - Show this help message
  /status   - Show current session info (mode, directory, tools)
  /mode     - View or change autonomy mode
  /new      - Start a new session (clears context)
  /quit     - Exit Pygmalion
  /clear    - Clear the screen

Autonomy Modes (/mode):
  approval  - Ask before file edits (safest, default)
  auto      - Auto-approve file edits (faster)
  full_auto - No prompts at all (use with caution!)

Example prompts:
  - "Create a responsive landing page for a bakery"
  - "Design an SVG logo with geometric shapes"
  - "Make a color palette and save it as CSS variables"

Iterative workflow:
  1. "Create a navigation bar with Home, About, Contact links"
  2. "Make it sticky at the top"
  3. "Add a dropdown menu under About"
  4. "Export the logo as PNG using Inkscape"
"""
    print(help_text)


def print_status(session: DesignSession, working_dir: str):
    """Display current session information."""
    tools_list = ", ".join(session.allowed_tools)
    mode_name = session.autonomy_mode.name
    mode_desc = {
        "APPROVAL": "asks before file edits",
        "AUTO": "auto-approves file edits",
        "FULL_AUTO": "no permission prompts",
    }.get(mode_name, "")

    status = f"""
Session Status:
  Connected:   {session.is_connected}
  Messages:    {session.message_count}
  Mode:        {mode_name} ({mode_desc})
  Working Dir: {working_dir}
  Tools:       {tools_list}

Use /mode to change autonomy level, /new to start fresh.
"""
    print(status)


def print_mode_help():
    """Display autonomy mode information."""
    mode_help = """
Autonomy Modes:
  approval   - Claude asks before making file changes (default, safest)
  auto       - Claude auto-approves file edits (faster prototyping)
  full_auto  - No permission prompts at all (use with caution!)

Usage:
  /mode            - Show current mode
  /mode auto       - Switch to auto mode
  /mode approval   - Switch to approval mode

Note: Changing mode requires starting a new session.
"""
    print(mode_help)


async def run_cli():
    """
    Main CLI loop for Pygmalion with persistent session, tools, and autonomy.

    This creates a DesignSession that:
    - Maintains context throughout the entire interaction
    - Can create and edit files in the current working directory
    - Can run shell commands for design tools
    - Operates at the configured autonomy level
    """
    print_banner()

    # Use current working directory for all file operations
    working_dir = os.getcwd()

    # Get default autonomy mode (from env var or default to APPROVAL)
    autonomy_mode = get_default_autonomy_mode()

    print("Type /help for available commands, or just start designing!")
    print(f"Working directory: {working_dir}")
    print(f"Mode: {autonomy_mode.name} (use /mode to change)\n")

    # Create a session with the working directory and autonomy mode
    session = DesignSession(working_dir=working_dir, autonomy_mode=autonomy_mode)

    try:
        await session.connect()
        print("✓ Session connected\n")

        while True:
            try:
                # Show message count in prompt to indicate session state
                msg_indicator = (
                    f"[{session.message_count}]" if session.message_count > 0 else ""
                )
                user_input = input(f"\n🎨 You {msg_indicator}: ").strip()

                # Handle empty input
                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    parts = user_input.lower().split()
                    command = parts[0]
                    args = parts[1:] if len(parts) > 1 else []

                    if command in ("/quit", "/exit", "/q"):
                        print("\nGoodbye! Happy designing!")
                        break

                    elif command in ("/help", "/h", "/?"):
                        print_help()
                        continue

                    elif command == "/status":
                        print_status(session, working_dir)
                        continue

                    elif command == "/mode":
                        if not args:
                            # Show current mode and help
                            print(f"\nCurrent mode: {autonomy_mode.name}")
                            print_mode_help()
                        else:
                            # Try to change mode
                            try:
                                new_mode = AutonomyMode.from_string(args[0])
                                if new_mode != autonomy_mode:
                                    autonomy_mode = new_mode
                                    print(f"\nMode changed to: {autonomy_mode.name}")
                                    print("Starting new session with new mode...")
                                    await session.disconnect()
                                    session = DesignSession(
                                        working_dir=working_dir,
                                        autonomy_mode=autonomy_mode,
                                    )
                                    await session.connect()
                                    print("✓ New session started\n")
                                else:
                                    print(f"\nAlready in {autonomy_mode.name} mode.")
                            except ValueError as e:
                                print(f"\n❌ {e}")
                                print_mode_help()
                        continue

                    elif command == "/new":
                        # Disconnect current session and create a new one
                        print("\nStarting new session...")
                        await session.disconnect()
                        session = DesignSession(
                            working_dir=working_dir, autonomy_mode=autonomy_mode
                        )
                        await session.connect()
                        print("✓ New session started (context cleared)\n")
                        continue

                    elif command == "/clear":
                        print("\033[2J\033[H", end="")  # ANSI clear screen
                        print_banner()
                        print(f"Working directory: {working_dir}")
                        print(f"Mode: {autonomy_mode.name}")
                        print(f"(Session active - {session.message_count} messages)\n")
                        continue

                    else:
                        print(f"Unknown command: {command}")
                        print("Type /help for available commands.")
                        continue

                # Send to agent and stream response
                print("\n🤖 Pygmalion: ", end="", flush=True)

                response_started = False
                async for text in session.send(user_input):
                    if not response_started:
                        response_started = True
                    print(text, end="", flush=True)

                if not response_started:
                    print("(No response received)")

                print()  # New line after response

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type /quit to exit.")
                continue

            except EOFError:
                print("\nGoodbye!")
                break

            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type /quit to exit.")

    finally:
        # Always disconnect the session on exit
        if session.is_connected:
            await session.disconnect()
            print("Session disconnected.")


def main():
    """Entry point for the pygmalion command."""
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
