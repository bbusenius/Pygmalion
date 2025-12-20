"""
Core agent module for Pygmalion.

Phase 2: Persistent sessions with ClaudeSDKClient.

SDK CONCEPTS EXPLAINED:
-----------------------
The Claude Agent SDK provides two main ways to interact with Claude:

1. query() - Simple one-off requests (Phase 1)
   - No persistent memory between calls
   - Good for independent tasks
   - Returns an async generator of messages

2. ClaudeSDKClient - Persistent sessions (Phase 2) ← NEW
   - Maintains conversation context across multiple exchanges
   - Claude remembers what you discussed previously
   - Essential for iterative design work where you refine outputs
   - Requires explicit connection management (connect/disconnect)

WHY PERSISTENT SESSIONS MATTER FOR DESIGN:
------------------------------------------
Design is inherently iterative. You might say:
  1. "Create a navigation bar"
  2. "Make it sticky"
  3. "Add a dropdown for the Products menu"
  4. "Change the color scheme to dark mode"

With query(), each request starts fresh - Claude wouldn't know what
"navigation bar" you're referring to in request #2.

With ClaudeSDKClient, Claude maintains context:
  - Remembers the code it generated
  - Understands references to previous elements
  - Can build upon and modify earlier work

HOW CONTEXT FLOWS:
------------------
                    ┌─────────────────┐
  User: "Create     │  ClaudeSDK      │
  a nav bar"  ───▶  │  Client         │ ───▶ Claude generates nav HTML
                    │                 │
  User: "Make it    │  (maintains     │
  sticky"     ───▶  │   context)      │ ───▶ Claude modifies the SAME nav
                    │                 │
  User: "Add        │  Session ID:    │
  dropdown"   ───▶  │  abc123...      │ ───▶ Claude adds to the SAME nav
                    └─────────────────┘

The session ID identifies your conversation. You can even resume
sessions later if you save the ID.

Message Types (same as Phase 1):
- AssistantMessage: Claude's responses containing content blocks
- TextBlock: Plain text within a message
- ToolUseBlock: When Claude wants to use a tool (Phase 3)
- ToolResultBlock: Results from tool execution (Phase 3)
"""

import asyncio
from typing import AsyncIterator

# Import from claude-agent-sdk
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ClaudeSDKError,
    CLINotFoundError,
    ProcessError,
    TextBlock,
    query,
)

# Export public API
__all__ = [
    # Phase 1: One-off queries
    "run_design_query",
    "simple_query",
    # Phase 2: Persistent sessions
    "DesignSession",
    # Error types
    "ClaudeSDKError",
    "CLINotFoundError",
    "ProcessError",
]


# =============================================================================
# Phase 1: One-off queries (kept for backwards compatibility and simple tasks)
# =============================================================================


async def run_design_query(
    prompt: str, working_dir: str | None = None
) -> AsyncIterator[str]:
    """
    Run a single design query using the Claude Agent SDK.

    This is the simplest way to interact with Claude. Each call is independent -
    there's no memory of previous calls. Use DesignSession for iterative work.

    Args:
        prompt: The design request or question
        working_dir: Optional directory for file operations

    Yields:
        Text responses from Claude
    """
    options = ClaudeAgentOptions(cwd=working_dir)

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    yield block.text


async def simple_query(prompt: str) -> str:
    """
    Convenience function that collects all responses into a single string.

    Args:
        prompt: The design request or question

    Returns:
        The complete response as a string
    """
    responses = []
    async for text in run_design_query(prompt):
        responses.append(text)
    return "\n".join(responses)


# =============================================================================
# Phase 2: Persistent sessions with ClaudeSDKClient
# =============================================================================


