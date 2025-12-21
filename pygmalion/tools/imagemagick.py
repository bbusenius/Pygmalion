"""
ImageMagick MCP Tools for Pygmalion.

Phase 7: Custom MCP tools for raster image processing.

SDK CONCEPTS EXPLAINED:
-----------------------
These tools wrap ImageMagick CLI commands to give Claude the ability to:

1. Resize images (with various fitting modes)
2. Convert between image formats (PNG, JPG, WebP, GIF, etc.)
3. Apply effects (blur, sharpen, contrast, etc.)
4. Composite/layer images together

IMAGEMAGICK COMMANDS:
---------------------
ImageMagick provides two main commands:
- `convert`: Transform images (one input, one output)
- `magick`: Modern unified command (ImageMagick 7+)
- `mogrify`: In-place modifications

We use `convert` for compatibility with both IM6 and IM7.

TOOL COMPOSITION:
-----------------
These tools can be chained together for complex workflows:
  1. Resize a photo to 800px wide
  2. Apply sharpening
  3. Convert to WebP for web use
  4. Composite with a watermark

Each tool is independent and works on files, enabling flexible pipelines.
"""

import os
import subprocess
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

# =============================================================================
# Image Resize Tool
# =============================================================================


@tool(
    "image_resize",
    "Resize an image to specified dimensions. Supports various fit modes: "
    "exact (stretch), fit (preserve aspect, fit within), fill (preserve aspect, crop to fill), "
    "and width/height only (scale proportionally).",
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
            "width": {
                "type": "integer",
                "minimum": 1,
                "description": "Target width in pixels",
            },
            "height": {
                "type": "integer",
                "minimum": 1,
                "description": "Target height in pixels",
            },
            "mode": {
                "type": "string",
                "enum": ["exact", "fit", "fill", "width", "height"],
                "description": (
                    "Resize mode: "
                    "exact=stretch to size, "
                    "fit=fit within bounds preserving aspect, "
                    "fill=fill bounds and crop, "
                    "width=scale to width, "
                    "height=scale to height"
                ),
            },
            "quality": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "description": "Output quality for JPEG/WebP (1-100, default 85)",
            },
        },
        "required": ["input_file", "output_file"],
    },
)
async def image_resize(args: dict[str, Any]) -> dict[str, Any]:
    """Resize an image using ImageMagick."""
    try:
        input_file = args["input_file"]
        output_file = args["output_file"]
        width = args.get("width")
        height = args.get("height")
        mode = args.get("mode", "fit")
        quality = args.get("quality", 85)

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

        # Build ImageMagick command
        cmd = ["convert", input_file]

        # Add resize geometry based on mode
        if width and height:
            if mode == "exact":
                # Stretch/squish to exact dimensions (ignore aspect ratio)
                cmd.extend(["-resize", f"{width}x{height}!"])
            elif mode == "fit":
                # Fit within bounds, preserve aspect ratio
                cmd.extend(["-resize", f"{width}x{height}"])
            elif mode == "fill":
                # Fill bounds and crop to exact size
                cmd.extend(["-resize", f"{width}x{height}^"])
                cmd.extend(["-gravity", "center"])
                cmd.extend(["-extent", f"{width}x{height}"])
        elif width:
            # Scale to width, auto height
            cmd.extend(["-resize", f"{width}x"])
        elif height:
            # Scale to height, auto width
            cmd.extend(["-resize", f"x{height}"])
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: Must specify width and/or height",
                    }
                ]
            }

        # Add quality setting
        cmd.extend(["-quality", str(quality)])

        # Output file
        cmd.append(output_file)

        # Execute
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and os.path.exists(output_file):
            # Get dimensions of output
            identify_result = subprocess.run(
                ["identify", "-format", "%wx%h", output_file],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output_dims = (
                identify_result.stdout.strip()
                if identify_result.returncode == 0
                else "unknown"
            )
            output_size = os.path.getsize(output_file)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Successfully resized image\n"
                            f"Input: {input_file}\n"
                            f"Output: {output_file}\n"
                            f"Dimensions: {output_dims}\n"
                            f"Size: {output_size:,} bytes"
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
                        "text": f"Resize failed: {error_msg}",
                    }
                ]
            }

    except subprocess.TimeoutExpired:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Resize operation timed out",
                }
            ]
        }
    except FileNotFoundError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "ImageMagick not found. Please install ImageMagick:\n"
                        "  sudo apt install imagemagick  # Debian/Ubuntu\n"
                        "  sudo dnf install ImageMagick  # Fedora\n"
                        "  sudo pacman -S imagemagick    # Arch"
                    ),
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Resize error: {str(e)}",
                }
            ]
        }


# =============================================================================
# Image Convert Tool
# =============================================================================


