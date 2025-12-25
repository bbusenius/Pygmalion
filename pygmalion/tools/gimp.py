"""
GIMP MCP Tools for Pygmalion.

Custom MCP tools for advanced raster editing.

SDK CONCEPTS EXPLAINED:
-----------------------
GIMP provides capabilities beyond ImageMagick for complex editing tasks:
- Advanced layer compositing with blend modes
- Complex filters and effects
- Text rendering with full font support
- Path-based selections and masks

WHEN TO USE GIMP VS IMAGEMAGICK:
--------------------------------
Use ImageMagick for:
- Simple resize, convert, crop operations
- Basic effects (blur, sharpen, brightness)
- Batch processing of many files
- Quick transformations

Use GIMP for:
- Complex multi-layer compositions
- Advanced text effects
- Precise selections and masking
- Filter combinations not available in ImageMagick
- When you need Script-Fu or Python-Fu automation

GIMP BATCH MODE:
----------------
GIMP can run headlessly using Script-Fu:
  gimp -i -b '(script-fu-command args)' -b '(gimp-quit 0)'

Or using Python-Fu with a script file:
  gimp -i -b 'python-fu-eval -s "python code"' -b '(gimp-quit 0)'

The -i flag runs GIMP without a GUI (batch mode).
"""

import os
import subprocess
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

# =============================================================================
# Helper Functions (not decorated, can be called internally)
# =============================================================================


def _get_save_command(output_file: str, quality: float = 0.9) -> str:
    """Get the appropriate GIMP save command for the output format."""
    output_ext = os.path.splitext(output_file)[1].lower()

    if output_ext in (".jpg", ".jpeg"):
        return (
            f"(file-jpeg-save RUN-NONINTERACTIVE image "
            f"(car (gimp-image-get-active-layer image)) "
            f'"{output_file}" "{output_file}" {quality} 0 0 0 "" 0 0 0 0)'
        )
    elif output_ext == ".png":
        return (
            f"(file-png-save RUN-NONINTERACTIVE image "
            f"(car (gimp-image-get-active-layer image)) "
            f'"{output_file}" "{output_file}" 0 9 1 1 1 1 1)'
        )
    elif output_ext == ".gif":
        return (
            f"(file-gif-save RUN-NONINTERACTIVE image "
            f"(car (gimp-image-get-active-layer image)) "
            f'"{output_file}" "{output_file}" 0 0 0 0)'
        )
    elif output_ext == ".tiff":
        return (
            f"(file-tiff-save RUN-NONINTERACTIVE image "
            f"(car (gimp-image-get-active-layer image)) "
            f'"{output_file}" "{output_file}" 0)'
        )
    else:
        return (
            f"(gimp-file-save RUN-NONINTERACTIVE image "
            f"(car (gimp-image-get-active-layer image)) "
            f'"{output_file}" "{output_file}")'
        )


def _run_gimp_batch(batch_script: str, timeout: int = 120) -> dict[str, Any]:
    """Run a GIMP batch script and return the result."""
    # Run GIMP in batch mode
    # Note: We don't use -d or -f flags because:
    # - -d disables data files which some plugins need
    # - -f disables fonts which breaks text rendering
    cmd = [
        "gimp",
        "-i",  # No interface (batch mode)
        "-b",
        batch_script,
        "-b",
        "(gimp-quit 0)",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"success": True, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "GIMP operation timed out"}
    except FileNotFoundError:
        return {
            "success": False,
            "error": (
                "GIMP not found. Please install GIMP:\n"
                "  sudo apt install gimp  # Debian/Ubuntu\n"
                "  sudo dnf install gimp  # Fedora\n"
                "  sudo pacman -S gimp    # Arch"
            ),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_gimp_script(
    input_file: str, output_file: str, script: str, flatten: bool = True
) -> dict[str, Any]:
    """
    Execute a GIMP Script-Fu command - internal helper function.

    This is the core logic that can be called by multiple MCP tools.
    """
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

    # Get the appropriate save command for the output format
    save_cmd = _get_save_command(output_file)
    flatten_cmd = "(gimp-image-flatten image)" if flatten else ""

    # Build the complete Script-Fu batch command
    batch_script = f"""
(let* (
    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_file}" "{input_file}")))
    (drawable (car (gimp-image-get-active-layer image)))
)
    {script}
    {flatten_cmd}
    {save_cmd}
    (gimp-image-delete image)
)
"""

    result = _run_gimp_batch(batch_script)

    if not result["success"]:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"GIMP script failed: {result['error']}",
                }
            ]
        }

    if os.path.exists(output_file):
        output_size = os.path.getsize(output_file)
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Successfully executed GIMP script\n"
                        f"Input: {input_file}\n"
                        f"Output: {output_file} ({output_size:,} bytes)"
                    ),
                }
            ]
        }
    else:
        error_msg = result.get("stderr", "") or result.get("stdout", "Unknown error")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"GIMP script failed: {error_msg}",
                }
            ]
        }


