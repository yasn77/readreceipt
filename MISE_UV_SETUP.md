# Mise & UV Setup Guide

## Overview

This project uses **mise** for environment and tool version management, and **uv** for Python package management. This combination provides:

- **Fast, reproducible environments** - uv is 10-100x faster than pip
- **Automatic tool management** - mise installs and manages Python, uv, and all dev tools
- **Task automation** - mise tasks replace manual commands with simple aliases
- **Cross-platform compatibility** - Works on Linux, macOS, and Windows

## Quick Start

### 1. Install mise

```bash
# macOS/Linux
curl https://mise.run | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://mise.run | iex"
```

Restart your shell or run:
```bash
source ~/.bashrc  # or ~/.zshrc, ~/.bash_profile, etc.
```

### 2. Set Up the Project

```bash
# Clone and enter the project
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt

# Install all tools and create virtual environment
mise install
```

This will automatically:
- Install Python 3.11
- Install uv package manager
- Install ruff, black, mypy, pytest, pre-commit
- Create a virtual environment in `.venv/`

### 3. Install Dependencies

```bash
# Install Python dependencies with uv
mise run install
```

### 4. Set Environment Variables

```bash
export ADMIN_TOKEN=your-secure-token
export SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
```

### 5. Run the Application

```bash
# Development mode with auto-reload
mise run dev

# Or production mode
mise run run
```

## Available mise Tasks

Run `mise run` to see all available tasks:

```bash
# Installation
mise run install          # Install all dependencies
mise run install-dev      # Install dev dependencies + pre-commit hooks

# Running
mise run run              # Run the application
mise run dev              # Run in development mode (FLASK_DEBUG=1)

# Testing
mise run test             # Run all tests
mise run test-cov         # Run tests with coverage
mise run test-html        # Run tests with HTML coverage report

# Code Quality
mise run lint             # Lint with ruff
mise run format           # Format with black
mise run format-check     # Check formatting (don't modify)
mise run typecheck        # Type check with mypy
mise run precommit        # Run pre-commit hooks

# Utilities
mise run clean            # Clean Python cache and artifacts
mise run clean-venv       # Remove virtual environment
mise run reset            # Clean and reinstall
mise run info             # Show project information
mise run docs             # Serve documentation locally
mise run build-docs       # Build documentation
```

## Project Configuration

### .mise.toml

The `.mise.toml` file configures everything:

```toml
[settings]
# Use uv to create and manage virtual environments
python.uv_venv_auto = "create|source"

[env]
# Project configuration
PROJECT_NAME = "readreceipt"

# All environment variables managed by mise
ADMIN_TOKEN = "{{ env.ADMIN_TOKEN | default='change-me-in-production' }}"
SQLALCHEMY_DATABASE_URI = "{{ env.SQLALCHEMY_DATABASE_URI | default='sqlite:///db.sqlite3' }}"
FLASK_ENV = "{{ env.FLASK_ENV | default='development' }}"

[tools]
python = "3.11"    # Python version
uv = "latest"      # Package manager
ruff = "latest"    # Linter
black = "latest"   # Formatter
```

**Key features:**
- `python.uv_venv_auto = "create|source"` - Automatically creates `.venv` with uv if missing
- Environment variables use template syntax with defaults
- Override any env var by setting it in your shell before running mise commands

### Environment Variables

All environment variables are managed by mise in `.mise.toml`. You can override them by setting them in your shell or creating a `.env` file:

```bash
# Set in shell
export ADMIN_TOKEN=your-secure-token
export SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost:5432/readreceipt

# Or create a .env file (not committed to git)
echo "ADMIN_TOKEN=your-secure-token" >> .env
echo "SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost:5432/readreceipt" >> .env
```

Mise will automatically load these when you run `mise run` commands.

## Using uv Directly

While mise tasks are recommended, you can also use uv directly:

```bash
# Install dependencies
uv pip install -r requirements.txt

# Install a package
uv pip install flask

# Uninstall a package
uv pip uninstall flask

# List installed packages
uv pip list

# Check for outdated packages
uv pip compile --upgrade requirements.in

# Create a lock file
uv pip compile requirements.in -o requirements.txt
```

## Migration from pip/venv

If you're migrating from a traditional pip/venv setup:

### 1. Remove old virtual environment
```bash
rm -rf venv/
```

### 2. Install mise and set up
```bash
curl https://mise.run | sh
mise install
```

### 3. Install dependencies with uv
```bash
mise run install
```

### 4. Update your workflow
Replace:
- `pip install -r requirements.txt` → `mise run install`
- `python app.py` → `mise run dev`
- `pytest` → `mise run test`
- `black .` → `mise run format`

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) uses mise:

```yaml
- name: Set up mise
  uses: jdx/mise-action@v2
  with:
    install: true

- name: Install dependencies
  run: mise run install

- name: Run tests
  run: mise run test
```

## Troubleshooting

### mise not found
Ensure mise is in your PATH:
```bash
echo 'export PATH="$HOME/.local/share/mise/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Virtual environment not activating
Mise automatically activates the venv when you run `mise run` commands. To verify:
```bash
mise run info
# Should show: Virtual Environment: /path/to/readreceipt/.venv
```

Or manually check:
```bash
which python
# Should point to: /path/to/readreceipt/.venv/bin/python
```

### Tool versions not matching
Refresh mise tools:
```bash
mise install --force
```

### Dependencies not installing
Clear uv cache and retry:
```bash
uv cache clean
mise run install
```

### Environment variables not set
Override defaults by setting them before running mise:
```bash
export ADMIN_TOKEN=my-token
mise run dev
```

Or create a `.env` file in the project root:
```bash
ADMIN_TOKEN=my-token
SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
```

### Venv not created by uv
Force recreation:
```bash
mise run clean-venv
mise install
```

## Benefits

### Speed
- **uv** is 10-100x faster than pip
- **mise** caches all tools for instant access
- Parallel dependency resolution

### Reproducibility
- Exact tool versions in `.mise.toml`
- Lock files for dependencies
- Consistent environments across machines

### Developer Experience
- Simple commands (`mise run test`)
- Automatic environment activation
- No manual venv management
- Cross-platform compatibility

### Best Practices
- Latest tool versions
- Security updates via mise
- Standardised development workflow
- Easy onboarding for new contributors

## Resources

- [mise documentation](https://mise.jdx.dev/)
- [uv documentation](https://docs.astral.sh/uv/)
- [mise cookbook](https://mise.jdx.dev/mise-cookbook.html)
- [Python with mise](https://mise.jdx.dev/lang/python.html)

## Support

For issues or questions:
1. Check the [mise docs](https://mise.jdx.dev/)
2. Check the [uv docs](https://docs.astral.sh/uv/)
3. Open an issue on GitHub
4. Ask in the project's discussion forum
