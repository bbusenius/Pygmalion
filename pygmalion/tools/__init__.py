"""
Custom MCP tools for design operations.

Phase 6+: MCP tools that extend Claude's capabilities with external tools.

Available tool modules:
- inkscape: Vector graphics processing (export, convert, query, open GUI)
- imagemagick: Raster image processing (resize, convert, effects, composite)
- gimp: Advanced raster editing (script-fu, filters, text, compositing)
- weasyprint: PDF generation (HTML to PDF conversion)
- gemini: AI image generation (coming in Phase 10)
"""

from pygmalion.tools.gimp import GIMP_TOOL_NAMES, create_gimp_server
from pygmalion.tools.imagemagick import (
    IMAGEMAGICK_TOOL_NAMES,
    create_imagemagick_server,
)
from pygmalion.tools.inkscape import INKSCAPE_TOOL_NAMES, create_inkscape_server
from pygmalion.tools.weasyprint import WEASYPRINT_TOOL_NAMES, create_weasyprint_server

__all__ = [
    "create_inkscape_server",
    "INKSCAPE_TOOL_NAMES",
    "create_imagemagick_server",
    "IMAGEMAGICK_TOOL_NAMES",
    "create_gimp_server",
    "GIMP_TOOL_NAMES",
    "create_weasyprint_server",
    "WEASYPRINT_TOOL_NAMES",
]