# =============================================================================
# Open in GIMP Tool
# =============================================================================


@tool(
    "open_in_gimp",
    "Open an image file in GIMP's graphical interface for manual editing. "
    "Use this when the user wants to visually edit an image or when batch "
    "processing isn't sufficient.",
    {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the image file to open",
            },
        },
        "required": ["file_path"],
    },
)
async def open_in_gimp(args: dict[str, Any]) -> dict[str, Any]:
    """Open an image in GIMP's GUI."""
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

        # Open GIMP with the file (non-blocking)
        subprocess.Popen(
            ["gimp", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Opened {file_path} in GIMP",
                }
            ]
        }

    except FileNotFoundError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "GIMP not found. Please install GIMP:\n"
                        "  sudo apt install gimp  # Debian/Ubuntu\n"
                        "  sudo dnf install gimp  # Fedora\n"
                        "  sudo pacman -S gimp    # Arch"
                    ),
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error opening GIMP: {str(e)}",
                }
            ]
        }


# =============================================================================
# GIMP Batch Command Tool
# =============================================================================


@tool(
    "gimp_script",
    "Execute a GIMP Script-Fu command in batch mode. Use this for complex "
    "image operations that require GIMP's advanced capabilities. "
    "Common operations: applying filters, text rendering, layer operations.",
    {
        "type": "object",
        "properties": {
            "input_file": {
                "type": "string",
                "description": "Path to the input image file",
            },
            "output_file": {
                "type": "string",
                "description": "Path for the output image file",
            },
            "script": {
                "type": "string",
                "description": (
                    "Script-Fu commands to execute. Use 'image' for the loaded image "
                    "and 'drawable' for the active layer. Example: "
                    "'(gimp-desaturate-full drawable DESATURATE-LUMINOSITY)'"
                ),
            },
            "flatten": {
                "type": "boolean",
                "description": "Flatten all layers before saving (default true)",
            },
        },
        "required": ["input_file", "output_file", "script"],
    },
)
async def gimp_script(args: dict[str, Any]) -> dict[str, Any]:
    """Execute GIMP Script-Fu commands in batch mode."""
    try:
        input_file = args["input_file"]
        output_file = args["output_file"]
        script = args["script"]
        flatten = args.get("flatten", True)

        return _execute_gimp_script(input_file, output_file, script, flatten)

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"GIMP script error: {str(e)}",
                }
            ]
        }


# =============================================================================
# GIMP Filter Tool
# =============================================================================


@tool(
    "gimp_filter",
    "Apply common GIMP filters to an image: gaussian-blur (smooth blur), "
    "motion-blur (directional blur), and unsharp-mask (sharpen). "
    "For other filters, use gimp_script with custom Script-Fu commands.",
    {
        "type": "object",
        "properties": {
            "input_file": {
                "type": "string",
                "description": "Path to the input image file",
            },
            "output_file": {
                "type": "string",
                "description": "Path for the output image file",
            },
            "filter": {
                "type": "string",
                "enum": [
                    "gaussian-blur",
                    "motion-blur",
                    "unsharp-mask",
                ],
                "description": "Filter to apply",
            },
            "strength": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "description": "Filter strength/intensity (1-100, default 50)",
            },
        },
        "required": ["input_file", "output_file", "filter"],
    },
)
async def gimp_filter(args: dict[str, Any]) -> dict[str, Any]:
    """Apply GIMP filters to an image."""
    try:
        input_file = args["input_file"]
        output_file = args["output_file"]
        filter_name = args["filter"]
        strength = args.get("strength", 50)

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

        # Map filter names to Script-Fu commands
        # Strength is normalized to each filter's expected range
        # These are GIMP 2.10 compatible procedure names
        filter_commands = {
            "gaussian-blur": f"(plug-in-gauss RUN-NONINTERACTIVE image drawable {strength / 2} {strength / 2} 0)",
            "motion-blur": f"(plug-in-mblur RUN-NONINTERACTIVE image drawable 0 {strength} 45 0 0)",
            "unsharp-mask": f"(plug-in-unsharp-mask RUN-NONINTERACTIVE image drawable {strength / 20} {strength / 100} 0)",
        }

        script_cmd = filter_commands.get(filter_name)
        if not script_cmd:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown filter: {filter_name}",
                    }
                ]
            }

        # Call the helper function directly (not the decorated tool)
        result = _execute_gimp_script(input_file, output_file, script_cmd, flatten=True)

        # Modify the success message to mention the filter
        if "Successfully" in result["content"][0]["text"]:
            result["content"][0]["text"] = result["content"][0]["text"].replace(
                "GIMP script", f"GIMP filter ({filter_name}, strength={strength})"
            )

        return result

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"GIMP filter error: {str(e)}",
                }
            ]
        }


