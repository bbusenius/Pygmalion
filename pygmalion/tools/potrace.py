"""
Potrace MCP Tools for Pygmalion.

Custom MCP tools for bitmap tracing (raster to vector conversion).

SDK CONCEPTS EXPLAINED:
-----------------------
Potrace is a tool for tracing bitmaps into smooth, scalable vector graphics.
This tool wraps the Potrace CLI to enable bitmap-to-SVG conversion for logos,
icons, and illustrations.

WHEN TO USE POTRACE:
-------------------
Use Potrace for:
- Converting bitmap logos/icons to scalable SVG format
- Tracing hand-drawn sketches or scanned artwork
- Creating vector versions of raster graphics
- Logo design workflows (generate bitmap → trace to vector)

WORKFLOW:
---------
1. Input: Any raster image (PNG, JPG, BMP, etc.)
2. Convert to BMP format using ImageMagick (Potrace requirement)
3. Trace bitmap to SVG using Potrace
4. Optimize viewBox with Inkscape --export-area-drawing (if tight_bounds=true)
5. Clean up temporary files
6. Return SVG path

REQUIREMENTS:
-------------
- potrace: Bitmap tracing tool (apt install potrace)
- ImageMagick: Image format conversion (apt install imagemagick)
- Inkscape: Optional, for viewBox optimization (apt install inkscape)

If not installed, the tool provides clear installation instructions.
Without Inkscape, traced SVGs will have large viewBox with excess whitespace.

POTRACE OPTIONS:
----------------
- Turnpolicy: How to resolve ambiguities in path extraction
- Turdsize: Suppress speckles of this size (default: 2)
- Alphamax: Corner threshold parameter (default: 1.0)
- Opticurve: Curve optimization (default: enabled)
- Opttolerance: Curve optimization tolerance (default: 0.2)
"""

import os
import shutil
import subprocess
import tempfile
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool


# =============================================================================
# Potrace Bitmap Tracing Tool
# =============================================================================


