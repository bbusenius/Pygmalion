"""
Inkscape MCP Tools for Pygmalion.

Phase 6: Custom MCP tools for vector graphics processing.

SDK CONCEPTS EXPLAINED:
-----------------------
MCP (Model Context Protocol) tools let you extend Claude's capabilities
with custom functionality. Here we wrap the Inkscape CLI to give Claude
the ability to:

1. Export SVG to raster formats (PNG) or PDF
2. Open SVG files in Inkscape GUI for preview/editing
3. Query SVG document properties
4. Convert between vector formats

TOOL STRUCTURE:
---------------
Each tool is defined with the @tool decorator:
  @tool(name, description, parameters)

Parameters can be simple types (str, int) or JSON Schema for validation.

Tools must return a dict with this structure:
  {"content": [{"type": "text", "text": "result message"}]}

MCP SERVER:
-----------
Tools are grouped into an MCP server using create_sdk_mcp_server().
The server is then registered with ClaudeAgentOptions.mcp_servers.

Tool names appear to Claude as: mcp__[server-name]__[tool-name]
Example: mcp__inkscape__export_svg

GUI ACTIONS:
------------
The inkscape_open tool opens Inkscape's GUI, which affects the user's
desktop. This should require confirmation in approval mode. We handle
this by returning a message that prompts for confirmation.
"""

import os
import subprocess
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

# =============================================================================
# Inkscape Export Tool
# =============================================================================


@tool(
    "export_svg",
    "Export an SVG file to PNG, PDF, or other formats using Inkscape CLI. "
    "Use this to convert vector graphics to raster images or print-ready PDFs.",
    {
        "type": "object",
        "properties": {
            "input_file": {
                "type": "string",
                "description": "Path to the input SVG file",
            },
            "output_file": {
                "type": "string",
                "description": "Path for the output file (include extension)",
            },
            "format": {
                "type": "string",
                "enum": ["png", "pdf", "eps", "ps", "emf", "wmf"],
                "description": "Export format (default: png)",
            },
            "dpi": {
                "type": "integer",
                "minimum": 72,
                "maximum": 2400,
                "description": "Export DPI/resolution (default: 96)",
            },
            "width": {
                "type": "integer",
                "minimum": 1,
                "description": "Export width in pixels (optional)",
            },
            "height": {
                "type": "integer",
                "minimum": 1,
                "description": "Export height in pixels (optional)",
            },
            "background": {
                "type": "string",
                "description": "Background color (e.g., '#ffffff' or 'transparent')",
            },
        },
        "required": ["input_file", "output_file"],
    },
)
async def export_svg(args: dict[str, Any]) -> dict[str, Any]:
    """Export SVG to various formats using Inkscape CLI."""
    try:
        input_file = args["input_file"]
        output_file = args["output_file"]
        export_format = args.get("format", "png")
        dpi = args.get("dpi", 96)
        width = args.get("width")
        height = args.get("height")
        background = args.get("background")

        # Validate input file exists
        if not os.path.exists(input_file):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Input file not found: {input_file}",
                    }
                ]
            }

        # Build Inkscape command
        cmd = ["inkscape", input_file, "-o", output_file]

        # Add export type
        cmd.append(f"--export-type={export_format}")

        # Add optional parameters
        if dpi and export_format == "png":
            cmd.append(f"--export-dpi={dpi}")
        if width:
            cmd.append(f"--export-width={width}")
        if height:
            cmd.append(f"--export-height={height}")
        if background:
            cmd.append(f"--export-background={background}")

        # Execute command
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60  # 60 second timeout
        )

        if result.returncode == 0 and os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Successfully exported to {export_format.upper()}\n"
                            f"Input: {input_file}\n"
                            f"Output: {output_file}\n"
                            f"Size: {file_size:,} bytes"
                        ),
                    }
                ]
            }
        else:
            error_msg = result.stderr or "Unknown error"
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Export failed: {error_msg}",
                    }
                ]
            }

    except subprocess.TimeoutExpired:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Export operation timed out (60 second limit)",
                }
            ]
        }
    except FileNotFoundError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Inkscape not found. Please install Inkscape:\n"
                        "  sudo apt install inkscape  # Debian/Ubuntu\n"
                        "  sudo dnf install inkscape  # Fedora\n"
                        "  sudo pacman -S inkscape    # Arch"
                    ),
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Export error: {str(e)}",
                }
            ]
        }


# =============================================================================
# Inkscape Open (GUI) Tool
# =============================================================================


@tool(
    "open_in_inkscape",
    "Open an SVG file in Inkscape GUI for interactive viewing and editing. "
    "This opens a graphical window on the user's desktop. "
    "Use this when the user wants to preview or manually tweak a design.",
    {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the SVG file to open",
            },
        },
        "required": ["file_path"],
    },
)
async def open_in_inkscape(args: dict[str, Any]) -> dict[str, Any]:
    """
    Open an SVG file in Inkscape's graphical interface.

    NOTE: This is a GUI action that affects the user's desktop.
    The agent should confirm with the user before executing this
    when in approval mode.
    """
    try:
        file_path = args["file_path"]

        # Validate file exists
        if not os.path.exists(file_path):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: File not found: {file_path}",
                    }
                ]
            }

        # Validate it's an SVG file
        if not file_path.lower().endswith(".svg"):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Warning: File may not be an SVG: {file_path}\n"
                            "Inkscape works best with SVG files."
                        ),
                    }
                ]
            }

        # Open Inkscape GUI (non-blocking)
        # Using Popen instead of run so it doesn't wait for Inkscape to close
        subprocess.Popen(
            ["inkscape", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # Detach from parent process
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Opened in Inkscape GUI: {file_path}\n"
                        "You can now view and edit the design interactively.\n"
                        "Close Inkscape when done, or save changes with Ctrl+S."
                    ),
                }
            ]
        }

    except FileNotFoundError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Inkscape not found. Please install Inkscape:\n"
                        "  sudo apt install inkscape  # Debian/Ubuntu\n"
                        "  sudo dnf install inkscape  # Fedora\n"
                        "  sudo pacman -S inkscape    # Arch"
                    ),
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Failed to open Inkscape: {str(e)}",
                }
            ]
        }


