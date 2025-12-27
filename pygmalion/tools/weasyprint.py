"""
WeasyPrint MCP Tools for Pygmalion.

Custom MCP tools for PDF generation.

SDK CONCEPTS EXPLAINED:
-----------------------
WeasyPrint is a Python library (not a CLI tool) that converts HTML/CSS to PDF.
This demonstrates integrating pure Python libraries as MCP tools, versus
CLI tools like Inkscape/ImageMagick/GIMP.

WHEN TO USE WEASYPRINT:
-----------------------
Use WeasyPrint for:
- Converting HTML designs to print-ready PDFs
- Creating PDFs with proper CSS styling and layout
- Generating multi-page documents from HTML
- Print materials (flyers, posters, business cards)

Use other tools for:
- Vector graphics: Inkscape (SVG to PDF)
- Raster images: ImageMagick/GIMP (no PDF generation)
- Complex layouts: Generate HTML first, then convert with WeasyPrint

PDF GENERATION BEST PRACTICES:
------------------------------
1. Use CSS @page rules for print-specific styling
2. Specify page size, margins, and orientation
3. Use print media queries for screen vs print differences
4. Test with different page sizes (A4, Letter, etc.)
5. Embed fonts for consistent rendering

PYTHON LIBRARY VS CLI TOOL:
---------------------------
WeasyPrint is imported as a Python library, not called as a subprocess:
  from weasyprint import HTML, CSS
  HTML('input.html').write_pdf('output.pdf')

This is more efficient than CLI tools because:
- No subprocess overhead
- Direct Python integration
- Better error handling
- Access to full library API
"""

import os
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

# WeasyPrint is optional, so check if it's installed
try:
    from weasyprint import CSS, HTML

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


# =============================================================================
# HTML to PDF Tool
# =============================================================================


@tool(
    "html_to_pdf",
    "Convert an HTML file to a print-ready PDF with CSS styling. Supports "
    "custom page sizes, margins, and print-specific CSS. Use this to create "
    "PDFs from web designs, flyers, business cards, or any HTML content.",
    {
        "type": "object",
        "properties": {
            "input_file": {
                "type": "string",
                "description": "Path to the input HTML file",
            },
            "output_file": {
                "type": "string",
                "description": "Path for the output PDF file",
            },
            "css_file": {
                "type": "string",
                "description": "Optional path to additional CSS file for styling",
            },
            "page_size": {
                "type": "string",
                "enum": ["letter", "legal", "a4", "a3", "a5"],
                "description": "Page size (default: letter)",
            },
            "orientation": {
                "type": "string",
                "enum": ["portrait", "landscape"],
                "description": "Page orientation (default: portrait)",
            },
        },
        "required": ["input_file", "output_file"],
    },
)
async def html_to_pdf(args: dict[str, Any]) -> dict[str, Any]:
    """Convert HTML to PDF using WeasyPrint."""
    if not WEASYPRINT_AVAILABLE:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "WeasyPrint not installed. Install it with:\n"
                        "  pip install weasyprint\n"
                        "Or install Pygmalion with all dependencies:\n"
                        '  pip install -e ".[all]"'
                    ),
                }
            ]
        }

    try:
        input_file = args["input_file"]
        output_file = args["output_file"]
        css_file = args.get("css_file")
        page_size = args.get("page_size", "letter")
        orientation = args.get("orientation", "portrait")

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

        # Validate CSS file if provided
        if css_file and not os.path.exists(css_file):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: CSS file not found: {css_file}",
                    }
                ]
            }

        # Build CSS for page size and orientation (only if explicitly specified)
        # We don't add margin here - let the HTML control margins for full bleed support
        stylesheets = []
        if "page_size" in args or "orientation" in args:
            page_css = f"""
            @page {{
                size: {page_size} {orientation};
            }}
            """
            stylesheets.append(CSS(string=page_css))

        if css_file:
            stylesheets.append(CSS(filename=css_file))

        # Convert HTML to PDF
        html = HTML(filename=input_file)
        html.write_pdf(output_file, stylesheets=stylesheets or None)

        # Check output file was created
        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Successfully converted HTML to PDF\n"
                            f"Input: {input_file}\n"
                            f"Output: {output_file} ({output_size:,} bytes)\n"
                            f"Page size: {page_size} {orientation}"
                        ),
                    }
                ]
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "PDF conversion failed: Output file not created",
                    }
                ]
            }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"PDF conversion error: {str(e)}",
                }
            ]
        }


# =============================================================================
# MCP Server Creation
# =============================================================================


def create_weasyprint_server():
    """
    Create the WeasyPrint MCP server with all tools.

    Returns an MCP server that can be registered with ClaudeAgentOptions.

    Usage:
        server = create_weasyprint_server()
        options = ClaudeAgentOptions(
            mcp_servers={"weasyprint": server},
            allowed_tools=WEASYPRINT_TOOL_NAMES
        )
    """
    return create_sdk_mcp_server(
        name="weasyprint",
        version="1.0.0",
        tools=[html_to_pdf],
    )


# Tool names for allowed_tools configuration
WEASYPRINT_TOOL_NAMES = [
    "mcp__weasyprint__html_to_pdf",
]
