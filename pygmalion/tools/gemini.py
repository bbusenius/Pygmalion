"""
Gemini MCP Tools for Pygmalion.

Optional custom MCP tools for AI image generation.

SDK CONCEPTS EXPLAINED:
-----------------------
Google Gemini provides AI image generation capabilities through the Imagen model.
This demonstrates integrating external AI APIs as optional MCP tools with
graceful degradation when not configured.

WHEN TO USE GEMINI:
-------------------
Use Gemini for:
- Generating photorealistic images from text descriptions
- Creating concept art and design mockups
- Producing placeholder images for designs
- Generating backgrounds and textures

Use other tools for:
- Vector graphics: Inkscape (precise, scalable)
- Photo editing: GIMP (precise control)
- Simple graphics: ImageMagick (fast, deterministic)

OPTIONAL TOOL PATTERN:
----------------------
This tool is optional and requires:
1. google-genai package installed: pip install google-genai
2. GEMINI_API_KEY or GOOGLE_API_KEY environment variable set
3. Gemini API access enabled

If not configured, the tool gracefully reports the requirement without breaking
the session. This pattern allows users to opt-in to AI image generation.

CONFIGURATION:
--------------
Set up Gemini integration:
1. Get API key from https://aistudio.google.com/apikey
2. Set environment variable: export GEMINI_API_KEY=your-key-here
3. Install optional dependency: pip install -e ".[gemini]"
4. Optional: Set default image size: export PYGMALION_GEMINI_IMAGE_SIZE=2K (or 4K)

RATE LIMITS & ERRORS:
---------------------
Gemini API has rate limits and quotas. The tool handles:
- Missing API key (clear error message)
- Rate limit errors (reports to user)
- Network errors (graceful failure)
- Invalid prompts (validation feedback)

IMAGEN 4.0 FEATURES:
--------------------
- High-fidelity photorealistic images
- SynthID watermarking for authenticity
- Support for multiple aspect ratios
- Configurable resolution: 1K (~1024px) or 2K (~2048px)
- Text in images capability
- English-only prompts

GEMINI 3 PRO IMAGE (4K):
------------------------
- 4K resolution (~4096px) via gemini-3-pro-image-preview model
- Single image generation only (no batch support)
- Preview model - may change without notice

SVG GENERATION:
---------------
- Direct SVG code generation via Gemini text models
- Default model: gemini-2.5-flash (fast, good quality)
- Override via PYGMALION_GEMINI_SVG_MODEL env var or model parameter
- Outputs clean SVG code suitable for logos, icons, and illustrations
- Supports style guidance (minimal, geometric, organic, detailed, flat)
"""

import os
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

# Gemini is optional, so check if it's installed
try:
    from google import genai
    from google.genai import types

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# Valid image sizes for Gemini image generation
VALID_IMAGE_SIZES = ("1K", "2K", "4K")


def _check_gemini_available() -> dict[str, Any] | None:
    """Check if Gemini SDK is available. Returns error response or None if OK."""
    if not GEMINI_AVAILABLE:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Google Gemini SDK not installed. Install it with:\n"
                        "  pip install google-genai\n"
                        "Or install Pygmalion with Gemini support:\n"
                        '  pip install -e ".[gemini]"\n\n'
                        "Note: The old google-generativeai package is deprecated. "
                        "Use google-genai instead."
                    ),
                }
            ]
        }
    return None