@tool(
    "image_convert",
    "Convert an image to a different format. Supports PNG, JPG, WebP, GIF, TIFF, BMP, and more. "
    "Can also adjust quality and strip metadata.",
    {
        "type": "object",
        "properties": {
            "input_file": {
                "type": "string",
                "description": "Path to the input image file",
            },
            "output_file": {
                "type": "string",
                "description": "Path for output file (format determined by extension)",
            },
            "quality": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "description": "Output quality for lossy formats (1-100, default 85)",
            },
            "strip_metadata": {
                "type": "boolean",
                "description": "Remove EXIF and other metadata (default true)",
            },
            "background": {
                "type": "string",
                "description": "Background color for transparency (e.g., 'white', '#ffffff')",
            },
        },
        "required": ["input_file", "output_file"],
    },
)
async def image_convert(args: dict[str, Any]) -> dict[str, Any]:
    """Convert image between formats using ImageMagick."""
    try:
        input_file = args["input_file"]
        output_file = args["output_file"]
        quality = args.get("quality", 85)
        strip_metadata = args.get("strip_metadata", True)
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

        # Build command
        cmd = ["convert", input_file]

        # Handle background for formats that don't support transparency
        output_ext = os.path.splitext(output_file)[1].lower()
        if output_ext in (".jpg", ".jpeg") and not background:
            background = "white"  # Default white background for JPG

        if background:
            cmd.extend(["-background", background, "-flatten"])

        # Quality setting
        cmd.extend(["-quality", str(quality)])

        # Strip metadata
        if strip_metadata:
            cmd.append("-strip")

        cmd.append(output_file)

        # Execute
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and os.path.exists(output_file):
            input_size = os.path.getsize(input_file)
            output_size = os.path.getsize(output_file)
            input_ext = os.path.splitext(input_file)[1]

            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Successfully converted image\n"
                            f"Input: {input_file} ({input_ext}, {input_size:,} bytes)\n"
                            f"Output: {output_file} ({output_ext}, {output_size:,} bytes)\n"
                            f"Size change: {output_size - input_size:+,} bytes"
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
                    "text": "ImageMagick not found. Please install ImageMagick.",
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
# Image Effects Tool
# =============================================================================


@tool(
    "image_effects",
    "Apply visual effects to an image: blur, sharpen, contrast, brightness, "
    "grayscale, sepia, and more. Multiple effects can be combined.",
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
            "blur": {
                "type": "number",
                "minimum": 0,
                "maximum": 100,
                "description": "Gaussian blur radius (0-100)",
            },
            "sharpen": {
                "type": "number",
                "minimum": 0,
                "maximum": 100,
                "description": "Sharpen amount (0-100)",
            },
            "brightness": {
                "type": "integer",
                "minimum": -100,
                "maximum": 100,
                "description": "Brightness adjustment (-100 to +100)",
            },
            "contrast": {
                "type": "integer",
                "minimum": -100,
                "maximum": 100,
                "description": "Contrast adjustment (-100 to +100)",
            },
            "saturation": {
                "type": "integer",
                "minimum": 0,
                "maximum": 200,
                "description": "Saturation (0=grayscale, 100=normal, 200=double)",
            },
            "grayscale": {
                "type": "boolean",
                "description": "Convert to grayscale",
            },
            "sepia": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Sepia tone amount (0-100)",
            },
            "negate": {
                "type": "boolean",
                "description": "Invert colors (negative)",
            },
            "rotate": {
                "type": "integer",
                "description": "Rotation angle in degrees",
            },
            "flip": {
                "type": "string",
                "enum": ["horizontal", "vertical", "both"],
                "description": "Flip the image",
            },
        },
        "required": ["input_file", "output_file"],
    },
)
async def image_effects(args: dict[str, Any]) -> dict[str, Any]:
    """Apply visual effects to an image using ImageMagick."""
    try:
        input_file = args["input_file"]
        output_file = args["output_file"]

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
        cmd = ["convert", input_file]
        effects_applied = []

        # Apply effects in order
        if args.get("blur"):
            blur_val = args["blur"]
            cmd.extend(["-blur", f"0x{blur_val}"])
            effects_applied.append(f"blur({blur_val})")

        if args.get("sharpen"):
            sharpen_val = args["sharpen"]
            cmd.extend(["-sharpen", f"0x{sharpen_val}"])
            effects_applied.append(f"sharpen({sharpen_val})")

        if args.get("brightness") is not None or args.get("contrast") is not None:
            brightness = args.get("brightness", 0)
            contrast = args.get("contrast", 0)
            cmd.extend(["-brightness-contrast", f"{brightness}x{contrast}"])
            effects_applied.append(f"brightness({brightness}), contrast({contrast})")

        if args.get("saturation") is not None:
            sat = args["saturation"]
            cmd.extend(["-modulate", f"100,{sat},100"])
            effects_applied.append(f"saturation({sat}%)")

        if args.get("grayscale"):
            cmd.extend(["-colorspace", "Gray"])
            effects_applied.append("grayscale")

        if args.get("sepia"):
            sepia_val = args["sepia"]
            cmd.extend(["-sepia-tone", f"{sepia_val}%"])
            effects_applied.append(f"sepia({sepia_val}%)")

        if args.get("negate"):
            cmd.append("-negate")
            effects_applied.append("negate")

        if args.get("rotate"):
            rotate_val = args["rotate"]
            cmd.extend(["-rotate", str(rotate_val)])
            effects_applied.append(f"rotate({rotate_val}°)")

        if args.get("flip"):
            flip_mode = args["flip"]
            if flip_mode == "horizontal":
                cmd.append("-flop")
            elif flip_mode == "vertical":
                cmd.append("-flip")
            elif flip_mode == "both":
                cmd.extend(["-flip", "-flop"])
            effects_applied.append(f"flip({flip_mode})")

        if not effects_applied:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No effects specified. Use blur, sharpen, brightness, etc.",
                    }
                ]
            }

        cmd.append(output_file)

        # Execute
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0 and os.path.exists(output_file):
            output_size = os.path.getsize(output_file)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Successfully applied effects\n"
                            f"Input: {input_file}\n"
                            f"Output: {output_file} ({output_size:,} bytes)\n"
                            f"Effects: {', '.join(effects_applied)}"
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
                        "text": f"Effects failed: {error_msg}",
                    }
                ]
            }

    except subprocess.TimeoutExpired:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Effects operation timed out",
                }
            ]
        }
    except FileNotFoundError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "ImageMagick not found. Please install ImageMagick.",
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Effects error: {str(e)}",
                }
            ]
        }


