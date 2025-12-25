# Pygmalion

AI-powered web and graphic design assistant using the Claude Agent SDK.

## Overview

Pygmalion is your complete design partner, capable of generating:
- Full websites (HTML/CSS/JS/React)
- Vector graphics and logos (SVG)
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

### Option 1: Claude Code CLI (Recommended)
If you have Claude Code installed, authentication is automatic:
```bash
claude  # Opens interactive auth if needed
```

### Option 2: API Key
Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

Or create a `.env` file (copy from `.env.example`).

## Frontend Design Skill Setup (Recommended)

Pygmalion can use the `frontend-design` skill to generate distinctive, production-grade web interfaces with bold aesthetics.

### Option 1: Install via Claude Code (Global)

If you have Claude Code installed:

```bash
claude /plugin marketplace add anthropics/claude-code
claude /plugin install frontend-design@anthropics-claude-code
```

This installs to `~/.claude/skills/` and is available for all projects.

### Option 2: Install to Project Directory (Local)

Install to this project only:

```bash
mkdir -p .claude/skills/frontend-design
curl -o .claude/skills/frontend-design/SKILL.md \
  https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/frontend-design/skills/frontend-design/SKILL.md
```

### Verification

Run `pygmalion` and type `/status`. You should see:
```
Skills: frontend-design
```

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

### Auto-Opening Files

Pygmalion automatically opens created files in the appropriate application:
- **SVG files** → Inkscape
- **Image files** (PNG, JPG, etc.) → GIMP
- **HTML files** → Default browser

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
- Inkscape (for vector graphics)
- ImageMagick (for image processing)
- GIMP (for advanced raster editing)
- Chrome with Claude Code extension (for web preview)

### Python Dependencies

- `claude-agent-sdk` - Core agent functionality
- `python-dotenv` - Environment variable management
- `prompt-toolkit` - Enhanced command-line input with history and editing
- `weasyprint` (optional) - PDF generation
- `google-genai` (optional) - Gemini Imagen 4.0 integration (requires billing account)

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
