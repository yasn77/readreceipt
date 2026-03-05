# Contributing to Read Receipt

Thank you for your interest in contributing to Read Receipt! This document provides comprehensive guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Review](#code-review)
- [Recognition](#recognition)

## Code of Conduct

### Our Pledge

We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone.

### Our Standards

Examples of behaviour that contributes to a positive environment:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Examples of unacceptable behaviour:

- The use of sexualised language or imagery
- Trolling, insulting/derogatory comments
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt
```

### 2. Set Up Python Environment with mise

We use `mise` for environment and tool management:

```bash
# Install mise (if not already installed)
curl https://mise.run | sh

# Install Python, uv, and all development tools
mise install

# This will:
# - Install Python 3.11
# - Install uv package manager
# - Install ruff, black, mypy, pytest, pre-commit
# - Create and activate virtual environment automatically
```

The virtual environment will be automatically created in `.venv/` and activated when you enter the project directory (if you have direnv installed).

### Alternative: Manual Setup (without mise)

```bash
# Install Python 3.11+
# Install uv package manager
pip install uv

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### 3. Set Up Node.js Environment

```bash
# Install Node.js via mise
mise use node@20

# Install admin dashboard dependencies
cd admin-dashboard
npm install
```

### 4. Install Pre-commit Hooks

```bash
mise run precommit
# or manually:
pre-commit install
```

### Useful mise Commands

```bash
# Install dependencies
mise run install

# Run tests
mise run test

# Run tests with coverage
mise run test-cov

# Lint code
mise run lint

# Format code
mise run format

# Type check
mise run typecheck

# Run the application
mise run dev

# Clean build artifacts
mise run clean

# See all available tasks
mise run
```

## Code Style

### Python

- Follow PEP-8 guidelines
- Use `ruff` for linting
- Use `black` for formatting (line-length: 88)
- Add type annotations to all functions
- Write docstrings for public functions and classes

```bash
# Lint
ruff check .

# Format
black .

# Type check
mypy .
```

### JavaScript/TypeScript

- Use ESLint for linting
- Follow React best practices
- Use functional components with hooks
- Add PropTypes or TypeScript types

```bash
cd admin-dashboard
npm run lint
```

## Testing

### Running Tests

```bash
# Backend tests
pytest

# Frontend tests
cd admin-dashboard
npm test

# All tests with coverage
pytest --cov=app --cov-fail-under=90
```

### Test Coverage

We require **>90% test coverage** for all contributions. Coverage is enforced in CI.

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage
open htmlcov/index.html
```

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/description
git checkout -b fix/description
git checkout -b refactor/description
```

### 2. Make Changes

- Write code following existing patterns
- Add tests for new functionality
- Update documentation if needed
- Run pre-commit hooks

### 3. Commit Messages

Follow conventional commits:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Format code
refactor: Refactor code
test: Add tests
chore: Update dependencies
```

Example:
```bash
git commit -m "feat: Add analytics endpoint for geographic data"
```

### 4. Open a Pull Request

1. Push to your branch: `git push origin feature/description`
2. Navigate to the repository on GitHub
3. Click "New Pull Request"
4. Select your branch
5. Fill in the PR template

### 5. PR Requirements

- [ ] All tests pass
- [ ] Coverage >90%
- [ ] CI pipeline succeeds
- [ ] Code reviewed and approved
- [ ] Documentation updated

### 6. Review Process

- A reviewer will review your code
- Address any comments or suggestions
- Once approved, the PR will be merged

## Issue Reporting

### Bug Reports

1. Check if the issue already exists
2. Use the bug report template
3. Include:
   - Clear description
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (Python version, OS, etc.)

### Feature Requests

1. Check if the feature already exists or is planned
2. Use the feature request template
3. Include:
   - Clear description
   - Use case
   - Proposed solution (optional)

## Documentation

When adding new features, update:

- README.md (if user-facing changes)
- API documentation (if new endpoints)
- Code comments and docstrings
- Inline type hints

## Agile Stories

User stories are stored in the `stories/` directory. When implementing a feature:

1. Check the relevant story file
2. Ensure all acceptance criteria are met
3. Update the story file if needed

## CI/CD

All PRs trigger the CI pipeline:

1. Linting (ruff, black, mypy)
2. Testing (pytest, Jest)
3. Coverage check (>90%)
4. Build validation

## Questions?

Feel free to open an issue with the "question" label for any questions about contributing.

## Getting Help

- **Documentation:** Check [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/yasn77/readreceipt/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yasn77/readreceipt/discussions)

## Recognition

### Contributors

We recognise all contributors:
- Name in CONTRIBUTORS file
- GitHub profile in repository insights
- Mention in release notes for significant contributions

### Significant Contributions

For major contributions:
- Co-author credit on commits
- Featured in release announcements
- Invitation to become a maintainer (for sustained contributions)

## Thank You!

Your contributions make Read Receipt better for everyone. We appreciate your time and effort! 🎉

---

**Last Updated:** 2024-01-15
**License:** MIT