# =============================================================================
# Image Composite Tool
# =============================================================================


@tool(
    "image_composite",
    "Composite (layer) one image on top of another. Useful for watermarks, "
    "overlays, and combining images. Supports various blend modes and positioning.",
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
            "position": {
                "type": "string",
                "enum": [
                    "center",
                    "northwest",
                    "north",
                    "northeast",
                    "west",
                    "east",
                    "southwest",
                    "south",
                    "southeast",
                ],
                "description": "Position of overlay (default: center)",
            },
            "offset_x": {
                "type": "integer",
                "description": "Horizontal offset in pixels from position",
            },
            "offset_y": {
                "type": "integer",
                "description": "Vertical offset in pixels from position",
            },
            "opacity": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Overlay opacity (0-100, default 100)",
            },
            "blend": {
                "type": "string",
                "enum": [
                    "over",
                    "multiply",
                    "screen",
                    "overlay",
                    "darken",
                    "lighten",
                ],
                "description": "Blend mode (default: over)",
            },
            "resize_overlay": {
                "type": "string",
                "description": "Resize overlay (e.g., '50%', '200x100')",
            },
        },
        "required": ["base_image", "overlay_image", "output_file"],
    },
)
async def image_composite(args: dict[str, Any]) -> dict[str, Any]:
    """Composite images together using ImageMagick."""
    try:
        base_image = args["base_image"]
        overlay_image = args["overlay_image"]
        output_file = args["output_file"]
        position = args.get("position", "center")
        offset_x = args.get("offset_x", 0)
        offset_y = args.get("offset_y", 0)
        opacity = args.get("opacity", 100)
        blend = args.get("blend", "over")
        resize_overlay = args.get("resize_overlay")

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

        # Build command
        cmd = ["convert", base_image]

        # Add overlay with options
        cmd.append("(")
        cmd.append(overlay_image)

        if resize_overlay:
            cmd.extend(["-resize", resize_overlay])

        if opacity < 100:
            cmd.extend(
                [
                    "-alpha",
                    "set",
                    "-channel",
                    "A",
                    "-evaluate",
                    "multiply",
                    str(opacity / 100),
                ]
            )

        cmd.append(")")

        # Set gravity (position)
        cmd.extend(["-gravity", position.capitalize()])

        # Set blend mode
        cmd.extend(["-compose", blend.capitalize()])

        # Set offset if specified
        if offset_x or offset_y:
            cmd.extend(["-geometry", f"{offset_x:+d}{offset_y:+d}"])

        # Composite
        cmd.append("-composite")

        cmd.append(output_file)

        # Execute
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and os.path.exists(output_file):
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
                            f"Position: {position}, Blend: {blend}"
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
                        "text": f"Composite failed: {error_msg}",
                    }
                ]
            }

    except subprocess.TimeoutExpired:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Composite operation timed out",
                }
            ]
        }
    except FileNotFoundError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "ImageMagick not found. Please install ImageMagick.",
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Composite error: {str(e)}",
                }
            ]
        }


# =============================================================================
# MCP Server Creation
# =============================================================================


def create_imagemagick_server():
    """
    Create the ImageMagick MCP server with all tools.

    Returns an MCP server that can be registered with ClaudeAgentOptions.

    Usage:
        server = create_imagemagick_server()
        options = ClaudeAgentOptions(
            mcp_servers={"imagemagick": server},
            allowed_tools=IMAGEMAGICK_TOOL_NAMES
        )
    """
    return create_sdk_mcp_server(
        name="imagemagick",
        version="1.0.0",
        tools=[image_resize, image_convert, image_effects, image_composite],
    )


# Tool names for allowed_tools configuration
IMAGEMAGICK_TOOL_NAMES = [
    "mcp__imagemagick__image_resize",
    "mcp__imagemagick__image_convert",
    "mcp__imagemagick__image_effects",
    "mcp__imagemagick__image_composite",
]