def _check_api_key() -> tuple[str | None, dict[str, Any] | None]:
    """Check for API key. Returns (api_key, error_response) - one will be None."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None, {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.\n\n"
                        "To use Gemini:\n"
                        "1. Get an API key from: https://aistudio.google.com/apikey\n"
                        "2. Set the environment variable:\n"
                        "   export GEMINI_API_KEY=your-key-here\n"
                        "3. Restart your session"
                    ),
                }
            ]
        }
    return api_key, None


# =============================================================================
# 4K Image Generation Helper (Gemini 3 Pro Preview)
# =============================================================================


async def _generate_image_4k(
    client: "genai.Client",
    prompt: str,
    output_file: str,
    aspect_ratio: str,
) -> dict[str, Any]:
    """
    Generate a 4K image using Gemini 3 Pro Image Preview model.

    This model uses generate_content() instead of generate_images() and
    only supports single image generation.
    """
    # Gemini 3 Pro supports more aspect ratios than Imagen 4.0
    # Map our supported ratios (validated elsewhere)
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size="4K",
        ),
    )

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=prompt,
        config=config,
    )

    # Extract image from response parts
    image_data = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data is not None:
            image_data = part.inline_data.data
            break

    if not image_data:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "4K image generation failed. The model did not return an image.\n"
                        "This could be due to:\n"
                        "- Content policy violation\n"
                        "- Invalid prompt\n"
                        "- API rate limit\n\n"
                        "Try rephrasing your prompt or try again later."
                    ),
                }
            ]
        }

    # Ensure we use absolute paths
    abs_output_file = output_file
    if not os.path.isabs(output_file):
        output_dir = os.environ.get("PYGMALION_OUTPUT_DIR")
        if output_dir:
            abs_output_file = os.path.join(output_dir, output_file)
        else:
            abs_output_file = os.path.abspath(output_file)

    # Create parent directories if needed
    parent_dir = os.path.dirname(abs_output_file)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    # Save the image
    with open(abs_output_file, "wb") as f:
        f.write(image_data)

    if os.path.exists(abs_output_file):
        file_size = os.path.getsize(abs_output_file)
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Successfully generated 4K image with Gemini 3 Pro (preview)\n"
                        f"Prompt: {prompt}\n"
                        f"Output: {abs_output_file} ({file_size:,} bytes)\n"
                        f"Aspect ratio: {aspect_ratio}\n"
                        f"Image size: 4K\n"
                        f"Note: Using preview model (gemini-3-pro-image-preview)"
                    ),
                }
            ]
        }
    else:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "4K image generation completed but file save failed",
                }
            ]
        }


# =============================================================================
# Gemini Image Generation Tool
# =============================================================================


@tool(
    "gemini_generate_image",
    "Generate photorealistic images from text descriptions using Google Gemini's "
    "Imagen 4.0 model. Creates concept art, mockups, backgrounds, textures, and "
    "placeholder images. All images include SynthID watermark. Requires "
    "GEMINI_API_KEY environment variable.",
    {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Text description of the image to generate. Be specific "
                "and detailed for best results. Use descriptive language, specify "
                "style (e.g., 'photograph', 'painting', 'sketch'), and include "
                "context. English only. Example: 'close-up photo of a modern website "
                "homepage on a laptop screen, minimalist design, soft lighting'",
            },
            "output_file": {
                "type": "string",
                "description": "Path where the generated image should be saved (e.g., "
                "'output.png'). For multiple images, '_1', '_2', etc. will be "
                "appended before the extension.",
            },
            "num_images": {
                "type": "integer",
                "description": "Number of images to generate (1-4, default: 1)",
                "minimum": 1,
                "maximum": 4,
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["1:1", "3:4", "4:3", "9:16", "16:9"],
                "description": "Aspect ratio for the generated image (default: 1:1)",
            },
            "image_size": {
                "type": "string",
                "enum": ["1K", "2K", "4K"],
                "description": "Output image resolution: 1K (~1024px), 2K (~2048px), or "
                "4K (~4096px). 4K uses Gemini 3 Pro preview model. "
                "Default: 1K, or PYGMALION_GEMINI_IMAGE_SIZE env var if set.",
            },
        },
        "required": ["prompt", "output_file"],
    },
)
async def gemini_generate_image(args: dict[str, Any]) -> dict[str, Any]:
    """Generate images using Google Gemini's Imagen 4.0 model."""
    if error := _check_gemini_available():
        return error

    api_key, error = _check_api_key()
    if error:
        return error

    try:
        # Create Gemini client
        client = genai.Client(api_key=api_key)

        # Extract parameters
        prompt = args["prompt"]
        output_file = args["output_file"]
        num_images = args.get("num_images", 1)
        aspect_ratio = args.get("aspect_ratio", "1:1")

        # Get image_size - env var takes precedence as user's preferred default
        env_image_size = os.environ.get("PYGMALION_GEMINI_IMAGE_SIZE", "").upper()
        if env_image_size in VALID_IMAGE_SIZES:
            # User set a preference via env var - use it as the default
            image_size = env_image_size
        else:
            # No env var set, use arg or fall back to 1K
            image_size = args.get("image_size", "1K")
        # Validate image_size
        if image_size not in VALID_IMAGE_SIZES:
            image_size = "1K"

        # Validate prompt
        if not prompt or len(prompt.strip()) < 3:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: Prompt must be at least 3 characters long",
                    }
                ]
            }

        # For 4K, delegate to Gemini 3 Pro (preview model)
        if image_size == "4K":
            if num_images > 1:
                # Gemini 3 Pro only supports single image generation
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "4K resolution only supports generating 1 image at a time.\n"
                                "Please set num_images to 1, or use 1K/2K for batch generation."
                            ),
                        }
                    ]
                }
            return await _generate_image_4k(client, prompt, output_file, aspect_ratio)

        # Generate images using Imagen 4.0
        config = types.GenerateImagesConfig(
            number_of_images=num_images,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )

        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=config,
        )

        # Check if generation was successful
        if not response.generated_images:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Image generation failed. This could be due to:\n"
                            "- Content policy violation\n"
                            "- Invalid prompt\n"
                            "- API rate limit\n"
                            "- Network error\n\n"
                            "Try rephrasing your prompt or try again later."
                        ),
                    }
                ]
            }

        # Save the generated image(s)
        # Ensure we use absolute paths so files are created in the correct location
        if not os.path.isabs(output_file):
            # If path is relative, resolve it against Pygmalion's output directory
            # This is passed via PYGMALION_OUTPUT_DIR environment variable
            output_dir = os.environ.get("PYGMALION_OUTPUT_DIR")
            if output_dir:
                output_file = os.path.join(output_dir, output_file)
            else:
                # Fallback to current working directory
                output_file = os.path.abspath(output_file)

        # Create parent directories if needed
        parent_dir = os.path.dirname(output_file)
        if parent_dir:  # Only create if there's a directory component
            os.makedirs(parent_dir, exist_ok=True)

        if num_images == 1:
            # Single image - save directly
            image_bytes = response.generated_images[0].image.image_bytes
            with open(output_file, "wb") as f:
                f.write(image_bytes)

            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Successfully generated image with Gemini Imagen 4.0\n"
                                f"Prompt: {prompt}\n"
                                f"Output: {output_file} ({file_size:,} bytes)\n"
                                f"Aspect ratio: {aspect_ratio}\n"
                                f"Image size: {image_size}\n"
                                f"Note: Image includes SynthID watermark"
                            ),
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Image generation completed but file save failed",
                        }
                    ]
                }
        else:
            # Multiple images - save with numbered suffixes
            # output_file has already been resolved to absolute path above
            base_name = os.path.splitext(output_file)[0]
            extension = os.path.splitext(output_file)[1] or ".png"
            saved_files = []

            # Create parent directories if needed
            parent_dir = os.path.dirname(output_file)
            if parent_dir:  # Only create if there's a directory component
                os.makedirs(parent_dir, exist_ok=True)

            for i, generated_image in enumerate(response.generated_images, 1):
                numbered_file = f"{base_name}_{i}{extension}"
                image_bytes = generated_image.image.image_bytes
                with open(numbered_file, "wb") as f:
                    f.write(image_bytes)
                if os.path.exists(numbered_file):
                    saved_files.append(numbered_file)

            if saved_files:
                files_list = "\n".join(f"  - {f}" for f in saved_files)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Successfully generated {len(saved_files)} images with Gemini Imagen 4.0\n"
                                f"Prompt: {prompt}\n"
                                f"Files:\n{files_list}\n"
                                f"Aspect ratio: {aspect_ratio}\n"
                                f"Image size: {image_size}\n"
                                f"Note: Images include SynthID watermark"
                            ),
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Image generation completed but no files were saved",
                        }
                    ]
                }

    except Exception as e:
        # Handle various errors gracefully
        error_msg = str(e)

        # Check for common error types
        if "quota" in error_msg.lower() or "rate" in error_msg.lower():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Gemini API rate limit or quota exceeded.\n"
                            f"Error: {error_msg}\n\n"
                            f"Please try again later or check your API quota at:\n"
                            f"https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas"
                        ),
                    }
                ]
            }
        elif "api key" in error_msg.lower() or "auth" in error_msg.lower():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Gemini API authentication error.\n"
                            f"Error: {error_msg}\n\n"
                            f"Please verify your API key is correct and active."
                        ),
                    }
                ]
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Gemini image generation error: {error_msg}",
                    }
                ]
            }


