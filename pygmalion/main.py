"""
Pygmalion CLI - Main entry point.

Phase 2: Multi-turn conversations with persistent sessions.

This module provides a command-line interface for Pygmalion that maintains
conversation context across multiple exchanges. Unlike Phase 1 where each
request was independent, now Claude remembers your previous requests and
can build upon earlier work.

SESSION FLOW:
-------------
    ┌──────────────────────────────────────────────────────────┐
    │  Start CLI                                               │
    │      ↓                                                   │
    │  Create DesignSession (connects to Claude)               │
    │      ↓                                                   │
    │  ┌─────────────────────────────────────────────────────┐ │
    │  │  User Input Loop                                    │ │
    │  │      ↓                                              │ │
    │  │  session.send(prompt) ← Context preserved!          │ │
    │  │      ↓                                              │ │
    │  │  Stream response                                    │ │
    │  │      ↓                                              │ │
    │  │  (repeat)                                           │ │
    │  └─────────────────────────────────────────────────────┘ │
    │      ↓                                                   │
    │  Disconnect session on exit                              │
    └──────────────────────────────────────────────────────────┘

The key difference from Phase 1:
- Phase 1: Each request was independent (no memory)
- Phase 2: All requests share context (Claude remembers)

This enables iterative design workflows like:
  "Create a header" → "Add a logo" → "Make it sticky" → "Change colors"
"""

import asyncio
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
  /status   - Show current session info
  /new      - Start a new session (clears context)
  /quit     - Exit Pygmalion
  /clear    - Clear the screen

Session Info:
  Your conversation has memory! Claude remembers previous requests
  in this session, so you can say things like:
    - "Make it blue" (referring to something you created earlier)
    - "Add a hover effect" (to the element you're working on)
    - "Now create a matching footer" (in the same style)

Example workflow:
  1. "Create a navigation bar with Home, About, Contact links"
  2. "Make it sticky at the top"
  3. "Add a dropdown menu under About"
  4. "Change the background to dark blue"
"""
    print(help_text)


def print_status(session: DesignSession):
    """Display current session information."""
    status = f"""
Session Status:
  Connected: {session.is_connected}
  Messages:  {session.message_count}

Context is preserved across all messages in this session.
Use /new to start fresh with a new session.
"""
    print(status)


async def run_cli():
    """
    Main CLI loop for Pygmalion with persistent session.

    This creates a DesignSession that maintains context throughout
    the entire interaction. Unlike Phase 1, Claude now remembers
    what you've discussed and can build upon previous work.

    The session is managed using an async context manager, which
    ensures proper cleanup (disconnection) when exiting.
    """
    print_banner()
    print("Type /help for available commands, or just start designing!")
    print("(Session memory is active - Claude remembers your conversation)\n")

    # Create a session that persists for the entire CLI interaction
    # The 'async with' ensures proper connection and cleanup
    session = DesignSession()

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
                        print_status(session)
                        continue

                    elif command == "/new":
                        # Disconnect current session and create a new one
                        print("\nStarting new session...")
                        await session.disconnect()
                        session = DesignSession()
                        await session.connect()
                        print("✓ New session started (context cleared)\n")
                        continue

                    elif command == "/clear":
                        print("\033[2J\033[H", end="")  # ANSI clear screen
                        print_banner()
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
