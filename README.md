# 🤖 Gemini Coding MCP Server

An IDE-friendly MCP server that integrates Google's Gemini AI with Claude Code for enhanced coding assistance.

## ✨ Features

- **15 Specialized Coding Tools**: From code review to debugging assistance
- **IDE-Optimized**: Seamless clipboard integration, file reading, and environment variable support
- **Conflict-Free Commands**: All commands prefixed with `gc` to avoid conflicts
- **Multiple Input Methods**: Direct text, file paths, clipboard, or environment variables
- **Smart Caching**: Improves response times for repeated queries
- **Long Text Support**: Handles up to 100KB of input

## 📋 Prerequisites

- Python 3.8 or higher
- [Gemini API Key](https://aistudio.google.com/app/apikey)
- Claude Code application

## 🚀 Installation

### Step 1: Clone and Install

```bash
# Clone to the standard MCP servers location
git clone https://github.com/YOUR_USERNAME/gemini-coding.git ~/.claude-mcp-servers/gemini-coding

# Navigate to the directory
cd ~/.claude-mcp-servers/gemini-coding

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set Up Gemini API Key

Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey) and set it as an environment variable:

```bash
# macOS/Linux
export GEMINI_API_KEY="your-api-key-here"

# Windows
set GEMINI_API_KEY=your-api-key-here
```

### Step 3: Configure Claude Code

Add the server to your Claude Code MCP configuration:

#### macOS
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-coding": {
      "command": "python",
      "args": ["~/.claude-mcp-servers/gemini-coding/server.py"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Windows
Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-coding": {
      "command": "python",
      "args": ["%USERPROFILE%\\.claude-mcp-servers\\gemini-coding\\server.py"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Linux
Edit `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-coding": {
      "command": "python",
      "args": ["~/.claude-mcp-servers/gemini-coding/server.py"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Step 4: Restart Claude Code

After updating the configuration, restart Claude Code to load the new MCP server.

## 🎯 Quick Start Guide

### Basic Usage

All commands follow the pattern: `mcp__gemini-coding__[command] [parameters]`

#### Get Help
```bash
mcp__gemini-coding__gchelp                    # Show all commands
mcp__gemini-coding__gchelp category="code"    # Show code-related commands
mcp__gemini-coding__gchelp category="ide"     # Show IDE workflow tips
```

#### Ask Questions
```bash
# Direct question
mcp__gemini-coding__gcask prompt="What are Python decorators?"

# From clipboard (copy code first)
mcp__gemini-coding__gcask prompt="Explain this code"

# From file
mcp__gemini-coding__gcask file_path="complex_algorithm.py" prompt="How does this work?"
```

### IDE Workflow Examples

#### Code Review Workflow
1. Select code in your IDE
2. Copy (Cmd/Ctrl+C)
3. Run: `mcp__gemini-coding__gcreview focus="security"`

#### Debug Error Messages
1. Copy error from terminal
2. Run: `mcp__gemini-coding__gcdebug`

#### Analyze Entire Files
```bash
mcp__gemini-coding__gcreview file_path="src/auth.py" focus="security"
mcp__gemini-coding__gctest file_path="utils.py" type="unit"
mcp__gemini-coding__gcperf file_path="slow_function.py"
```

## 📚 Command Reference

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `gchelp` | Show available commands | `gchelp category="all"` |
| `gcask` | Ask Gemini any question | `gcask prompt="How to optimize loops?"` |

### Specification & Design

| Command | Description | Example |
|---------|-------------|---------|
| `gcspec` | Analyze requirements | `gcspec file_path="requirements.md" type="api"` |
| `gcarch` | Review architecture | `gcarch architecture="microservices design" focus="scalability"` |
| `gcapi` | Design APIs | `gcapi type="REST" requirements="user authentication"` |

### Code Analysis

| Command | Description | Example |
|---------|-------------|---------|
| `gcreview` | Review code quality | `gcreview file_path="main.py" focus="security"` |
| `gcrefactor` | Suggest improvements | `gcrefactor goal="readability"` (uses clipboard) |
| `gcperf` | Analyze performance | `gcperf context="database queries"` |
| `gcsecurity` | Security audit | `gcsecurity level="enterprise"` |
| `gctest` | Generate test strategy | `gctest type="integration"` |

### Debug & Understanding

| Command | Description | Example |
|---------|-------------|---------|
| `gcdebug` | Debug errors | `gcdebug` (paste error first) |
| `gcexplain` | Explain code | `gcexplain level="beginner"` |

### Utility Tools

| Command | Description | Example |
|---------|-------------|---------|
| `gcdeps` | Analyze dependencies | `gcdeps file_path="package.json" focus="security"` |
| `gccomplete` | Complete code | `gccomplete context="class User:" request="add login method"` |
| `gcdocs` | Generate documentation | `gcdocs type="api"` |

## 🔧 Advanced Features

### Multiple Input Methods

All commands support these input methods:

1. **Direct Text**: Pass text directly in the command
2. **File Path**: Use `file_path` parameter to analyze files
3. **Clipboard**: Leave text parameters empty to use clipboard content
4. **Environment Variable**: Set `GEMINI_INPUT` for programmatic use

### Performance Optimization

- Commands with temperature ≤ 0.3 are cached for 5 minutes
- Use `fast=true` with `gcask` for quicker responses with Gemini Flash model

### IDE Integration Tips

- Most effective with modern IDEs like VS Code, Cursor, or Windsurf
- Clipboard integration requires `pyperclip` (included in requirements)
- File paths can be relative or absolute

## 🐛 Troubleshooting

### Common Issues

**"Gemini not available" error**
- Check your `GEMINI_API_KEY` environment variable
- Ensure you have internet connectivity
- Verify your API key is valid

**"No input provided" error**
- Ensure you've copied text to clipboard before running commands
- Check file paths are correct
- Try providing text directly in the command

**Commands not found**
- Restart Claude Code after configuration changes
- Verify the server name is exactly "gemini-coding" in config
- Check Python path in configuration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Links

- [Gemini API Documentation](https://ai.google.dev/docs)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)