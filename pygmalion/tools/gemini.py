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
4. Optional: Set default image size: export PYGMALION_GEMINI_IMAGE_SIZE=2K

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
                "enum": ["1K", "2K"],
                "description": "Output image resolution: 1K (~1024px) or 2K (~2048px). "
                "Default: 1K, or PYGMALION_GEMINI_IMAGE_SIZE env var if set.",
            },
        },
        "required": ["prompt", "output_file"],
    },
)
async def gemini_generate_image(args: dict[str, Any]) -> dict[str, Any]:
    """Generate images using Google Gemini's Imagen 4.0 model."""
    # Check if Gemini is available
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

    # Check for API key (supports both GEMINI_API_KEY and GOOGLE_API_KEY)
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.\n\n"
                        "To use Gemini image generation:\n"
                        "1. Get an API key from: https://aistudio.google.com/apikey\n"
                        "2. Set the environment variable:\n"
                        "   export GEMINI_API_KEY=your-key-here\n"
                        "3. Restart your session"
                    ),
                }
            ]
        }

    try:
        # Create Gemini client
        client = genai.Client(api_key=api_key)

        # Extract parameters
        prompt = args["prompt"]
        output_file = args["output_file"]
        num_images = args.get("num_images", 1)
        aspect_ratio = args.get("aspect_ratio", "1:1")

        # Get image_size with env var fallback (default: 1K)
        default_image_size = os.environ.get("PYGMALION_GEMINI_IMAGE_SIZE", "1K")
        image_size = args.get("image_size", default_image_size)
        # Validate image_size
        if image_size not in ("1K", "2K"):
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
# MCP Server Creation
# =============================================================================


def create_gemini_server():
    """
    Create the Gemini MCP server with image generation tools.

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
        tools=[gemini_generate_image],
    )


# Tool names for allowed_tools configuration
GEMINI_TOOL_NAMES = [
    "mcp__gemini__gemini_generate_image",
]