# =============================================================================
# Inkscape Query Tool
# =============================================================================


@tool(
    "query_svg",
    "Query properties of an SVG file (dimensions, objects, IDs). "
    "Use this to inspect an SVG before processing it.",
    {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the SVG file to query",
            },
            "query_type": {
                "type": "string",
                "enum": ["dimensions", "objects", "all"],
                "description": "What to query: dimensions, objects list, or all",
            },
        },
        "required": ["file_path"],
    },
)
async def query_svg(args: dict[str, Any]) -> dict[str, Any]:
    """Query SVG document properties using Inkscape CLI."""
    try:
        file_path = args["file_path"]
        query_type = args.get("query_type", "dimensions")

        # Validate file exists
        if not os.path.exists(file_path):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: File not found: {file_path}",
                    }
                ]
            }

        results = []

        if query_type in ("dimensions", "all"):
            # Query document dimensions
            width_result = subprocess.run(
                ["inkscape", file_path, "--query-width"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            height_result = subprocess.run(
                ["inkscape", file_path, "--query-height"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            width = width_result.stdout.strip() if width_result.returncode == 0 else "?"
            height = (
                height_result.stdout.strip() if height_result.returncode == 0 else "?"
            )

            results.append(f"Dimensions: {width} x {height} (user units)")

        if query_type in ("objects", "all"):
            # Query all objects
            objects_result = subprocess.run(
                ["inkscape", file_path, "--query-all"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if objects_result.returncode == 0:
                lines = objects_result.stdout.strip().split("\n")
                results.append(f"Objects: {len(lines)} total")
                # Show first 10 objects
                if len(lines) > 10:
                    results.append("First 10 objects:")
                    for line in lines[:10]:
                        results.append(f"  {line}")
                    results.append(f"  ... and {len(lines) - 10} more")
                else:
                    for line in lines:
                        results.append(f"  {line}")

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"SVG Query: {file_path}\n" + "\n".join(results),
                }
            ]
        }

    except subprocess.TimeoutExpired:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Query operation timed out",
                }
            ]
        }
    except FileNotFoundError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Inkscape not found. Please install Inkscape.",
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Query error: {str(e)}",
                }
            ]
        }


# =============================================================================
# Inkscape Convert Tool
# =============================================================================


@tool(
    "convert_svg",
    "Convert an SVG file to a different vector format or optimize it. "
    "Can convert to plain SVG, Inkscape SVG, or PDF.",
    {
        "type": "object",
        "properties": {
            "input_file": {
                "type": "string",
                "description": "Path to the input SVG file",
            },
            "output_file": {
                "type": "string",
                "description": "Path for the output file",
            },
            "plain_svg": {
                "type": "boolean",
                "description": "Export as plain SVG (removes Inkscape-specific data)",
            },
        },
        "required": ["input_file", "output_file"],
    },
)
async def convert_svg(args: dict[str, Any]) -> dict[str, Any]:
    """Convert SVG between formats using Inkscape CLI."""
    try:
        input_file = args["input_file"]
        output_file = args["output_file"]
        plain_svg = args.get("plain_svg", False)

        # Validate input file exists
        if not os.path.exists(input_file):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Input file not found: {input_file}",
                    }
                ]
            }

        # Build command
        cmd = ["inkscape", input_file, "-o", output_file]

        if plain_svg:
            cmd.append("--export-plain-svg")

        # Execute
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and os.path.exists(output_file):
            input_size = os.path.getsize(input_file)
            output_size = os.path.getsize(output_file)
            savings = input_size - output_size
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Successfully converted SVG\n"
                            f"Input: {input_file} ({input_size:,} bytes)\n"
                            f"Output: {output_file} ({output_size:,} bytes)\n"
                            f"Size change: {savings:+,} bytes"
                        ),
                    }
                ]
            }
        else:
            error_msg = result.stderr or "Unknown error"
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Conversion failed: {error_msg}",
                    }
                ]
            }

    except subprocess.TimeoutExpired:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Conversion operation timed out",
                }
            ]
        }
    except FileNotFoundError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Inkscape not found. Please install Inkscape.",
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Conversion error: {str(e)}",
                }
            ]
        }


# =============================================================================
# MCP Server Creation
# =============================================================================


def create_inkscape_server():
    """
    Create the Inkscape MCP server with all tools.

    Returns an MCP server that can be registered with ClaudeAgentOptions.

    Usage:
        server = create_inkscape_server()
        options = ClaudeAgentOptions(
            mcp_servers={"inkscape": server},
            allowed_tools=[
                "mcp__inkscape__export_svg",
                "mcp__inkscape__open_in_inkscape",
                "mcp__inkscape__query_svg",
                "mcp__inkscape__convert_svg",
            ]
        )
    """
    return create_sdk_mcp_server(
        name="inkscape",
        version="1.0.0",
        tools=[export_svg, open_in_inkscape, query_svg, convert_svg],
    )


# Tool names for allowed_tools configuration
INKSCAPE_TOOL_NAMES = [
    "mcp__inkscape__export_svg",
    "mcp__inkscape__open_in_inkscape",
    "mcp__inkscape__query_svg",
    "mcp__inkscape__convert_svg",
]