class DesignSession:
    """
    A persistent design session that maintains context across multiple exchanges.

    This class wraps ClaudeSDKClient to provide a clean interface for
    multi-turn design conversations. Claude will remember previous requests
    and can build upon earlier work.

    Usage:
        async with DesignSession() as session:
            # First request
            async for text in session.send("Create a navigation bar"):
                print(text)

            # Follow-up - Claude remembers the nav bar
            async for text in session.send("Make it sticky"):
                print(text)

            # Another follow-up
            async for text in session.send("Add a logo on the left"):
                print(text)

    Attributes:
        session_id: Unique identifier for this conversation (can be used to resume)
        is_connected: Whether the session is currently active
        message_count: Number of exchanges in this session

    Why use this instead of query()?
        - Claude remembers context between messages
        - You can refine designs iteratively
        - References like "make IT blue" work because Claude knows what "it" is
    """

    def __init__(self, working_dir: str | None = None):
        """
        Initialize a new design session.

        Args:
            working_dir: Directory where files will be created/modified.
                         This scopes Claude's file operations for safety.
        """
        self._working_dir = working_dir
        self._client: ClaudeSDKClient | None = None
        self._session_id: str | None = None
        self._message_count = 0
        self._is_connected = False

    @property
    def session_id(self) -> str | None:
        """Get the session ID (available after first message exchange)."""
        return self._session_id

    @property
    def is_connected(self) -> bool:
        """Check if the session is currently connected."""
        return self._is_connected

    @property
    def message_count(self) -> int:
        """Get the number of user messages sent in this session."""
        return self._message_count

    async def connect(self) -> None:
        """
        Establish the connection to Claude.

        This is called automatically when using the async context manager,
        but can be called manually if needed.

        The connection starts a Claude Code subprocess that maintains
        your conversation state.
        """
        if self._is_connected:
            return

        # Configure the client options
        # We'll add more options in later phases (tools, permissions, etc.)
        options = ClaudeAgentOptions(cwd=self._working_dir)

        # Create and connect the client
        self._client = ClaudeSDKClient(options=options)
        await self._client.connect()
        self._is_connected = True

    async def disconnect(self) -> None:
        """
        Close the connection to Claude.

        This is called automatically when exiting the async context manager.
        After disconnecting, you can no longer send messages in this session.
        """
        if self._client and self._is_connected:
            await self._client.disconnect()
            self._is_connected = False

    async def send(self, prompt: str) -> AsyncIterator[str]:
        """
        Send a message to Claude and stream the response.

        This is the main method for interacting with the design session.
        Each call maintains context from previous exchanges.

        Args:
            prompt: Your design request or follow-up instruction

        Yields:
            Text chunks from Claude's response (streams as they arrive)

        Raises:
            RuntimeError: If the session is not connected

        Example:
            async for text in session.send("Create a blue button"):
                print(text, end="", flush=True)
        """
        if not self._is_connected or not self._client:
            raise RuntimeError(
                "Session not connected. Use 'async with DesignSession()' "
                "or call connect() first."
            )

        # Send the prompt to Claude
        await self._client.query(prompt)
        self._message_count += 1

        # Stream the response
        # receive_response() yields messages and completes when the response is done
        async for message in self._client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield block.text

    async def __aenter__(self) -> "DesignSession":
        """Async context manager entry - connects the session."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - disconnects the session."""
        await self.disconnect()


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":

    async def test_one_off():
        """Test Phase 1 one-off query."""
        print("=== Testing one-off query ===")
        result = await simple_query("What is the most important rule of web design?")
        print(result)
        print()

    async def test_session():
        """Test Phase 2 persistent session."""
        print("=== Testing persistent session ===")
        async with DesignSession() as session:
            print(f"Session connected: {session.is_connected}")

            # First message
            print("\n[User]: Describe a simple HTML button in one sentence.")
            print("[Claude]: ", end="")
            async for text in session.send(
                "Describe a simple HTML button in one sentence."
            ):
                print(text, end="", flush=True)
            print(f"\n(Messages: {session.message_count})")

            # Follow-up - Claude should understand "it" refers to the button
            print("\n[User]: How would you style it with CSS?")
            print("[Claude]: ", end="")
            async for text in session.send("How would you style it with CSS?"):
                print(text, end="", flush=True)
            print(f"\n(Messages: {session.message_count})")

    async def main():
        await test_one_off()
        await test_session()

    asyncio.run(main())
