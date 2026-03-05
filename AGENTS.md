# AI Agent Guidelines for Read Receipt

This document provides comprehensive guidelines for AI agents working on the Read Receipt repository.

## Repository Overview

**Read Receipt** is a comprehensive email tracking system with:
- Flask backend with admin/analytics API endpoints
- React + Vite admin dashboard
- Chrome and Firefox browser extensions
- Prometheus metrics, structured logging, and security hardening
- 90%+ test coverage requirement

## Tool Management

### Mise and UV (MANDATORY)

**All AI agents MUST use mise and uv for environment and package management.**

#### Setup (First Time)
```bash
# Install mise if not already installed
curl https://mise.run | sh

# Install all tools and create virtual environment
mise install
```

#### Common Tasks
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

# Run pre-commit hooks
mise run precommit

# Run the application
mise run dev
```

#### Adding New Tools
Add to `.mise.toml` in the `[tools]` section:
```toml
[tools]
new-tool = "latest"
```

Then run:
```bash
mise install
```

## Pre-Commit Requirements

**BEFORE EVERY COMMIT:**

1. **Run pre-commit hooks**
   ```bash
   mise run precommit
   ```

2. **Run tests with coverage**
   ```bash
   mise run test-cov
   ```

3. **Verify coverage is >80%**
   - Coverage must be at least 80% for all changes
   - If coverage drops, add more tests

4. **Fix any issues before committing**
   - No linting errors
   - No type checking errors
   - All tests passing
   - Coverage requirement met

## Testing Standards

### Coverage Requirement
- **Minimum: 80%** (hard requirement)
- **Target: 90%+** (goal for new code)

### Running Tests
```bash
# All tests
mise run test

# With coverage
mise run test-cov

# HTML coverage report
mise run test-html
```

### Writing Tests
- Test all new functionality
- Test edge cases and error conditions
- Use pytest fixtures for common setup
- Mock external dependencies
- Include integration tests for critical paths

### Test File Naming
- `test_*.py` for Python test files
- Place in `tests/` directory
- Mirror the structure of `app.py`

## Code Quality

### Python Code
- Follow PEP-8 guidelines
- Use type annotations for all functions
- Add docstrings to public functions and classes
- Use `ruff` for linting (configured in `pyproject.toml`)
- Use `black` for formatting (line-length: 88)
- Use `mypy` for type checking

### JavaScript/TypeScript Code
- Use ESLint for linting
- Follow React best practices
- Use functional components with hooks
- Add PropTypes or TypeScript types

### Pre-Commit Hooks
Configured in `.pre-commit-config.yaml`:
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON validation
- Ruff linting
- Black formatting
- Mypy type checking

## Environment Variables

All environment variables are managed by mise in `.mise.toml`:

```toml
[env]
ADMIN_TOKEN = "{{ env.ADMIN_TOKEN | default='change-me-in-production' }}"
SQLALCHEMY_DATABASE_URI = "{{ env.SQLALCHEMY_DATABASE_URI | default='sqlite:///db.sqlite3' }}"
FLASK_ENV = "{{ env.FLASK_ENV | default='development' }}"
```

### Overriding Variables
```bash
# In shell
export ADMIN_TOKEN=my-secure-token
mise run dev

# Or create .env file (add to .gitignore)
ADMIN_TOKEN=my-secure-token
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/db
```

## Commit Guidelines

### Before Committing Checklist
- [ ] Pre-commit hooks pass (`mise run precommit`)
- [ ] All tests pass (`mise run test`)
- [ ] Coverage >80% (`mise run test-cov`)
- [ ] No linting errors
- [ ] No type checking errors
- [ ] Code formatted with black

### Commit Message Format
Use conventional commits:
```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Format code
refactor: Refactor code
test: Add tests
chore: Update dependencies
```

### Example Commit
```bash
git add .
mise run precommit  # MUST run before commit
mise run test-cov   # MUST verify coverage
git commit -m "feat: Add new tracking endpoint

