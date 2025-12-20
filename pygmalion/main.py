"""
Pygmalion CLI - Main entry point.

Phase 1: Simple CLI loop for interacting with the design agent.

This module provides a basic command-line interface for Pygmalion.
It demonstrates the fundamental pattern of:
1. Getting user input
2. Passing it to the agent
3. Displaying streamed responses

In later phases, we'll add:
- Argument parsing (Phase 11)
- Configuration file support (Phase 11)
- Session management display (Phase 2)
- Logging integration (Phase 10)
"""

import asyncio
import sys

from pygmalion.agent import run_design_query


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
  /quit     - Exit Pygmalion
  /clear    - Clear the screen

Just type your design request and press Enter to get started!

Example prompts:
  - "Create a responsive navigation bar with HTML and CSS"
  - "Design a color palette for a tech startup"
  - "Generate an SVG logo with geometric shapes"
"""
    print(help_text)


async def run_cli():
    """
    Main CLI loop for Pygmalion.

    This is a simple read-eval-print loop (REPL) that:
    1. Prompts the user for input
    2. Handles special commands (/help, /quit, etc.)
    3. Sends design requests to the agent
    4. Streams and displays responses

    The streaming approach (async for) allows us to show responses
    as they arrive rather than waiting for the complete response.
    This provides a better user experience for longer responses.
    """
    print_banner()
    print("Type /help for available commands, or just start designing!\n")

    while True:
        try:
            # Get user input
            user_input = input("\n🎨 You: ").strip()

            # Handle empty input
            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                command = user_input.lower()
                if command in ("/quit", "/exit", "/q"):
                    print("\nGoodbye! Happy designing! ✨")
                    break
                elif command in ("/help", "/h", "/?"):
                    print_help()
                    continue
                elif command == "/clear":
                    print("\033[2J\033[H", end="")  # ANSI clear screen
                    print_banner()
                    continue
                else:
                    print(f"Unknown command: {user_input}")
                    print("Type /help for available commands.")
                    continue

            # Send to agent and stream response
            print("\n🤖 Pygmalion: ", end="", flush=True)

            response_started = False
            async for text in run_design_query(user_input):
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


def main():
    """Entry point for the pygmalion command."""
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
