#!/bin/bash

# Gemini Coding MCP Server Installation Script
# This script installs the server to ~/.claude-mcp-servers/gemini_coding

set -e  # Exit on error

echo "🚀 Installing Gemini Coding MCP Server..."
echo ""

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

# Compare versions
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $PYTHON_VERSION is installed, but version 3.8 or higher is required."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Set installation directory
INSTALL_DIR="$HOME/.claude-mcp-servers/gemini_coding"

# Create installation directory
echo "📁 Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy files
echo "📋 Copying files..."
cp -r . "$INSTALL_DIR/"

# Change to installation directory
cd "$INSTALL_DIR"

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    ./venv/Scripts/pip install -r requirements.txt
else
    # macOS/Linux
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

# Make installation script executable
chmod +x install.sh 2>/dev/null || true

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Get your Gemini API key from: https://aistudio.google.com/app/apikey"
echo "2. Configure Claude Code by adding the following to your MCP configuration:"
echo ""

# Detect OS and show appropriate config
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_PATH="~/Library/Application Support/Claude/claude_desktop_config.json"
    PYTHON_PATH="$INSTALL_DIR/venv/bin/python"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    CONFIG_PATH="%APPDATA%\\Claude\\claude_desktop_config.json"
    PYTHON_PATH="$INSTALL_DIR\\venv\\Scripts\\python.exe"
else
    # Linux
    CONFIG_PATH="~/.config/Claude/claude_desktop_config.json"
    PYTHON_PATH="$INSTALL_DIR/venv/bin/python"
fi

echo "Configuration file location: $CONFIG_PATH"
echo ""
echo '{
  "mcpServers": {
    "gemini-coding": {
      "command": "'$PYTHON_PATH'",
      "args": ["'$INSTALL_DIR/server.py'"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}'
echo ""
echo "3. Replace 'your-api-key-here' with your actual Gemini API key"
echo "4. Restart Claude Code"
echo ""
echo "🎉 Enjoy using Gemini Coding MCP Server!"