# =============================================================================
# GIMP Text Tool
# =============================================================================


@tool(
    "gimp_text",
    "Add text to an image using GIMP's text rendering. Supports custom fonts, "
    "colors, sizes, and positioning. Better text quality than ImageMagick.",
    {
        "type": "object",
        "properties": {
            "input_file": {
                "type": "string",
                "description": "Path to the input image file",
            },
            "output_file": {
                "type": "string",
                "description": "Path for the output image file",
            },
            "text": {
                "type": "string",
                "description": "Text to add to the image",
            },
            "font": {
                "type": "string",
                "description": "Font name (e.g., 'Sans', 'Serif', 'Monospace')",
            },
            "size": {
                "type": "integer",
                "minimum": 8,
                "maximum": 500,
                "description": "Font size in pixels",
            },
            "color": {
                "type": "string",
                "description": "Text color as hex (e.g., '#ffffff') or name",
            },
            "x": {
                "type": "integer",
                "description": "X position for text (default 10)",
            },
            "y": {
                "type": "integer",
                "description": "Y position for text (default 10)",
            },
        },
        "required": ["input_file", "output_file", "text"],
    },
)
async def gimp_text(args: dict[str, Any]) -> dict[str, Any]:
    """Add text to an image using GIMP."""
    try:
        input_file = args["input_file"]
        output_file = args["output_file"]
        text = args["text"].replace('"', '\\"').replace("'", "\\'")  # Escape quotes
        font = args.get("font", "Sans")
        size = args.get("size", 32)
        color = args.get("color", "#000000")
        x = args.get("x", 10)
        y = args.get("y", 10)

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

        # Parse color to RGB values (0-255)
        if color.startswith("#"):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        else:
            # Common color names
            color_map = {
                "black": (0, 0, 0),
                "white": (255, 255, 255),
                "red": (255, 0, 0),
                "green": (0, 255, 0),
                "blue": (0, 0, 255),
                "yellow": (255, 255, 0),
                "cyan": (0, 255, 255),
                "magenta": (255, 0, 255),
            }
            r, g, b = color_map.get(color.lower(), (0, 0, 0))

        # Script-Fu command to add text
        # Note: gimp-context-set-foreground expects a list of RGB values
        script = f"""
(gimp-context-set-foreground '({r} {g} {b}))
(gimp-text-fontname image drawable {x} {y} "{text}" 0 TRUE {size} PIXELS "{font}")
"""

        # Call the helper function directly
        result = _execute_gimp_script(input_file, output_file, script, flatten=True)

        # Modify the success message
        if "Successfully" in result["content"][0]["text"]:
            display_text = text[:20] + "..." if len(text) > 20 else text
            result["content"][0]["text"] = result["content"][0]["text"].replace(
                "GIMP script", f"GIMP text ('{display_text}')"
            )

        return result

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"GIMP text error: {str(e)}",
                }
            ]
        }


# =============================================================================
# GIMP Layer Composite Tool
# =============================================================================


