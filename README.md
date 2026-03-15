# Pygmalion

AI-powered web and graphic design assistant using the Claude Agent SDK.

## Overview

Pygmalion is your complete design partner, capable of generating:
- Full websites (HTML/CSS/JS/React)
- Professional logos with color variations (SVG)
- Vector graphics and illustrations (SVG)
- Social media graphics
- Print-ready designs (PDF exports)

Built for Linux users who prioritize open-source tools and local execution.

## Installation

```bash
# Clone the repository
git clone https://github.com/bbusenius/Pygmalion.git
cd pygmalion

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .

# Or with all optional dependencies
pip install -e ".[all]"
```

## Authentication

Pygmalion uses the Claude Agent SDK, which supports multiple authentication methods:

### Option 1: API Key (Recommended)

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

Or create a `.env` file (copy from `.env.example`).

Get an API key at [console.anthropic.com](https://console.anthropic.com/).

### Option 2: Claude Code CLI (OAuth)

If you have Claude Code installed, authentication can happen automatically via OAuth:
```bash
claude  # Opens interactive auth if needed
```

> **Warning:** Anthropic has been known to ban accounts for using OAuth authentication (via Claude Code or any personal plan) to power third-party tools or automated agents. If you use this method, you risk having your account suspended. The API key method (Option 1) is the safe and supported approach for programmatic use.

## Skills

Pygmalion uses skills to guide Claude's design work. Skills in Pygmalion's `.claude/skills/` directory are automatically copied to your output directory on session startup, making them available to the SDK.

### Bundled Skills

**logo-design** - Creates distinctive, professional logos with proper color variations. Generates logos in three color versions (monotone, two-color, three-color) with layout variations when appropriate. Supports all logo types: wordmarks, lettermarks, iconographic, combination marks, and emblems. Includes Potrace bitmap tracing to convert raster images (PNG, JPG) to clean vector graphics for logo icons. Automatically invokes frontend-design skill for typography guidance. Outputs both editable versions (text as text) and delivery versions (text converted to outlines for perfect browser rendering), plus an HTML presentation showing all variations.

**print-design** - Creates print-ready designs (posters, flyers, business cards, resumes) using HTML/WeasyPrint or SVG/Inkscape. Includes guidance on full bleed layouts, WeasyPrint CSS limitations, and proper text handling.

### Frontend Design Skill (Recommended)

The `frontend-design` skill generates distinctive, production-grade web interfaces with bold aesthetics. This is Anthropic's skill and must be installed separately.

**Option 1: Install via Claude Code (Global)**

```bash
claude /plugin marketplace add anthropics/claude-code
claude /plugin install frontend-design@anthropics-claude-code
```

This installs to `~/.claude/skills/` and is available for all projects.

**Option 2: Install to Pygmalion Directory**

Install to Pygmalion so it gets copied to all output directories:

```bash
mkdir -p .claude/skills/frontend-design
curl -o .claude/skills/frontend-design/SKILL.md \
  https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/frontend-design/skills/frontend-design/SKILL.md
```

### Verification

Run `pygmalion` and type `/status`. You should see your installed skills:
```
Skills: frontend-design, logo-design, print-design
```

### Logo Design with Bitmap Tracing

Create professional logos using bitmap tracing workflow (generate bitmap → trace to vector):

```
🎨 You: Invoke the logo-design skill and design me a logo for Volcano Adventures,
       a volcano tour company in Antigua, Guatemala. The brand should feel bold
       and adventurous. Generate a high-contrast black and white volcano
       illustration with Gemini, then trace it to SVG.

🤖 Pygmalion: [Invokes frontend-design skill for typography guidance]
              [Generates volcano illustration bitmap using Gemini]
              [Traces the bitmap to vector using Potrace]
              [Optimizes viewBox with Inkscape for tight bounding]
              [Creates logo with traced volcano icon and distinctive typography]
              [Generates all color variations: monotone, two-color, three-color]
              [Creates layout variations: horizontal, vertical, icon-only]
              [Converts text to outlines for browser-safe rendering]
              [Opens presentation HTML showing all variations]

Files created:
- volcano_traced.svg (optimized vector from bitmap)
- logo_monotone_horizontal_editable.svg (editable version, text as text)
- logo_monotone_horizontal.svg (delivery version, text as paths)
- logo_two_color_horizontal.svg
- logo_three_color_horizontal.svg
- logo_monotone_vertical.svg
- logo_icon_only.svg
- logo_presentation.html
```

The bitmap tracing workflow:
1. Generate or provide a raster image (via Gemini, photo, sketch)
2. Convert to vector using Potrace
3. Optimize viewBox with Inkscape for tight bounding
4. Integrate into logo with professional typography
5. Output editable (text) and delivery (outlined) versions

## Usage

```bash
# Start the interactive CLI
pygmalion

# Or specify an output directory
pygmalion --output-dir ~/my-project

# Or run the module directly
python -m pygmalion.main
```

If you don't specify `--output-dir`, Pygmalion will prompt you for a directory when it starts. This gives you complete control over where files are created.

### Model Selection

Choose which Claude model to use with the `--model` flag. Aliases automatically resolve to the latest version:

```bash
# Use Claude Opus (most capable, best for complex designs)
pygmalion --model opus

# Use Claude Sonnet (default, balanced performance)
pygmalion --model sonnet

# Use Claude Haiku (fastest, good for simple tasks)
pygmalion --model haiku
```

To pin a specific model version, pass the full model ID:

```bash
pygmalion --model claude-sonnet-4-5-20250514
```

Available model IDs can be found in the [Anthropic API documentation](https://docs.anthropic.com/en/docs/about-claude/models).

You can also change models during a session with the `/model` command.

### Auto-Opening Files

Pygmalion automatically opens created files in the appropriate application:
- **SVG files** → Inkscape
- **Image files** (PNG, JPG, etc.) → GIMP
- **HTML files** → Default browser
- **PDF files** → Default PDF viewer

### Customization with CLAUDE.md

Pygmalion respects project-specific and global CLAUDE.md files for custom design guidelines:

**Project-level** (`.claude/CLAUDE.md` in your output directory):
```markdown
# Design System

## Colors
Primary: #3B82F6
Secondary: #10B981

## Typography
- Use Inter font family
- Headings: 700 weight
- Body: 400 weight

## Spacing
Use 8px grid system (8, 16, 24, 32, etc.)
```

**Global** (`~/.claude/CLAUDE.md` - applies to all projects):
```markdown
# Personal Preferences
- Always use Tailwind CSS classes
- Prefer semantic HTML5 elements
- Include accessibility attributes (ARIA labels, alt text)
```

These files are automatically loaded and Claude will follow the guidelines when generating designs.

**Custom Skills** (`.claude/skills/` in output directory or `~/.claude/skills/`):

You can also create custom skills for reusable design patterns. See the [Claude Code skills documentation](https://github.com/anthropics/claude-code) for details on creating SKILL.md files.

### Using Brand Guidelines and Styleguides

Pygmalion can follow your organization's brand guidelines when generating designs. Configure your CLAUDE.md to include brand rules or reference external documentation:

**Embed Rules Directly**

For simple brand systems, include the key rules in CLAUDE.md:

```markdown
# Brand Guidelines

## Colors
Primary: #1E3A5F (Navy Blue)
Secondary: #E8B923 (Gold)
Accent: #2E7D32 (Forest Green)

## Typography
- Headings: Montserrat Bold
- Body: Open Sans Regular

## Logo Usage
- Minimum clear space: 20px around logo
- Logo file: assets/logo.svg
```

**Reference External Documents**

For comprehensive brand guides, reference them in CLAUDE.md so Pygmalion reads them automatically:

```markdown
# Brand Guidelines

Before creating any designs, read and follow the brand guidelines in:
- docs/brand-guide.pdf (complete brand documentation)
- docs/color-palette.md (approved color codes)
- https://example.com/design-system (online style guide)
```

Pygmalion can read PDFs, markdown files, and fetch web-based style guides to extract colors, typography, spacing rules, and usage guidelines.

**Recommended Project Structure**

```
my-project/
├── .claude/
│   └── CLAUDE.md          # Brand rules + references to docs
├── docs/
│   ├── brand-guide.pdf    # Full brand documentation
│   └── color-palette.md   # Quick color reference
├── assets/
│   ├── logo.svg
│   └── icons/
└── src/
    └── [generated files]
```

This ensures Pygmalion automatically applies your brand rules to every design without needing to specify them in each prompt.

### Example Session

Pygmalion maintains conversation context, so you can iterate on designs:

```
🎨 You: Create a responsive navigation bar with a logo and three menu items

🤖 Pygmalion: [Claude generates the HTML, CSS, and provides explanations]
               [Browser automatically opens with the page]

🎨 You [1]: Make it sticky at the top of the page

🤖 Pygmalion: [Claude modifies the SAME navigation bar]

🎨 You [2]: Add a dropdown menu under the About link

🤖 Pygmalion: [Claude adds to the existing code]
```

### Commands

- `/help` - Show available commands
- `/status` - Show current session info (message count)
- `/new` - Start a new session (clears context)
- `/quit` - Exit Pygmalion
- `/clear` - Clear the screen

### Debug Mode and Logging

Pygmalion includes logging for troubleshooting:

```bash
# Enable debug mode (verbose logging)
pygmalion --debug

# Disable file logging (console only)
pygmalion --no-log-file
```

**Log Files:**
- Location: `~/.pygmalion/logs/pygmalion.log`
- Automatic rotation: 10 MB max size, 5 backup files
- Debug mode: Shows detailed SDK communication and tool calls
- Normal mode: Shows errors and warnings only

**Error Messages:**
Pygmalion provides user-friendly error messages with suggestions:
- Missing API key → Instructions to set ANTHROPIC_API_KEY
- Tool not found → Installation instructions for Inkscape/ImageMagick/GIMP
- Network errors → Retry suggestions
- Permission errors → File permission fixes

## Requirements

### System Dependencies

- Python 3.10+
- Inkscape (for vector graphics and text-to-outlines conversion)
- Potrace (for bitmap tracing - converts raster images to vector graphics)
- ImageMagick (for image processing and format conversion)
- GIMP (for advanced raster editing)
- Chrome with Claude Code extension (for web preview)

### Python Dependencies

- `claude-agent-sdk` - Core agent functionality
- `python-dotenv` - Environment variable management
- `prompt-toolkit` - Enhanced command-line input with history and editing
- `weasyprint` (optional) - PDF generation
- `google-genai` (optional) - Gemini Imagen 4.0 integration (requires billing account)

### External MCP Server Integrations (Optional)

These integrations require separate installation and configuration via environment variables in your `.env` file:

**Figma** - Import designs from Figma files
- Requires: Node.js (npx)
- Get access token: https://www.figma.com/developers/api#access-tokens
- Environment variables:
  ```bash
  PYGMALION_FIGMA_ENABLED=true
  FIGMA_ACCESS_TOKEN=figd_...
  ```

**Grok** - AI image generation and vision capabilities via xAI
- Requires: [Grok MCP](https://github.com/merterbak/Grok-MCP) installed separately
- Get API key: https://console.x.ai/
- Environment variables:
  ```bash
  PYGMALION_GROK_ENABLED=true
  XAI_API_KEY=xai-...
  GROK_MCP_PATH=/path/to/Grok-MCP
  ```

### Image Generation

Pygmalion supports AI image generation through two providers:

**Gemini (Google)** - Photorealistic images and SVG vector graphics
- Requires: `pip install -e ".[gemini]"` and billing-enabled API key
- Get API key: https://aistudio.google.com/apikey
- Environment variables:
  ```bash
  PYGMALION_GEMINI_ENABLED=true
  GEMINI_API_KEY=AIza...
  PYGMALION_GEMINI_IMAGE_SIZE=1K  # Options: 1K, 2K, 4K
  PYGMALION_GEMINI_SVG_MODEL=gemini-2.5-flash  # Optional: Override SVG model
  ```
- **Raster image resolution options:**
  | Size | Resolution | Model | Batch |
  |------|------------|-------|-------|
  | 1K | ~1024px | Imagen 4.0 | 1-4 images |
  | 2K | ~2048px | Imagen 4.0 | 1-4 images |
  | 4K | ~4096px | Gemini 3 Pro (preview) | 1 image only |

- **SVG vector graphics generation:**
  - Generate clean, scalable SVG code for logos, icons, illustrations
  - Default model: `gemini-2.5-flash` (fast, good quality)
  - Alternative models: `gemini-3-flash`, `gemini-3-pro` (higher quality, slower)
  - Style options: minimal, geometric, organic, detailed, flat
  - Example: "Have Gemini generate an SVG of a minimalist mountain logo"

**Grok (xAI)** - Image generation and vision analysis
- Image generation: Create images from text prompts
- Vision/analysis: Analyze existing images, extract colors, identify compositions
- See Grok MCP configuration above for setup

### Vision and Image Analysis

**Grok Vision** - Analyze images to extract design information. The print-design skill uses this to analyze generated images and determine optimal text placement.

- Identify color palettes, typography, layout patterns
- Describe image content and composition
- Useful for recreating designs or extracting style elements
- Requires Grok MCP integration (see above)

## Project Structure

```
pygmalion/
├── pygmalion/
│   ├── __init__.py
│   ├── main.py          # CLI entry point
│   ├── agent.py         # Core agent logic
│   ├── config.py        # Configuration management
│   ├── tools/           # Custom MCP tools
│   ├── prompts/         # System prompts
│   └── utils/           # Utilities
├── pyproject.toml
└── README.md
```

## License

MIT
