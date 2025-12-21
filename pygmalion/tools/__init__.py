"""
Custom MCP tools for design operations.

Phase 6+: MCP tools that extend Claude's capabilities with external tools.

Available tool modules:
- inkscape: Vector graphics processing (export, convert, query, open GUI)
- imagemagick: Raster image processing (coming in Phase 7)
- gimp: Advanced raster editing (coming in Phase 8)
- weasyprint: PDF generation (coming in Phase 9)
- gemini: AI image generation (coming in Phase 10)
"""

from pygmalion.tools.inkscape import (
    INKSCAPE_TOOL_NAMES,
    create_inkscape_server,
)

__all__ = [
    "create_inkscape_server",
    "INKSCAPE_TOOL_NAMES",
]
