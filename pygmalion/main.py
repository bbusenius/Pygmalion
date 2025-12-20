"""
Pygmalion CLI - Main entry point.

Phase 3: Built-in tools for file operations and shell commands.

This module provides a command-line interface for Pygmalion that:
- Maintains conversation context across multiple exchanges
- Enables Claude to create and edit files in your working directory
- Allows Claude to run shell commands (Inkscape, ImageMagick, etc.)
- Supports web search for design research and inspiration

TOOLS ENABLED:
--------------
Claude can now actually CREATE your designs, not just describe them:

  FILE TOOLS:
  - Read/Write/Edit files (HTML, CSS, SVG, images)

  SHELL TOOLS:
  - Run commands like inkscape, convert (ImageMagick), git

  WEB TOOLS:
  - Search the web for design inspiration
  - Fetch content from URLs

WORKING DIRECTORY:
------------------
All file operations happen in the current directory where you run pygmalion.
This keeps your designs organized and limits Claude's file access for safety.

Example workflow:
  $ mkdir my-website && cd my-website
  $ pygmalion
  🎨 You: Create a landing page for a coffee shop with a logo
  🤖 Pygmalion: [Creates index.html, styles.css, logo.svg]
"""

import asyncio
import os
import sys

from pygmalion.agent import DesignSession


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
  /status   - Show current session info (directory, tools, messages)
  /new      - Start a new session (clears context)
  /quit     - Exit Pygmalion
  /clear    - Clear the screen

Tools Available:
  Claude can create and edit files, run shell commands, and search the web.
  All files are created in your current working directory.

Example prompts:
  - "Create a responsive landing page for a bakery"
  - "Design an SVG logo with geometric shapes"
  - "Make a color palette and save it as CSS variables"
  - "Create a button component and show me what it looks like"

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
    status = f"""
Session Status:
  Connected:   {session.is_connected}
  Messages:    {session.message_count}
  Working Dir: {working_dir}
  Tools:       {tools_list}

Claude can create/edit files in the working directory and run shell commands.
Use /new to start fresh with a new session.
"""
    print(status)


async def run_cli():
    """
    Main CLI loop for Pygmalion with persistent session and tools.

    This creates a DesignSession that:
    - Maintains context throughout the entire interaction
    - Can create and edit files in the current working directory
    - Can run shell commands for design tools
    - Can search the web for inspiration
    """
    print_banner()

    # Use current working directory for all file operations
    working_dir = os.getcwd()

    print("Type /help for available commands, or just start designing!")
    print(f"Working directory: {working_dir}")
    print("(Claude can create files here and run design tools)\n")

    # Create a session with the working directory
    session = DesignSession(working_dir=working_dir)

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
                    command = user_input.lower().split()[0]  # Get first word

                    if command in ("/quit", "/exit", "/q"):
                        print("\nGoodbye! Happy designing!")
                        break

                    elif command in ("/help", "/h", "/?"):
                        print_help()
                        continue

                    elif command == "/status":
                        print_status(session, working_dir)
                        continue

                    elif command == "/new":
                        # Disconnect current session and create a new one
                        print("\nStarting new session...")
                        await session.disconnect()
                        session = DesignSession(working_dir=working_dir)
                        await session.connect()
                        print("✓ New session started (context cleared)\n")
                        continue

                    elif command == "/clear":
                        print("\033[2J\033[H", end="")  # ANSI clear screen
                        print_banner()
                        print(f"Working directory: {working_dir}")
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
