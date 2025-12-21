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

## Usage

```bash
# Start the interactive CLI
pygmalion

# Or run the module directly
python -m pygmalion.main
```

### Example Session

Pygmalion maintains conversation context, so you can iterate on designs:

```
🎨 You: Create a responsive navigation bar with a logo and three menu items

🤖 Pygmalion: [Claude generates the HTML, CSS, and provides explanations]

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

## Requirements

### System Dependencies

- Python 3.10+
- Inkscape (for vector graphics)
- ImageMagick (for image processing)
- Chrome with Claude Code extension (for web preview)

### Python Dependencies

- `claude-agent-sdk` - Core agent functionality
- `python-dotenv` - Environment variable management
- `weasyprint` (optional) - PDF generation
- `google-generativeai` (optional) - Gemini integration

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

## Development Status

This project is being built incrementally:

- [x] Phase 1: Basic SDK setup with `query()`
- [x] Phase 2: Persistent sessions with `ClaudeSDKClient`
- [x] Phase 3: Built-in tools (Read/Write/Edit/Bash)
- [x] Phase 4: Permission modes and autonomy
- [x] Phase 5: Front-end design skill
- [x] Phase 6: Inkscape integration
- [ ] Phase 7: ImageMagick integration
- [ ] Phase 8: GIMP integration
- [ ] Phase 9: PDF generation (WeasyPrint)
- [ ] Phase 10: Optional Gemini integration
- [ ] Phase 11: GitHub integration
- [ ] Phase 12: Figma/Canva integration (optional)
- [ ] Phase 13: Design system prompts
- [ ] Phase 14: Logging and error handling
- [ ] Phase 15: CLI polish
- [ ] Phase 16: Session export
- [ ] Phase 17: Chrome extension workflow

## License

MIT
