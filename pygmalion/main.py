"""
Pygmalion CLI - Main entry point.

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

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

# Load environment variables from .env file FIRST
# This must happen before importing DesignSession, because DEFAULT_TOOLS
# is evaluated at class definition time and checks is_figma_enabled()
load_dotenv()

from pygmalion.agent import AutonomyMode, DesignSession
from pygmalion.config import get_default_autonomy_mode
from pygmalion.utils import Spinner, format_error_for_user, get_logger, setup_logging

# Get logger for this module
logger = get_logger(__name__)


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

Debug Mode:
  Run with --debug flag for verbose logging:
    pygmalion --debug

  Logs are saved to: ~/.pygmalion/logs/pygmalion.log

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


def get_installed_skills(working_dir: str) -> list[str]:
    """Scan for installed Claude skills in user and project directories."""
    skills = []

    # Check user skills directory
    user_skills_dir = os.path.expanduser("~/.claude/skills")
    if os.path.isdir(user_skills_dir):
        for entry in os.listdir(user_skills_dir):
            skill_path = os.path.join(user_skills_dir, entry)
            if os.path.isdir(skill_path) and os.path.exists(
                os.path.join(skill_path, "SKILL.md")
            ):
                skills.append(entry)

    # Check project skills directory
    project_skills_dir = os.path.join(working_dir, ".claude/skills")
    if os.path.isdir(project_skills_dir):
        for entry in os.listdir(project_skills_dir):
            skill_path = os.path.join(project_skills_dir, entry)
            if os.path.isdir(skill_path) and os.path.exists(
                os.path.join(skill_path, "SKILL.md")
            ):
                if entry not in skills:  # Avoid duplicates
                    skills.append(entry)

    return sorted(skills)


def print_status(session: DesignSession, working_dir: str):
    """Display current session information."""
    # Separate built-in tools from MCP tools
    builtin_tools = [t for t in session.allowed_tools if not t.startswith("mcp__")]
    mcp_tools = [t for t in session.allowed_tools if t.startswith("mcp__")]

    builtin_list = ", ".join(builtin_tools)
    mcp_list = ", ".join(t.split("__")[-1] for t in mcp_tools)  # Just tool names

    mode_name = session.autonomy_mode.name
    mode_desc = {
        "APPROVAL": "asks before file edits",
        "AUTO": "auto-approves file edits",
        "FULL_AUTO": "no permission prompts",
    }.get(mode_name, "")

    # Get installed skills
    skills = get_installed_skills(working_dir)
    skills_list = ", ".join(skills) if skills else "none installed"

    status = f"""
Session Status:
  Connected:   {session.is_connected}
  Messages:    {session.message_count}
  Mode:        {mode_name} ({mode_desc})
  Model:       {session.model}
  Working Dir: {working_dir}
  Built-in:    {builtin_list}
  MCP Tools:   {mcp_list}
  Skills:      {skills_list}

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

    # Create prompt session with history for better input handling
    prompt_session = PromptSession(history=InMemoryHistory())

    # Create a session with the working directory and autonomy mode
    session = DesignSession(working_dir=working_dir, autonomy_mode=autonomy_mode)

    try:
        logger.info(
            f"Connecting session (mode={autonomy_mode.name}, dir={working_dir})"
        )
        with Spinner("Connecting to Claude..."):
            await session.connect()
        logger.info("Session connected successfully")
        print("✓ Session connected\n")

        while True:
            try:
                # Show message count in prompt to indicate session state
                msg_indicator = (
                    f"[{session.message_count}]" if session.message_count > 0 else ""
                )
                user_input = await prompt_session.prompt_async(
                    f"\n🎨 You {msg_indicator}: "
                )
                user_input = user_input.strip()

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
                                    logger.info(
                                        f"Changing mode from {autonomy_mode.name} to {new_mode.name}"
                                    )
                                    autonomy_mode = new_mode
                                    print(f"\nMode changed to: {autonomy_mode.name}")
                                    await session.disconnect()
                                    session = DesignSession(
                                        working_dir=working_dir,
                                        autonomy_mode=autonomy_mode,
                                    )
                                    with Spinner("Starting new session..."):
                                        await session.connect()
                                    logger.info("New session started with new mode")
                                    print("✓ New session started\n")
                                else:
                                    print(f"\nAlready in {autonomy_mode.name} mode.")
                            except ValueError as e:
                                logger.warning(f"Invalid mode: {e}")
                                print(f"\n❌ {e}")
                                print_mode_help()
                        continue

                    elif command == "/new":
                        # Disconnect current session and create a new one
                        logger.info("Starting new session (clearing context)")
                        await session.disconnect()
                        session = DesignSession(
                            working_dir=working_dir, autonomy_mode=autonomy_mode
                        )
                        with Spinner("Starting new session..."):
                            await session.connect()
                        logger.info("New session started")
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
                # Show spinner while waiting for first response
                spinner = Spinner("Thinking...")
                spinner.start()

                response_started = False
                last_char = ""
                tool_spinner = None
                try:
                    async for msg_type, content in session.send(user_input):
                        if msg_type == "text":
                            if not response_started:
                                # Stop initial spinner and show response label
                                spinner.stop()
                                print("🤖 Pygmalion: ", end="", flush=True)
                                response_started = True

                            # If we had a tool spinner running, stop it before showing text
                            if tool_spinner:
                                tool_spinner.stop()
                                tool_spinner = None

                            # Add space between text blocks if needed
                            # (prevents "file.Now" when Claude writes, uses tool, continues)
                            if last_char and content:
                                needs_space = (
                                    last_char not in " \n\t"
                                    and content[0] not in " \n\t"
                                    and last_char in ".!?:)"
                                )
                                if needs_space:
                                    print(" ", end="", flush=True)
                            print(content, end="", flush=True)
                            if content:
                                last_char = content[-1]

                        elif msg_type == "tool_use":
                            # Stop any existing tool spinner
                            if tool_spinner:
                                tool_spinner.stop()
                            # Print newline so spinner appears on new line
                            print()
                            # Start new spinner for this tool
                            tool_spinner = Spinner(f"Working ({content})...")
                            tool_spinner.start()

                    if not response_started:
                        spinner.stop()
                        print("🤖 Pygmalion: (No response received)")
                finally:
                    # Ensure spinners are stopped even if error occurs
                    spinner.stop()
                    if tool_spinner:
                        tool_spinner.stop()

                print()  # New line after response

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type /quit to exit.")
                continue

            except EOFError:
                print("\nGoodbye!")
                break

            except Exception as e:
                logger.error(f"Error during message exchange: {e}", exc_info=True)
                error_msg = format_error_for_user(e)
                print(f"\n❌ {error_msg}")
                print("\nPlease try again or type /quit to exit.")

    finally:
        # Always disconnect the session on exit
        if session.is_connected:
            await session.disconnect()
            print("Session disconnected.")


def main():
    """Entry point for the pygmalion command."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Pygmalion - AI-powered design assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (verbose logging)",
    )
    parser.add_argument(
        "--no-log-file",
        action="store_true",
        help="Disable logging to file",
    )
    args = parser.parse_args()

    # Set up logging
    setup_logging(debug=args.debug, log_to_file=not args.no_log_file)

    try:
        logger.info("Starting Pygmalion")
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        error_msg = format_error_for_user(e)
        print(f"\n❌ Fatal error:\n{error_msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
