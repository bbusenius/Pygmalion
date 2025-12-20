"""
Core agent module for Pygmalion.

Phase 1: Basic agent using query() for one-off requests.

SDK CONCEPTS EXPLAINED:
-----------------------
The Claude Agent SDK provides two main ways to interact with Claude:

1. query() - Used here in Phase 1
   - Simple, one-off requests
   - No persistent memory between calls
   - Good for learning and simple automation
   - Returns an async generator of messages

2. ClaudeSDKClient - Coming in Phase 2
   - Maintains conversation context
   - Supports multi-turn interactions
   - Better for iterative design work
   - Requires explicit session management

The query() function is the simplest way to get started. It handles:
- Connecting to Claude
- Sending your prompt
- Streaming back responses
- Automatically retrying on transient errors

Message Types:
- AssistantMessage: Claude's text responses
- ToolUseBlock: When Claude wants to use a tool
- ToolResultBlock: Results from tool execution
- TextBlock: Plain text within a message
"""

import asyncio
from typing import AsyncIterator

# Import from claude-agent-sdk
# Note: The SDK handles tool execution automatically when tools are allowed
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKError,
    CLINotFoundError,
    ProcessError,
    TextBlock,
    query,
)

# Export error types for use in main.py and other modules
__all__ = [
    "run_design_query",
    "simple_query",
    "ClaudeSDKError",
    "CLINotFoundError",
    "ProcessError",
]


async def run_design_query(
    prompt: str, working_dir: str | None = None
) -> AsyncIterator[str]:
    """
    Run a single design query using the Claude Agent SDK.

    This is the simplest way to interact with Claude. Each call is independent -
    there's no memory of previous calls. This is fine for one-off tasks but
    we'll upgrade to ClaudeSDKClient in Phase 2 for iterative design work.

    Args:
        prompt: The design request or question
        working_dir: Optional directory for file operations

    Yields:
        Text responses from Claude

    Example:
        async for response in run_design_query("Create an HTML button"):
            print(response)
    """
    # Configure the agent options
    # For Phase 1, we're keeping it simple - no tools yet
    options = ClaudeAgentOptions(
        # Working directory for any file operations (Phase 3)
        cwd=working_dir,
        # We'll add allowed_tools in Phase 3
        # allowed_tools=["Read", "Write", "Edit", "Bash"],
    )

    # query() returns an async generator that yields messages
    # The SDK handles the connection, authentication, and message parsing
    async for message in query(prompt=prompt, options=options):
        # Check if this is an assistant message with text content
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    yield block.text


async def simple_query(prompt: str) -> str:
    """
    Convenience function that collects all responses into a single string.

    Useful for simple queries where you want the full response at once
    rather than streaming it.

    Args:
        prompt: The design request or question

    Returns:
        The complete response as a string
    """
    responses = []
    async for text in run_design_query(prompt):
        responses.append(text)
    return "\n".join(responses)


# For testing the module directly
if __name__ == "__main__":

    async def test():
        print("Testing basic query...")
        result = await simple_query("What are three key principles of good web design?")
        print(result)

    asyncio.run(test())
