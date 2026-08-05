# Skills Installation Guide

This guide explains how to install dependencies for Claude Code skills.

## Overview

Skills are organized into groups with Python utility scripts. Each skill's scripts directory contains a `requirements.txt` file listing dependencies.

## Automated Installation (Recommended)

Use the provided installation scripts for automated setup:

> **Running the script by hand?** When `tkm` runs these scripts it passes its
> version so the installer can check the kit's minimum required CLI version. If
> you invoke `install.sh` / `install.ps1` yourself (no `tkm`) and the kit
> declares a minimum, the script refuses to run. Prepend
> `TKM_SKIP_CLI_VERSION_CHECK=1` to override:
>
> ```bash
> TKM_SKIP_CLI_VERSION_CHECK=1 ./install.sh          # Linux/macOS
> $env:TKM_SKIP_CLI_VERSION_CHECK=1; .\install.ps1   # Windows
> ```

### Linux/macOS

```bash
cd .claude/skills
chmod +x install.sh
./install.sh
```

The script will:
- Detect your OS (Linux or macOS)
- Install package managers (Homebrew for macOS, apt-get for Linux)
- Install system dependencies (FFmpeg, ImageMagick)
- Install Node.js and global packages (rmbg-cli, pnpm, wrangler, repomix)
- Create Python virtual environment
- Install Python packages for all skills
- Install test dependencies
- Verify all installations

### Windows (PowerShell)

Run as Administrator:

```powershell
cd .claude\skills
Set-ExecutionPolicy Bypass -Scope Process -Force
.\install.ps1
```

Options:
```powershell
# Skip Chocolatey installation if already installed
.\install.ps1 -SkipChocolatey

# Show help
.\install.ps1 -Help
```

The script will:
- Install Chocolatey package manager (if needed)
- Install system dependencies (FFmpeg, ImageMagick)
- Install Node.js and global packages
- Create Python virtual environment
- Install Python packages
- Verify all installations

### What Gets Installed

**System Tools:**
- FFmpeg (video/audio processing)
- ImageMagick (image processing)

**Node.js Packages (global):**
- rmbg-cli (AI background removal)
- pnpm (package manager)
- wrangler (Cloudflare CLI)
- repomix (repository packaging)

**Python Packages:**
- pypdf, python-docx (document processing)
- Pillow (image processing)
- pytest, pytest-cov (testing)

## Manual Installation

If you prefer manual installation or the automated script fails:

## Quick Start

### Option 1: Install All Dependencies (Recommended)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies for every skill that ships a requirements.txt
for req in .claude/skills/*/scripts/requirements.txt .claude/skills/*/requirements.txt; do
  [ -f "$req" ] && pip install -r "$req"
done

# Install test dependencies for development
pip install pytest pytest-cov pytest-mock
```

### Option 2: Install Per-Skill

Navigate to a specific skill and install its requirements (only skills that ship a `requirements.txt`):

```bash
cd .claude/skills/<skill-name>/scripts
pip install -r requirements.txt
```

## Skills Dependencies

### Python Package Dependencies

Most skills use only the Python standard library. Skills that need external packages ship their own `scripts/requirements.txt` (e.g. `audio-transcribe`, `devops`, `pack-codebase`, `translate-file`, document-processing skills). Common packages across these:

- `pypdf` - PDF processing
- `python-docx` - DOCX conversion
- `Pillow` - Image processing
- `markdown` - Markdown processing
- `python-dotenv` - Environment variables

Install them per-skill from each skill's `requirements.txt`, or all at once with the loop in Quick Start above.

### System Tool Dependencies

Several skills require external CLI tools:

#### Image/Video CLI Tools
- **FFmpeg**: Video/audio processing
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: `choco install ffmpeg`
- **ImageMagick**: Image processing
  - Ubuntu/Debian: `sudo apt-get install imagemagick`
  - macOS: `brew install imagemagick`
  - Windows: `choco install imagemagick`
- **RMBG CLI**: AI background removal
  - All platforms: `npm install -g rmbg-cli`

#### devops
- **Cloudflare Wrangler**: `npm install -g wrangler`
- **Docker**: https://docs.docker.com/get-docker/
- **Google Cloud CLI**: https://cloud.google.com/sdk/docs/install

#### better-auth, repomix
- **Node.js 18+**: https://nodejs.org/
- **Better Auth**: `npm install better-auth`
- **Repomix**: `npm install -g repomix`

#### databases
- **PostgreSQL client**: `sudo apt-get install postgresql-client` (Linux)
- **MongoDB Shell**: https://www.mongodb.com/try/download/shell
- **MongoDB Tools**: https://www.mongodb.com/try/download/database-tools

#### web-frameworks, ui-styling
- **Node.js 18+**: https://nodejs.org/
- **pnpm**: `npm install -g pnpm`
- **yarn**: `npm install -g yarn`

## Installation by Platform

### Linux (Ubuntu/Debian)

```bash
# Python environment
python3 -m venv .venv
source .venv/bin/activate