@tool(
    "gimp_composite",
    "Composite multiple images with advanced layer blending. More powerful than "
    "ImageMagick composite with support for GIMP's full range of blend modes.",
    {
        "type": "object",
        "properties": {
            "base_image": {
                "type": "string",
                "description": "Path to the base (background) image",
            },
            "overlay_image": {
                "type": "string",
                "description": "Path to the overlay (foreground) image",
            },
            "output_file": {
                "type": "string",
                "description": "Path for the output image file",
            },
            "blend_mode": {
                "type": "string",
                "enum": [
                    "normal",
                    "multiply",
                    "screen",
                    "overlay",
                    "soft-light",
                    "hard-light",
                    "difference",
                    "addition",
                    "subtract",
                    "darken-only",
                    "lighten-only",
                ],
                "description": "Layer blend mode (default: normal)",
            },
            "opacity": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Overlay layer opacity (0-100, default 100)",
            },
            "offset_x": {
                "type": "integer",
                "description": "Horizontal offset of overlay (default 0)",
            },
            "offset_y": {
                "type": "integer",
                "description": "Vertical offset of overlay (default 0)",
            },
        },
        "required": ["base_image", "overlay_image", "output_file"],
    },
)
async def gimp_composite(args: dict[str, Any]) -> dict[str, Any]:
    """Composite images with advanced blending using GIMP."""
    try:
        base_image = args["base_image"]
        overlay_image = args["overlay_image"]
        output_file = args["output_file"]
        blend_mode = args.get("blend_mode", "normal")
        opacity = args.get("opacity", 100)
        offset_x = args.get("offset_x", 0)
        offset_y = args.get("offset_y", 0)

        # Validate input files exist
        if not os.path.exists(base_image):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Base image not found: {base_image}",
                    }
                ]
            }
        if not os.path.exists(overlay_image):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Overlay image not found: {overlay_image}",
                    }
                ]
            }

        # Map blend modes to GIMP constants
        blend_modes = {
            "normal": "LAYER-MODE-NORMAL",
            "multiply": "LAYER-MODE-MULTIPLY",
            "screen": "LAYER-MODE-SCREEN",
            "overlay": "LAYER-MODE-OVERLAY",
            "soft-light": "LAYER-MODE-SOFTLIGHT",
            "hard-light": "LAYER-MODE-HARDLIGHT",
            "difference": "LAYER-MODE-DIFFERENCE",
            "addition": "LAYER-MODE-ADDITION",
            "subtract": "LAYER-MODE-SUBTRACT",
            "darken-only": "LAYER-MODE-DARKEN-ONLY",
            "lighten-only": "LAYER-MODE-LIGHTEN-ONLY",
        }
        gimp_blend_mode = blend_modes.get(blend_mode, "LAYER-MODE-NORMAL")

        # Get the appropriate save command
        save_cmd = _get_save_command(output_file)

        # Build batch script for compositing
        batch_script = f"""
(let* (
    (image (car (gimp-file-load RUN-NONINTERACTIVE "{base_image}" "{base_image}")))
    (base-layer (car (gimp-image-get-active-layer image)))
    (overlay (car (gimp-file-load-layer RUN-NONINTERACTIVE image "{overlay_image}")))
)
    (gimp-image-insert-layer image overlay 0 0)
    (gimp-layer-set-mode overlay {gimp_blend_mode})
    (gimp-layer-set-opacity overlay {opacity})
    (gimp-layer-set-offsets overlay {offset_x} {offset_y})
    (gimp-image-flatten image)
    {save_cmd}
    (gimp-image-delete image)
)
"""

        result = _run_gimp_batch(batch_script)

        if not result["success"]:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"GIMP composite failed: {result['error']}",
                    }
                ]
            }

        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Successfully composited images\n"
                            f"Base: {base_image}\n"
                            f"Overlay: {overlay_image}\n"
                            f"Output: {output_file} ({output_size:,} bytes)\n"
                            f"Blend: {blend_mode}, Opacity: {opacity}%"
                        ),
                    }
                ]
            }
        else:
            error_msg = result.get("stderr", "") or result.get(
                "stdout", "Unknown error"
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"GIMP composite failed: {error_msg}",
                    }
                ]
            }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"GIMP composite error: {str(e)}",
                }
            ]
        }


# =============================================================================
# MCP Server Creation
# =============================================================================


def create_gimp_server():
    """
    Create the GIMP MCP server with all tools.

    Returns an MCP server that can be registered with ClaudeAgentOptions.

    Usage:
        server = create_gimp_server()
        options = ClaudeAgentOptions(
            mcp_servers={"gimp": server},
            allowed_tools=GIMP_TOOL_NAMES
        )
    """
    return create_sdk_mcp_server(
        name="gimp",
        version="1.0.0",
        tools=[open_in_gimp, gimp_script, gimp_filter, gimp_text, gimp_composite],
    )


# Tool names for allowed_tools configuration
GIMP_TOOL_NAMES = [
    "mcp__gimp__open_in_gimp",
    "mcp__gimp__gimp_script",
    "mcp__gimp__gimp_filter",
    "mcp__gimp__gimp_text",
    "mcp__gimp__gimp_composite",
]