- Add /api/track endpoint for tracking events
- Add tests for new endpoint
- Update documentation"
```

## Security Guidelines

### Critical Security Rules
1. **Never commit secrets or API keys**
   - Use environment variables
   - Add to `.gitignore` if needed

2. **Input validation**
   - Validate all user inputs
   - Use bleach for sanitisation
   - Check length limits

3. **Authentication**
   - All admin endpoints require `@require_auth` decorator
   - Validate Authorization header
   - Never log tokens or passwords

4. **Security headers**
   - CSP headers present
   - HSTS enabled
   - X-Frame-Options: DENY

### Security Testing
```bash
# Run security tests
mise run test  # Includes test_security.py

# Check for vulnerabilities
pip-audit  # If installed
```

## Branch Strategy

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Refactoring
- `docs/description` - Documentation
- `test/description` - Test additions

### Pull Request Process
1. Create branch from master
2. Make changes
3. Run pre-commit and tests
4. Commit with conventional commit message
5. Push and create PR
6. Ensure all CI checks pass
7. Merge after approval

## Architecture Notes

### Backend (Flask)
- `app.py` - Main Flask application
- All endpoints require authentication (except public tracking pixel)
- SQLAlchemy ORM for database
- Prometheus metrics for monitoring
- Structured JSON logging

### Frontend (React)
- `admin-dashboard/` - React + Vite application
- Tailwind CSS for styling
- Recharts for analytics visualisations
- Axios for API calls

### Extensions
- `extensions/chrome/` - Chrome extension (Manifest V3)
- `extensions/firefox/` - Firefox extension (Manifest V2)
- `extensions/shared/` - Shared code
- Content scripts inject tracking pixels

### Database
- PostgreSQL (production) or SQLite (development)
- Migrations managed by Flask-Migrate
- Models: Recipients, Tracking, FailedEvent

## Common Workflows

### Adding a New Feature
```bash
# 1. Create branch
git checkout -b feature/new-feature

# 2. Install any new dependencies
# Add to requirements.txt
mise run install

# 3. Write code
# Edit files...

# 4. Write tests
# Add to tests/test_*.py

# 5. Run pre-commit and tests
mise run precommit
mise run test-cov

# 6. Commit
git add .
git commit -m "feat: Add new feature"

# 7. Push and create PR
git push origin feature/new-feature
```

### Fixing a Bug
```bash
# 1. Create branch
git checkout -b fix/bug-description

# 2. Fix the bug
# Edit files...

# 3. Add regression test
# Add to appropriate test file

# 4. Run pre-commit and tests
mise run precommit
mise run test

# 5. Commit
git add .
git commit -m "fix: Fix bug description"

# 6. Push and create PR
```

### Adding Dependencies
```bash
# 1. Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. Install with mise
mise run install

# 3. Add to .mise.toml if it's a dev tool
# [tools]
# new-tool = "latest"

# 4. Run mise install
mise install

# 5. Commit
git add requirements.txt .mise.toml
git commit -m "chore: Add new-package dependency"
```

## Troubleshooting

### Tests Failing
```bash
# Clean and reinstall
mise run clean
mise run install
mise run test
```

### Coverage Too Low
```bash
# Check what's missing
mise run test-cov

# Add tests for missing lines
# Edit tests/test_*.py

# Re-run tests
mise run test-cov
```

### Pre-Commit Failing
```bash
# See what failed
mise run precommit

# Fix the issues
# Run again
mise run precommit
```

### Environment Issues
```bash
# Recreate venv
mise run clean-venv
mise install
mise run install
```

## Resources

- **Mise Documentation**: https://mise.jdx.dev/
- **UV Documentation**: https://docs.astral.sh/uv/
- **Pytest Documentation**: https://docs.pytest.org/
- **Ruff Documentation**: https://docs.astral.sh/ruff/

## Questions?

If unsure about anything:
1. Check this document first
2. Check existing code for patterns
3. Run `mise run info` to see project state
4. Ask for clarification if needed

**Remember: Always run pre-commit and tests before committing!**
