"""
Core agent module for Pygmalion.

Phase 3: Built-in tools for file operations and shell commands.

SDK CONCEPTS EXPLAINED:
-----------------------
The Claude Agent SDK provides two main ways to interact with Claude:

1. query() - Simple one-off requests (Phase 1)
   - No persistent memory between calls
   - Good for independent tasks
   - Returns an async generator of messages

2. ClaudeSDKClient - Persistent sessions (Phase 2)
   - Maintains conversation context across multiple exchanges
   - Claude remembers what you discussed previously
   - Essential for iterative design work where you refine outputs
   - Requires explicit connection management (connect/disconnect)

3. Built-in Tools - File & shell access (Phase 3) ← NEW
   - Claude can create, read, and edit files
   - Claude can run shell commands (Inkscape, ImageMagick, etc.)
   - Claude can search the web for design inspiration
   - Tools are enabled via the allowed_tools parameter

BUILT-IN TOOLS EXPLAINED:
-------------------------
The SDK provides these built-in tools that Claude can use:

  FILE TOOLS:
  - Read:  Read file contents from working directory
  - Write: Create new files (HTML, CSS, SVG, etc.)
  - Edit:  Make precise edits to existing files

  SHELL TOOLS:
  - Bash:  Run shell commands (inkscape, convert, git, etc.)

  SEARCH TOOLS:
  - Glob:  Find files by pattern ("*.svg", "**/*.css")
  - Grep:  Search within file contents

  WEB TOOLS:
  - WebSearch: Search the web for research/inspiration
  - WebFetch:  Fetch and parse web page content

WHY TOOLS MATTER FOR DESIGN:
----------------------------
With tools enabled, Claude can actually CREATE your designs:

  User: "Create a landing page for a coffee shop"
  Claude: [Uses Write tool to create index.html]
          [Uses Write tool to create styles.css]
          [Uses Bash to run: inkscape --export-png logo.png logo.svg]
          "I've created your landing page with..."

Without tools, Claude can only describe what to do.
With tools, Claude does the work for you.

WORKING DIRECTORY:
------------------
The working_dir parameter scopes where Claude can operate:
- All file operations are relative to this directory
- Provides safety by limiting Claude's file access
- Defaults to current directory if not specified

Message Types:
- AssistantMessage: Claude's responses containing content blocks
- TextBlock: Plain text within a message
- ToolUseBlock: When Claude wants to use a tool
- ToolResultBlock: Results from tool execution
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

    # Default tools for design work
    # These are Claude's built-in tools that we enable for the design session
    DEFAULT_TOOLS = [
        "Read",  # Read files from the working directory
        "Write",  # Create new files
        "Edit",  # Make precise edits to existing files
        "Bash",  # Run shell commands (for Inkscape, ImageMagick, etc.)
        "Glob",  # Find files by pattern (e.g., "*.svg", "**/*.css")
        "Grep",  # Search file contents
        "WebSearch",  # Search the web for design inspiration/research
        "WebFetch",  # Fetch and parse web content
    ]

    def __init__(
        self,
        working_dir: str | None = None,
        allowed_tools: list[str] | None = None,
    ):
        """
        Initialize a new design session.

        Args:
            working_dir: Directory where files will be created/modified.
                         This scopes Claude's file operations for safety.
                         Defaults to current directory if not specified.
            allowed_tools: List of tools Claude can use. Defaults to DEFAULT_TOOLS.
                          Available tools:
                          - Read: Read files
                          - Write: Create new files
                          - Edit: Modify existing files
                          - Bash: Run shell commands
                          - Glob: Find files by pattern
                          - Grep: Search file contents
                          - WebSearch: Search the web
                          - WebFetch: Fetch web pages
        """
        self._working_dir = working_dir
        self._allowed_tools = allowed_tools or self.DEFAULT_TOOLS.copy()
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

    @property
    def working_dir(self) -> str | None:
        """Get the working directory for this session."""
        return self._working_dir

    @property
    def allowed_tools(self) -> list[str]:
        """Get the list of tools enabled for this session."""
        return self._allowed_tools.copy()

    async def connect(self) -> None:
        """
        Establish the connection to Claude.

        This is called automatically when using the async context manager,
        but can be called manually if needed.

        The connection starts a Claude Code subprocess that maintains
        your conversation state. The subprocess has access to the tools
        specified in allowed_tools and operates within working_dir.
        """
        if self._is_connected:
            return

        # Configure the client options with tools
        # allowed_tools controls what Claude can do:
        # - File tools (Read/Write/Edit): Create and modify design files
        # - Bash: Run CLI tools like Inkscape, ImageMagick
        # - Search tools (Glob/Grep): Find files and content
        # - Web tools (WebSearch/WebFetch): Research and inspiration
        options = ClaudeAgentOptions(
            cwd=self._working_dir,
            allowed_tools=self._allowed_tools,
        )

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
