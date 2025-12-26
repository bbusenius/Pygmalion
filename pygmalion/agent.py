"""
Core agent module for Pygmalion.

This module provides the DesignSession class that manages persistent
conversations with Claude for iterative design work.

SDK CONCEPTS EXPLAINED:
-----------------------
The Claude Agent SDK provides two main ways to interact with Claude:

1. query() - Simple one-off requests
   - No persistent memory between calls
   - Good for independent tasks
   - Returns an async generator of messages

2. ClaudeSDKClient - Persistent sessions
   - Maintains conversation context across multiple exchanges
   - Claude remembers what you discussed previously
   - Essential for iterative design work where you refine outputs
   - Requires explicit connection management (connect/disconnect)

3. Built-in Tools - File & shell access
   - Claude can create, read, and edit files
   - Claude can run shell commands (Inkscape, ImageMagick, etc.)
   - Claude can search the web for design inspiration
   - Tools are enabled via the allowed_tools parameter

4. Permission Modes - Autonomy levels
   - Control how much Claude can do without asking permission
   - Three modes: APPROVAL, AUTO, FULL_AUTO
   - Configured via the autonomy_mode parameter

5. Skills - Specialized capabilities
   - Skills are SKILL.md files that Claude auto-invokes based on context
   - The frontend-design skill guides production-grade UI generation
   - Skills are loaded from .claude/skills/ via setting_sources
   - Requires "Skill" in allowed_tools

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

PERMISSION MODES (AUTONOMY):
----------------------------
The autonomy_mode parameter controls how much Claude can do without asking:

  APPROVAL (default) - permission_mode="default"
    Claude asks before file edits. Safest option.
    Good for: Learning, sensitive projects, reviewing changes

  AUTO - permission_mode="acceptEdits"
    Claude auto-approves file edits but asks for dangerous ops.
    Good for: Rapid prototyping, experienced users

  FULL_AUTO - permission_mode="bypassPermissions"
    No permission prompts at all. Use with caution!
    Good for: Automation, scripts, fully trusted workflows

Example:
  # Safe mode - review all changes
  session = DesignSession(autonomy_mode=AutonomyMode.APPROVAL)

  # Fast mode - auto-approve file edits
  session = DesignSession(autonomy_mode=AutonomyMode.AUTO)

Message Types:
- AssistantMessage: Claude's responses containing content blocks
- TextBlock: Plain text within a message
- ToolUseBlock: When Claude wants to use a tool
- ToolResultBlock: Results from tool execution
"""

import asyncio
import json
import os
import subprocess
from typing import AsyncIterator
import urllib.request

# Import from claude-agent-sdk
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ClaudeSDKError,
    CLINotFoundError,
    ProcessError,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

from pygmalion.utils import get_logger

# Get logger for this module
logger = get_logger(__name__)

from pygmalion.config import (
    AutonomyMode,
    get_default_autonomy_mode,
    is_figma_enabled,
    is_gemini_enabled,
    is_grok_enabled,
)
from pygmalion.tools.gemini import GEMINI_TOOL_NAMES, create_gemini_server
from pygmalion.tools.gimp import GIMP_TOOL_NAMES, create_gimp_server
from pygmalion.tools.imagemagick import (
    IMAGEMAGICK_TOOL_NAMES,
    create_imagemagick_server,
)
from pygmalion.tools.inkscape import INKSCAPE_TOOL_NAMES, create_inkscape_server
from pygmalion.tools.weasyprint import WEASYPRINT_TOOL_NAMES, create_weasyprint_server

# Export public API
__all__ = [
    # Simple query functions
    "run_design_query",
    "simple_query",
    # Persistent session class
    "DesignSession",
    # Autonomy modes
    "AutonomyMode",
    # Error types
    "ClaudeSDKError",
    "CLINotFoundError",
    "ProcessError",
]