# =============================================================================
# Gemini SVG Generation Tool
# =============================================================================

# Default SVG model - can be overridden via env var or parameter
DEFAULT_SVG_MODEL = "gemini-2.5-flash"


@tool(
    "gemini_generate_svg",
    "Generate SVG vector graphics from text descriptions using Google Gemini. "
    "Creates clean, scalable vector code for any SVG need: logos, icons, "
    "illustrations, diagrams, or graphic elements. Output is pure SVG code "
    "saved to a file. Requires GEMINI_API_KEY environment variable.",
    {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Text description of the SVG to generate. Be specific "
                "about shapes, colors, style, and composition. Can request anything "
                "from simple icons to complete logos to complex illustrations.",
            },
            "output_file": {
                "type": "string",
                "description": "Path where the SVG file should be saved (e.g., "
                "'logo.svg'). Must end with .svg extension.",
            },
            "style": {
                "type": "string",
                "enum": ["minimal", "geometric", "organic", "detailed", "flat"],
                "description": "Visual style hint (default: minimal). "
                "minimal: clean lines, few elements. "
                "geometric: precise shapes. "
                "organic: flowing curves. "
                "detailed: more complexity. "
                "flat: solid colors, no gradients.",
            },
            "viewbox_size": {
                "type": "integer",
                "minimum": 24,
                "maximum": 1024,
                "description": "Size of the SVG viewBox (square). "
                "Default: 100. Smaller (24-64) for icons, larger for detailed work.",
            },
            "model": {
                "type": "string",
                "description": "Gemini model to use for generation. "
                "Default: gemini-2.5-flash (or PYGMALION_GEMINI_SVG_MODEL env var). "
                "Options: gemini-2.5-flash, gemini-3-flash, gemini-3-pro, etc.",
            },
        },
        "required": ["prompt", "output_file"],
    },
)
async def gemini_generate_svg(args: dict[str, Any]) -> dict[str, Any]:
    """Generate SVG vector graphics using Google Gemini."""
    if error := _check_gemini_available():
        return error

    api_key, error = _check_api_key()
    if error:
        return error

    try:
        client = genai.Client(api_key=api_key)

        prompt = args["prompt"]
        output_file = args["output_file"]
        style = args.get("style", "minimal")
        viewbox_size = args.get("viewbox_size", 100)

        # Model selection: parameter > env var > default
        model = args.get("model")
        if not model:
            model = os.environ.get("PYGMALION_GEMINI_SVG_MODEL", DEFAULT_SVG_MODEL)

        if not output_file.lower().endswith(".svg"):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: output_file must end with .svg extension",
                    }
                ]
            }

        if not prompt or len(prompt.strip()) < 3:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: Prompt must be at least 3 characters long",
                    }
                ]
            }

        # Style guidance for the prompt
        style_guidance = {
            "minimal": "Clean lines, minimal elements, simplicity.",
            "geometric": "Precise geometric shapes, mathematical precision.",
            "organic": "Flowing curves, bezier paths, natural forms.",
            "detailed": "Fine details, textures, ornamentation.",
            "flat": "Solid flat colors only, no gradients or effects.",
        }

        svg_prompt = f"""Generate clean, well-structured SVG code for:

{prompt}

Style guidance: {style_guidance.get(style, style_guidance['minimal'])}

Requirements:
- Output ONLY valid SVG code, no explanation or markdown
- Use viewBox="0 0 {viewbox_size} {viewbox_size}"
- Do NOT include width/height attributes (viewBox handles scaling)
- Keep paths clean and optimized
- Ensure the design is centered and well-composed
- Start with <svg and end with </svg>

SVG code:"""

        response = client.models.generate_content(
            model=model,
            contents=svg_prompt,
        )

        if not response.candidates or not response.candidates[0].content.parts:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "SVG generation failed. The model did not return content.\n"
                            "Try rephrasing your prompt or try again later."
                        ),
                    }
                ]
            }

        svg_content = response.candidates[0].content.parts[0].text.strip()

        # Remove markdown code blocks if present
        if svg_content.startswith("```"):
            lines = svg_content.split("\n")
            start_idx = 1
            end_idx = len(lines)
            for i, line in enumerate(lines):
                if line.startswith("```") and i > 0:
                    end_idx = i
                    break
            svg_content = "\n".join(lines[start_idx:end_idx]).strip()

        # Extract SVG if embedded in other text
        if not svg_content.startswith("<svg"):
            svg_start = svg_content.find("<svg")
            svg_end = svg_content.rfind("</svg>")
            if svg_start != -1 and svg_end != -1:
                svg_content = svg_content[svg_start : svg_end + 6]
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "SVG generation produced invalid output.\n"
                                "The response did not contain valid SVG code.\n"
                                "Try a more specific prompt."
                            ),
                        }
                    ]
                }

        # Resolve output path
        abs_output_file = output_file
        if not os.path.isabs(output_file):
            output_dir = os.environ.get("PYGMALION_OUTPUT_DIR")
            if output_dir:
                abs_output_file = os.path.join(output_dir, output_file)
            else:
                abs_output_file = os.path.abspath(output_file)

        parent_dir = os.path.dirname(abs_output_file)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(abs_output_file, "w", encoding="utf-8") as f:
            f.write(svg_content)

        if os.path.exists(abs_output_file):
            file_size = os.path.getsize(abs_output_file)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Successfully generated SVG with Gemini\n"
                            f"Model: {model}\n"
                            f"Prompt: {prompt}\n"
                            f"Output: {abs_output_file} ({file_size:,} bytes)\n"
                            f"Style: {style}\n"
                            f"ViewBox: 0 0 {viewbox_size} {viewbox_size}"
                        ),
                    }
                ]
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "SVG generation completed but file save failed",
                    }
                ]
            }

    except Exception as e:
        error_msg = str(e)

        # Check for specific error types
        if "not found" in error_msg.lower() or "404" in error_msg:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Model not found: {model}\n"
                            f"Error: {error_msg}\n\n"
                            f"Available models:\n"
                            f"- gemini-2.5-flash (fast, stable)\n"
                            f"- gemini-2.5-pro (powerful, stable)\n"
                            f"- gemini-3-flash (preview)\n\n"
                            f"Note: Model names may change. Use stable 2.5 models for reliability."
                        ),
                    }
                ]
            }
        elif "quota" in error_msg.lower() or ("rate" in error_msg.lower() and "limit" in error_msg.lower()):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Gemini API rate limit exceeded.\nError: {error_msg}",
                    }
                ]
            }
        elif "api key" in error_msg.lower() or "auth" in error_msg.lower():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Gemini API authentication error.\nError: {error_msg}",
                    }
                ]
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Gemini SVG generation error: {error_msg}",
                    }
                ]
            }


# =============================================================================
# MCP Server Creation
# =============================================================================


def create_gemini_server():
    """
    Create the Gemini MCP server with image and SVG generation tools.

    Returns an MCP server that can be conditionally registered with
    ClaudeAgentOptions based on configuration.

    Usage:
        if gemini_enabled:
            server = create_gemini_server()
            options = ClaudeAgentOptions(
                mcp_servers={"gemini": server},
                allowed_tools=GEMINI_TOOL_NAMES
            )
    """
    return create_sdk_mcp_server(
        name="gemini",
        version="1.0.0",
        tools=[gemini_generate_image, gemini_generate_svg],
    )


# Tool names for allowed_tools configuration
GEMINI_TOOL_NAMES = [
    "mcp__gemini__gemini_generate_image",
    "mcp__gemini__gemini_generate_svg",
]