# Python packages (skills that ship a requirements.txt)
for req in .claude/skills/*/scripts/requirements.txt .claude/skills/*/requirements.txt; do
  [ -f "$req" ] && pip install -r "$req"
done

# System tools
sudo apt-get update
sudo apt-get install -y ffmpeg imagemagick postgresql-client

# Node.js and tools
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g pnpm wrangler repomix rmbg-cli @shopify/cli
```

### macOS

```bash
# Python environment
python3 -m venv .venv
source .venv/bin/activate

# Python packages (skills that ship a requirements.txt)
for req in .claude/skills/*/scripts/requirements.txt .claude/skills/*/requirements.txt; do
  [ -f "$req" ] && pip install -r "$req"
done

# System tools via Homebrew
brew install ffmpeg imagemagick postgresql

# Node.js and tools
brew install node
npm install -g pnpm wrangler repomix rmbg-cli @shopify/cli
```

### Windows

```powershell
# Python environment
python -m venv .venv
.venv\Scripts\activate

# Python packages (install each skill's requirements.txt that exists)
Get-ChildItem .claude\skills\*\scripts\requirements.txt, .claude\skills\*\requirements.txt -ErrorAction SilentlyContinue | ForEach-Object { pip install -r $_.FullName }

# System tools via Chocolatey
choco install ffmpeg imagemagick nodejs

# Node.js tools
npm install -g pnpm wrangler repomix rmbg-cli @shopify/cli
```

## Testing Dependencies

All skills include test dependencies in `requirements.txt`:

```txt
pytest>=8.0.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
```

To run tests for a skill:

```bash
cd .claude/skills/{skill-name}/scripts
python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

## Environment Variables

Skills respect environment variable loading priority:

1. **process.env** (highest priority - runtime environment)
2. **`.claude/skills/{skill-name}/.env`** (skill-specific config)
3. **`.claude/skills/.env`** (shared skills config)
4. **`.claude/.env`** (global Claude config)

Example `.env` files are provided where needed (e.g., `devops/.env.example`).

## Troubleshooting

### "externally-managed-environment" Error

If you see this error when installing packages:

```bash
# Use virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Or use pipx for CLI tools
pipx install <package-name>
```

### Missing System Tools

If scripts fail with "command not found":

```bash
# Check if tool is installed
which ffmpeg
which docker
which node

# Verify tool works
ffmpeg -version
docker --version
node --version
```

### Permission Errors

On Linux/macOS, you may need to make scripts executable:

```bash
chmod +x .claude/skills/*/scripts/*.py
```

## Minimal Installation

If you only want to use specific skills:

**For document-processing skills only:**
```bash
pip install pypdf python-docx markdown Pillow python-dotenv
```

**For image/video CLI tools (FFmpeg, ImageMagick, RMBG) only:**
```bash
# macOS
brew install ffmpeg imagemagick
npm install -g rmbg-cli

# Linux
sudo apt-get install ffmpeg imagemagick
npm install -g rmbg-cli

# Windows
choco install ffmpeg imagemagick
npm install -g rmbg-cli
```

**For other skills:**
Most other skills (better-auth, repomix, devops, web-frameworks, ui-styling, databases) use only Python stdlib and require no `pip install`.

## Development Setup

For contributors working on skills:

```bash
# Install all test dependencies
pip install pytest pytest-cov pytest-mock

# Install pre-commit hooks (if available)
pre-commit install

# Run all tests
pytest .claude/skills/*/scripts/tests/ -v

# Check coverage across all skills
pytest .claude/skills/*/scripts/tests/ --cov=.claude/skills --cov-report=html
```

## Skill-Specific Notes

### Image/Video CLI Tools
- FFmpeg must be in PATH
- ImageMagick must be in PATH
- RMBG CLI must be installed globally
- Test with: `ffmpeg -version`, `convert -version`, and `rmbg --version`

### devops
- Cloudflare: Requires `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`
- GCloud: Requires `GOOGLE_APPLICATION_CREDENTIALS` path to service account JSON
- Docker: Must have Docker daemon running

## Getting Help

If dependencies fail to install or scripts don't work:

1. Check the skill's `scripts/requirements.txt` for specific versions
2. Verify system tools are installed and in PATH
3. Check environment variables are set correctly
4. Review skill's `SKILL.md` for additional setup instructions
5. Open an issue: https://github.com/anthropics/claude-code/issues