@tool(
    "trace_bitmap",
    "Trace a bitmap image (PNG, JPG, BMP, etc.) to SVG vector format using Potrace. "
    "Converts raster graphics into smooth, scalable vector paths. Useful for "
    "converting logos, icons, illustrations, and hand-drawn artwork to SVG. "
    "Requires potrace and ImageMagick installed.",
    {
        "type": "object",
        "properties": {
            "input_file": {
                "type": "string",
                "description": "Path to the input bitmap image (PNG, JPG, BMP, etc.)",
            },
            "output_file": {
                "type": "string",
                "description": "Path where the SVG output should be saved (e.g., 'traced.svg'). "
                "Must end with .svg extension.",
            },
            "turdsize": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Suppress speckles of this many pixels (default: 2). "
                "Higher values remove more small artifacts.",
            },
            "turnpolicy": {
                "type": "string",
                "enum": ["black", "white", "left", "right", "minority", "majority"],
                "description": "How to resolve ambiguities in path extraction (default: minority). "
                "black: prefer black, white: prefer white, minority/majority: prefer minority/majority color.",
            },
            "alphamax": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.34,
                "description": "Corner threshold (default: 1.0). Lower values = sharper corners, "
                "higher values = smoother curves.",
            },
            "opttolerance": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Curve optimization tolerance (default: 0.2). "
                "Higher values = smoother but less accurate curves.",
            },
            "tight_bounds": {
                "type": "boolean",
                "description": "Optimize viewBox to tightly fit content using Inkscape (default: true). "
                "Removes excess whitespace from traced output. Requires Inkscape installed.",
            },
        },
        "required": ["input_file", "output_file"],
    },
)
async def trace_bitmap(args: dict[str, Any]) -> dict[str, Any]:
    """Trace a bitmap image to SVG using Potrace."""
    input_file = args["input_file"]
    output_file = args["output_file"]
    turdsize = args.get("turdsize", 2)
    turnpolicy = args.get("turnpolicy", "minority")
    alphamax = args.get("alphamax", 1.0)
    opttolerance = args.get("opttolerance", 0.2)
    tight_bounds = args.get("tight_bounds", True)

    # Validate output file extension
    if not output_file.lower().endswith(".svg"):
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Error: output_file must end with .svg extension",
                }
            ]
        }

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

    # Check for required tools
    if not shutil.which("potrace"):
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Potrace not found. Install it with:\n"
                        "  Ubuntu/Debian: sudo apt install potrace\n"
                        "  macOS: brew install potrace\n"
                        "  Arch: sudo pacman -S potrace"
                    ),
                }
            ]
        }

    if not shutil.which("convert"):
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "ImageMagick not found. Install it with:\n"
                        "  Ubuntu/Debian: sudo apt install imagemagick\n"
                        "  macOS: brew install imagemagick\n"
                        "  Arch: sudo pacman -S imagemagick"
                    ),
                }
            ]
        }

    try:
        # Create temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Convert input to BMP format (Potrace requirement)
            bmp_file = os.path.join(tmpdir, "input.bmp")

            # Convert to BMP using ImageMagick
            convert_cmd = ["convert", input_file, bmp_file]
            convert_result = subprocess.run(
                convert_cmd, capture_output=True, text=True, timeout=30
            )

            if convert_result.returncode != 0:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"ImageMagick conversion failed.\n"
                                f"Error: {convert_result.stderr}\n"
                                f"Command: {' '.join(convert_cmd)}"
                            ),
                        }
                    ]
                }

            # Build potrace command
            potrace_cmd = [
                "potrace",
                "--svg",  # Output format
                "-o",
                output_file,
                "--turdsize",
                str(turdsize),
                "--turnpolicy",
                turnpolicy,
                "--alphamax",
                str(alphamax),
                "--opttolerance",
                str(opttolerance),
                bmp_file,
            ]

            # Run potrace
            potrace_result = subprocess.run(
                potrace_cmd, capture_output=True, text=True, timeout=60
            )

            if potrace_result.returncode != 0:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Potrace tracing failed.\n"
                                f"Error: {potrace_result.stderr}\n"
                                f"Command: {' '.join(potrace_cmd)}"
                            ),
                        }
                    ]
                }

            # Check if output was created
            if os.path.exists(output_file):
                # Optimize viewBox with Inkscape if requested
                if tight_bounds:
                    if shutil.which("inkscape"):
                        # Create temporary file for optimized output
                        temp_svg = os.path.join(tmpdir, "optimized.svg")

                        inkscape_cmd = [
                            "inkscape",
                            output_file,
                            "--export-area-drawing",
                            "--export-plain-svg",
                            f"--export-filename={temp_svg}",
                        ]

                        inkscape_result = subprocess.run(
                            inkscape_cmd,
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )

                        if inkscape_result.returncode == 0 and os.path.exists(temp_svg):
                            # Replace original with optimized version
                            shutil.copy(temp_svg, output_file)
                            optimization_msg = " (viewBox optimized)"
                        else:
                            optimization_msg = " (viewBox optimization failed, using original)"
                    else:
                        optimization_msg = " (Inkscape not found, skipping viewBox optimization)"
                else:
                    optimization_msg = ""

                file_size = os.path.getsize(output_file)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Successfully traced bitmap to SVG{optimization_msg}\n"
                                f"Input: {input_file}\n"
                                f"Output: {output_file} ({file_size:,} bytes)\n"
                                f"Settings: turdsize={turdsize}, turnpolicy={turnpolicy}, "
                                f"alphamax={alphamax}, opttolerance={opttolerance}"
                            ),
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Potrace completed but output file was not created",
                        }
                    ]
                }

    except subprocess.TimeoutExpired:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Tracing timeout exceeded (60 seconds). Try a smaller image or simpler settings.",
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Bitmap tracing error: {str(e)}",
                }
            ]
        }


# =============================================================================
# MCP Server Creation
# =============================================================================


def create_potrace_server():
    """
    Create the Potrace MCP server with bitmap tracing tools.

    Returns an MCP server that can be conditionally registered with
    ClaudeAgentOptions based on configuration.

    Usage:
        server = create_potrace_server()
        options = ClaudeAgentOptions(
            mcp_servers={"potrace": server},
            allowed_tools=POTRACE_TOOL_NAMES
        )
    """
    return create_sdk_mcp_server(
        name="potrace",
        version="1.0.0",
        tools=[trace_bitmap],
    )


# Tool names for allowed_tools configuration
POTRACE_TOOL_NAMES = [
    "mcp__potrace__trace_bitmap",
]