# =============================================================================
# Simple Query Functions
# =============================================================================
# These provide one-off queries without persistent sessions.
# Kept for backwards compatibility and simple tasks.


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
# DesignSession - Persistent Claude Sessions
# =============================================================================
# This class wraps ClaudeSDKClient to provide a clean interface for
# persistent design sessions with context and tool access.


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
    DEFAULT_TOOLS = (
        [
            "Read",  # Read files from the working directory
            "Write",  # Create new files
            "Edit",  # Make precise edits to existing files
            "Bash",  # Run shell commands (for Inkscape, ImageMagick, etc.)
            "Glob",  # Find files by pattern (e.g., "*.svg", "**/*.css")
            "Grep",  # Search file contents
            "WebSearch",  # Search the web for design inspiration/research
            "WebFetch",  # Fetch and parse web content
            "Skill",  # Enable Claude Code skills (e.g., frontend-design)
        ]
        + INKSCAPE_TOOL_NAMES
        + IMAGEMAGICK_TOOL_NAMES
        + GIMP_TOOL_NAMES
        + WEASYPRINT_TOOL_NAMES
        + (
            GEMINI_TOOL_NAMES if is_gemini_enabled() else []
        )  # Optional AI image generation
        + (
            [
                "mcp__figma__get_figma_data",
                "mcp__figma__download_figma_images",
            ]
            if is_figma_enabled()
            else []
        )  # Optional Figma integration
        + (
            [
                "mcp__grok__generate_image",
                "mcp__grok__chat_with_vision",
            ]
            if is_grok_enabled()
            else []
        )  # Optional Grok integration (image gen + vision)
    )

    # Available Claude models
    # Use model aliases for convenience, SDK accepts both aliases and full IDs
    AVAILABLE_MODELS = {
        "opus": "claude-opus-4-5-20251101",
        "sonnet": "claude-sonnet-4-20250514",
        "haiku": "claude-3-5-haiku-20241022",
    }

    # Default model for high-quality design work
    # Use Claude Sonnet 4 for best balance of quality and speed
    DEFAULT_MODEL = "sonnet"

    def __init__(
        self,
        working_dir: str | None = None,
        allowed_tools: list[str] | None = None,
        autonomy_mode: AutonomyMode | None = None,
        model: str | None = None,
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
                          - Skill: Enable Claude Code skills
            autonomy_mode: How much autonomy Claude has. Defaults to APPROVAL.
                          - APPROVAL: Ask before file edits (safest)
                          - AUTO: Auto-approve file edits
                          - FULL_AUTO: No permission prompts (use with caution)
            model: Which Claude model to use. Defaults to DEFAULT_MODEL.
                   Accepts aliases (opus, sonnet, haiku) or full model IDs.
        """
        self._working_dir = working_dir
        self._allowed_tools = allowed_tools or self.DEFAULT_TOOLS.copy()
        self._autonomy_mode = autonomy_mode or get_default_autonomy_mode()

        # Resolve model alias to full model ID
        model_key = model or self.DEFAULT_MODEL
        if model_key in self.AVAILABLE_MODELS:
            self._model = self.AVAILABLE_MODELS[model_key]
            self._model_alias = model_key
        else:
            # Assume it's a full model ID
            self._model = model_key
            # Try to find alias for display
            self._model_alias = next(
                (k for k, v in self.AVAILABLE_MODELS.items() if v == model_key),
                model_key
            )
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

    @property
    def autonomy_mode(self) -> AutonomyMode:
        """Get the autonomy mode for this session."""
        return self._autonomy_mode

    @property
    def model(self) -> str:
        """Get the model being used for this session."""
        return self._model

    @property
    def model_alias(self) -> str:
        """Get the model alias (opus, sonnet, haiku) or full ID if no alias."""
        return self._model_alias

    @classmethod
    def get_available_models(cls) -> dict[str, str]:
        """Get available models and their full IDs."""
        return cls.AVAILABLE_MODELS.copy()

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
            logger.debug("Already connected, skipping connection")
            return

        logger.info("Connecting to Claude SDK...")

        # Set output directory in environment for MCP tools to use
        # SDK MCP servers run in the same Python process and can access this
        os.environ["PYGMALION_OUTPUT_DIR"] = self._working_dir
        logger.debug(f"Set PYGMALION_OUTPUT_DIR={self._working_dir}")

        # Create MCP servers for custom tools
        # MCP servers extend Claude with custom functionality
        inkscape_server = create_inkscape_server()
        imagemagick_server = create_imagemagick_server()
        gimp_server = create_gimp_server()
        weasyprint_server = create_weasyprint_server()

        # Conditionally create Gemini server if enabled
        # Gemini requires GEMINI_API_KEY and PYGMALION_GEMINI_ENABLED=true
        gemini_server = create_gemini_server() if is_gemini_enabled() else None

        # Configure the client options with tools, permissions, and skills
        #
        # allowed_tools controls what Claude can do:
        # - File tools (Read/Write/Edit): Create and modify design files
        # - Bash: Run CLI tools like Inkscape, ImageMagick
        # - Search tools (Glob/Grep): Find files and content
        # - Web tools (WebSearch/WebFetch): Research and inspiration
        # - Skill: Enable Claude Code skills (loaded from .claude/skills/)
        # - MCP tools (mcp__inkscape__*): Custom Inkscape operations
        #
        # permission_mode controls autonomy:
        # - "default": Ask before file edits (APPROVAL mode)
        # - "acceptEdits": Auto-approve file changes (AUTO mode)
        # - "bypassPermissions": No prompts at all (FULL_AUTO mode)
        #
        # setting_sources enables skill loading:
        # - "user": Load skills from ~/.claude/skills/
        # - "project": Load skills from .claude/skills/ in working directory
        #
        # mcp_servers registers custom MCP tool servers
        #
        # model selects which Claude model to use for high-quality output

        # Build MCP servers dict
        mcp_servers = {
            "inkscape": inkscape_server,
            "imagemagick": imagemagick_server,
            "gimp": gimp_server,
            "weasyprint": weasyprint_server,
        }
        # Add Gemini if enabled
        if gemini_server:
            mcp_servers["gemini"] = gemini_server

        # Add Figma MCP server if enabled
        # Figma is an external MCP server (runs as separate Node.js process)
        if is_figma_enabled():
            figma_token = os.environ.get("FIGMA_ACCESS_TOKEN", "")
            mcp_servers["figma"] = {
                "command": "npx",
                "args": [
                    "-y",
                    "figma-developer-mcp",
                    "--figma-api-key",
                    figma_token,
                    "--stdio",
                ],
            }

        # Add Grok MCP server if enabled
        # Grok is an external MCP server (runs as separate Python process via UV)
        if is_grok_enabled():
            grok_path = os.environ.get("GROK_MCP_PATH", "")
            mcp_servers["grok"] = {
                "command": "uv",
                "args": ["--directory", grok_path, "run", "python", "main.py"],
                "env": {"XAI_API_KEY": os.environ.get("XAI_API_KEY", "")},
            }

        # Custom system prompt additions for Pygmalion
        system_prompt = f"""
# File Creation and Path Reporting

CRITICAL: When you create, edit, or save any files, you MUST always report:
1. The filename
2. The complete absolute path where the file was created

The current output directory is: {self._working_dir}

Examples:
- "I've created index.html at /home/user/project/index.html"
- "I've saved logo.svg at /home/user/project/assets/logo.svg"
- "I've updated styles.css at /home/user/project/css/styles.css"

Never say just "I created index.html" - always include the full path.
"""

        options = ClaudeAgentOptions(
            cwd=self._working_dir,
            allowed_tools=self._allowed_tools,
            permission_mode=self._autonomy_mode.value,
            setting_sources=["user", "project"],
            mcp_servers=mcp_servers,
            model=self._model,
            system_prompt=system_prompt,
        )

        # Create and connect the client
        logger.debug(
            f"Creating SDK client with model={self._model}, tools={len(self._allowed_tools)}"
        )
        self._client = ClaudeSDKClient(options=options)
        await self._client.connect()
        self._is_connected = True
        logger.info("Successfully connected to Claude SDK")

    async def disconnect(self) -> None:
        """
        Close the connection to Claude.

        This is called automatically when exiting the async context manager.
        After disconnecting, you can no longer send messages in this session.
        """
        if self._client and self._is_connected:
            logger.info(f"Disconnecting session (messages sent: {self._message_count})")
            await self._client.disconnect()
            self._is_connected = False
            logger.debug("Disconnected successfully")

    def _auto_open_file(self, file_path: str) -> None:
        """
        Automatically open a file based on its extension.

        SVG files -> Inkscape
        Image files -> GIMP
        HTML files -> Default browser (xdg-open)

        Args:
            file_path: Absolute path to the file to open
        """
        if not os.path.exists(file_path):
            logger.debug(f"File does not exist, skipping auto-open: {file_path}")
            return

        # Get file extension
        _, ext = os.path.splitext(file_path.lower())

        try:
            if ext == ".svg":
                logger.info(f"Auto-opening SVG in Inkscape: {file_path}")
                subprocess.Popen(
                    ["inkscape", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
                logger.info(f"Auto-opening image in GIMP: {file_path}")
                subprocess.Popen(
                    ["gimp", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif ext in [".html", ".htm"]:
                logger.info(f"Auto-opening HTML in browser: {file_path}")
                subprocess.Popen(
                    ["xdg-open", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                logger.debug(f"No auto-open handler for extension: {ext}")
        except FileNotFoundError as e:
            logger.warning(f"Failed to auto-open {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error auto-opening {file_path}: {e}")

    async def send(self, prompt: str) -> AsyncIterator[tuple[str, str]]:
        """
        Send a message to Claude and stream the response.

        This is the main method for interacting with the design session.
        Each call maintains context from previous exchanges.

        Files created during the session (SVG, images, HTML) are automatically
        opened in the appropriate application.

        Args:
            prompt: Your design request or follow-up instruction

        Yields:
            Tuples of (message_type, content) where:
            - ("text", text_chunk) for Claude's text responses
            - ("tool_use", tool_name) when Claude starts using a tool
            - ("tool_result", "") when a tool completes

        Raises:
            RuntimeError: If the session is not connected

        Example:
            async for msg_type, content in session.send("Create a blue button"):
                if msg_type == "text":
                    print(content, end="", flush=True)
                elif msg_type == "tool_use":
                    print(f"[Using {content}...]")
        """
        if not self._is_connected or not self._client:
            raise RuntimeError(
                "Session not connected. Use 'async with DesignSession()' "
                "or call connect() first."
            )

        # Track files created during this interaction for auto-opening
        created_files = []
        # Track the last tool used (for handling results)
        last_tool_used = None

        # Send the prompt to Claude
        await self._client.query(prompt)
        self._message_count += 1

        # Stream the response
        # receive_response() yields messages and completes when the response is done
        async for message in self._client.receive_response():
            logger.debug(f"Received message type: {type(message).__name__}")
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield ("text", block.text)
                    elif isinstance(block, ToolUseBlock):
                        # Notify that a tool is being used
                        tool_name = block.name
                        last_tool_used = tool_name  # Track for result handling
                        logger.debug(f"ToolUseBlock detected: {tool_name}")
                        yield ("tool_use", tool_name)

                        # Track file creations for auto-opening
                        # Check if this is a file-creation tool
                        if tool_name == "Write":
                            # Write tool creates new files
                            file_path = block.input.get("file_path")
                            if file_path:
                                # Convert to absolute path
                                abs_path = os.path.abspath(
                                    os.path.join(self._working_dir, file_path)
                                )
                                created_files.append(abs_path)
                                logger.debug(f"Tracking file creation: {abs_path}")
                        elif tool_name == "Edit":
                            # Edit can create new files if they don't exist
                            file_path = block.input.get("file_path")
                            if file_path:
                                abs_path = os.path.abspath(
                                    os.path.join(self._working_dir, file_path)
                                )
                                # Only track if it's being created for the first time
                                if not os.path.exists(abs_path):
                                    created_files.append(abs_path)
                                    logger.debug(f"Tracking file creation: {abs_path}")
                        elif tool_name == "mcp__gemini__gemini_generate_image":
                            # Gemini image generation creates PNG files
                            file_path = block.input.get("output_file")
                            if file_path:
                                # Gemini paths are already absolute or relative to cwd
                                abs_path = os.path.abspath(
                                    os.path.join(self._working_dir, file_path)
                                )
                                created_files.append(abs_path)
                                logger.debug(f"Tracking Gemini image creation: {abs_path}")
                        elif tool_name.startswith("mcp__inkscape__"):
                            # Inkscape tools that might create files
                            # Check for common output parameters
                            for param in ["output_file", "output_path", "file_path"]:
                                file_path = block.input.get(param)
                                if file_path:
                                    abs_path = os.path.abspath(
                                        os.path.join(self._working_dir, file_path)
                                    )
                                    created_files.append(abs_path)
                                    logger.debug(f"Tracking Inkscape file creation: {abs_path}")
                                    break
                        elif tool_name.startswith("mcp__imagemagick__") or tool_name.startswith("mcp__gimp__"):
                            # ImageMagick/GIMP tools that might create files
                            for param in ["output_file", "output_path", "file_path"]:
                                file_path = block.input.get(param)
                                if file_path:
                                    abs_path = os.path.abspath(
                                        os.path.join(self._working_dir, file_path)
                                    )
                                    created_files.append(abs_path)
                                    logger.debug(f"Tracking image file creation: {abs_path}")
                                    break
                    else:
                        logger.debug(f"Unknown block type: {type(block).__name__}")
            elif isinstance(message, UserMessage):
                # Handle tool results for special cases like Grok image generation
                if last_tool_used == "mcp__grok__generate_image":
                    # Grok returns image URLs that need to be downloaded
                    for block in message.content:
                        if isinstance(block, ToolResultBlock):
                            try:
                                # SDK returns MCP content format: [{"type": "text", "text": "..."}]
                                result_data = {}
                                for item in block.content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        result_data = json.loads(item.get("text", ""))
                                        break
                                images = result_data.get("images", [])

                                # Download each image
                                for idx, img in enumerate(images):
                                    url = img.get("url")
                                    if url:
                                        # Generate filename with extension from URL
                                        ext = os.path.splitext(url)[1]
                                        filename = f"grok_image_{idx + 1}{ext}"
                                        file_path = os.path.join(self._working_dir, filename)

                                        # Download the image with browser-like headers
                                        logger.debug(f"Downloading Grok image from {url}")
                                        req = urllib.request.Request(
                                            url,
                                            headers={
                                                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                                            }
                                        )
                                        with urllib.request.urlopen(req) as response:
                                            with open(file_path, "wb") as f:
                                                f.write(response.read())

                                        # Track for auto-opening
                                        created_files.append(file_path)
                                        logger.debug(f"Downloaded Grok image to {file_path}")
                            except (json.JSONDecodeError, KeyError, Exception) as e:
                                logger.error(f"Failed to download Grok image: {e}")

        # After response is complete, auto-open created files
        for file_path in created_files:
            self._auto_open_file(file_path)

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
        """Test simple one-off query."""
        print("=== Testing one-off query ===")
        result = await simple_query("What is the most important rule of web design?")
        print(result)
        print()

    async def test_session():
        """Test persistent session."""
        print("=== Testing persistent session ===")
        async with DesignSession() as session:
            print(f"Session connected: {session.is_connected}")

            # First message
            print("\n[User]: Describe a simple HTML button in one sentence.")
            print("[Claude]: ", end="")
            async for msg_type, content in session.send(
                "Describe a simple HTML button in one sentence."
            ):
                if msg_type == "text":
                    print(content, end="", flush=True)
            print(f"\n(Messages: {session.message_count})")

            # Follow-up - Claude should understand "it" refers to the button
            print("\n[User]: How would you style it with CSS?")
            print("[Claude]: ", end="")
            async for msg_type, content in session.send(
                "How would you style it with CSS?"
            ):
                if msg_type == "text":
                    print(content, end="", flush=True)
            print(f"\n(Messages: {session.message_count})")

    async def main():
        await test_one_off()
        await test_session()

    asyncio.run(main())
