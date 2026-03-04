# Development Guide

This guide covers setting up a development environment, running tests, code style guidelines, and contributing to Read Receipt.

## Table of Contents

- [Development Environment](#development-environment)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Contributing Process](#contributing-process)
- [Branch Strategy](#branch-strategy)
- [Code Review](#code-review)
- [Release Process](#release-process)

## Development Environment

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- PostgreSQL (optional, SQLite for development)
- Chrome or Firefox (for extension testing)

### Clone Repository

```bash
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt
```

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov ruff black mypy pre-commit

# Initialize database
export SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3
export ADMIN_TOKEN=dev-token-123

# Run database migrations
flask db init  # Only once
flask db migrate -m "Initial migration"
flask db upgrade
```

### Frontend Setup

```bash
cd admin-dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

### Extension Setup

Load the extension in development mode:

**Chrome:**
1. Go to `chrome://extensions/`
2. Enable Developer Mode
3. Click "Load unpacked"
4. Select `extensions/chrome` folder

**Firefox:**
1. Go to `about:debugging`
2. Click "This Firefox"
3. Click "Load Temporary Add-on"
4. Select `extensions/firefox/manifest.json`

### Pre-commit Hooks

Install pre-commit hooks for automatic linting:

```bash
pip install pre-commit
pre-commit install
```

Pre-commit hooks will run on every commit:
- Ruff linting
- Black formatting
- MyPy type checking
- YAML validation
- Secret detection

### Development Server

**Backend:**
```bash
# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export ADMIN_TOKEN=dev-token-123

# Run with auto-reload
flask run --reload --debug
```

**Frontend:**
```bash
cd admin-dashboard
npm run dev
```

**Both:**
Use separate terminal tabs or a process manager like `tmux` or `concurrently`.

## Running Tests

### Backend Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_readreceipt.py -v

# Run specific test function
pytest tests/test_readreceipt.py::test_new_uuid -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# Run tests matching pattern
pytest -k "test_admin" -v

# Run tests with markers
pytest -m slow -v
```

### Test Structure

Tests are located in `tests/` directory:

```
tests/
├── test_readreceipt.py      # Main test file
├── test_api.py              # API endpoint tests
├── test_models.py           # Database model tests
└── conftest.py              # Pytest fixtures and configuration
```

### Example Test

```python
import pytest
from app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_root_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.data == b''

def test_new_uuid(client):
    response = client.get('/new-uuid?description=Test&email=test@example.com')
    assert response.status_code == 200
    assert b'<p>' in response.data
    assert b'</p>' in response.data
```

### Frontend Tests

```bash
cd admin-dashboard

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- src/pages/Dashboard.test.jsx
```

### Extension Tests

(Future implementation)

```bash
cd extensions

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

### CI/CD Tests

Tests run automatically on:
- Every push to master/main
- Every pull request
- Scheduled runs (nightly)

View results in GitHub Actions tab.

## Code Style

### Python

We use the following tools for Python code quality:

**Ruff (Linting):**
```bash
ruff check .
ruff check --fix .
```

**Black (Formatting):**
```bash
black .
black --check .
```

**MyPy (Type Checking):**
```bash
mypy .
mypy --ignore-missing-imports .
```

**Configuration:**
See `pyproject.toml` for configuration:

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true
```

**Style Guidelines:**
- Line length: 88 characters
- Indentation: 4 spaces
- String quotes: Double quotes
- Type hints: Required for function signatures
- Docstrings: Google style

**Example:**
```python
from __future__ import annotations

from typing import Any

def create_recipient(
    email: str,
    description: str = ""
) -> dict[str, Any]:
    """Create a new recipient in the database.
    
    Args:
        email: Recipient email address
        description: Optional description
        
    Returns:
        Dictionary with recipient details
        
    Raises:
        ValueError: If email is invalid
    """
    if not email:
        raise ValueError("Email is required")
    
    # Implementation
    return {"email": email, "description": description}
```

### JavaScript/TypeScript

**ESLint (Linting):**
```bash
cd admin-dashboard
npm run lint
```

**Prettier (Formatting):**
```bash
npx prettier --write .
npx prettier --check .
```

**Configuration:**
See `admin-dashboard/.eslintrc` and `admin-dashboard/.prettierrc`

**Style Guidelines:**
- Line length: 100 characters
- Indentation: 2 spaces
- String quotes: Single quotes
- Semicolons: Required
- Arrow functions: Preferred

**Example:**
```javascript
import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * Dashboard component showing analytics overview
 * @param {Object} props - Component props
 * @param {string} props.title - Dashboard title
 */
function Dashboard({ title }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/admin/stats');
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="dashboard">
      <h1>{title}</h1>
      {/* Dashboard content */}
    </div>
  );
}

Dashboard.propTypes = {
  title: PropTypes.string.isRequired,
};

export default Dashboard;
```

### Browser Extensions

**JavaScript:**
- ES6+ features encouraged
- No build step (vanilla JS)
- JSDoc comments for documentation
- Strict mode enabled

**Example:**
```javascript
/**
 * Content script for Read Receipt extension
 * Injects tracking pixels into Gmail compose windows
 * @module content
 */

'use strict';

/**
 * Generate a unique UUID for tracking
 * @returns {string} Unique identifier in format xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
 */
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
```

### Git Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

**Format:**
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(extension): add support for Outlook.com

Add content script detection for Outlook.com compose windows.

Closes #42

---

fix(api): resolve database connection issue

Fix connection pooling configuration to prevent timeout errors.

Fixes #38

---

docs(readme): update installation instructions

Add detailed steps for Windows installation.
```

## Contributing Process

### 1. Find an Issue

- Check [GitHub Issues](https://github.com/yasn77/readreceipt/issues)
- Look for labels: `good first issue`, `help wanted`
- Comment on issue to claim it

### 2. Fork Repository

```bash
# Fork on GitHub, then clone
git clone https://github.com/YOUR_USERNAME/readreceipt.git
cd readreceipt

# Add upstream remote
git remote add upstream https://github.com/yasn77/readreceipt.git
```

### 3. Create Branch

```bash
# Sync with upstream
git checkout master
git pull upstream master

# Create feature branch
git checkout -b feature/your-feature-name
```

### 4. Make Changes

- Write code
- Write tests
- Update documentation
- Follow code style guidelines

### 5. Test Locally

```bash
# Run all tests
pytest
npm test

# Run pre-commit hooks
pre-commit run --all-files

# Build frontend
cd admin-dashboard
npm run build
```

### 6. Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat(extension): add your feature description"
```

### 7. Push to GitHub

```bash
git push origin feature/your-feature-name
```

### 8. Create Pull Request

1. Go to your fork on GitHub
2. Click "Compare & pull request"
3. Fill in PR template:
   - Description of changes
   - Related issues
   - Testing done
   - Screenshots (if applicable)
4. Submit PR

### 9. Address Review Feedback

- Respond to comments
- Make requested changes
- Push additional commits
- Request re-review

### 10. Merge

Once approved:
- Maintainer will merge PR
- Delete feature branch
- Celebrate! 🎉

## Branch Strategy

### Branch Types

**master:**
- Production-ready code
- Protected branch
- Requires PR and approval
- Deployed automatically

**feature/\*:**
- New features
- Branch from master
- Merge back to master via PR
- Example: `feature/outlook-support`

**fix/\*:**
- Bug fixes
- Branch from master
- Merge back to master via PR
- Example: `fix/database-timeout`

**hotfix/\*:**
- Critical production fixes
- Branch from master
- Expedited review
- Example: `hotfix/security-patch`

**docs/\*:**
- Documentation updates
- Can be merged directly by maintainers
- Example: `docs/api-reference`

### Branch Naming

Format: `<type>/<description>`

**Examples:**
- `feature/chrome-extension-improvements`
- `fix/analytics-export-bug`
- `docs/deployment-guide`
- `test/api-endpoints`

**Rules:**
- Use lowercase
- Use hyphens as separators
- Be descriptive but concise
- Include issue number if applicable: `feature/42-outlook-support`

## Code Review

### Reviewer Guidelines

**Check:**
- Code follows style guidelines
- Tests are included and passing
- Documentation is updated
- No security vulnerabilities
- Performance implications considered
- Edge cases handled

**Provide Feedback:**
- Be constructive and respectful
- Explain reasoning
- Suggest alternatives
- Approve when ready

### Reviewer Checklist

- [ ] Code compiles without errors
- [ ] Tests pass locally
- [ ] Tests cover new functionality
- [ ] Documentation updated
- [ ] No sensitive data exposed
- [ ] Follows project conventions
- [ ] No unnecessary dependencies
- [ ] Error handling adequate

### PR Template

```markdown
## Description
Brief description of changes

## Related Issue
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] Manual testing performed
- [ ] All tests passing

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

**Format:** `MAJOR.MINOR.PATCH`

**Examples:**
- `1.0.0` - Initial release
- `1.1.0` - New features, backwards compatible
- `1.1.1` - Bug fixes
- `2.0.0` - Breaking changes

### Release Steps

1. **Update Version Numbers:**
   - `pyproject.toml`
   - `admin-dashboard/package.json`
   - Extension manifests
   - Helm chart

2. **Update CHANGELOG:**
   - Add new entries
   - Categorise changes
   - Link to PRs/issues

3. **Create Release Branch:**
   ```bash
   git checkout -b release/v1.2.0
   ```

4. **Final Testing:**
   - Run all tests
   - Manual QA testing
   - Performance testing

5. **Merge to Master:**
   - Create PR
   - Get approval
   - Merge

6. **Tag Release:**
   ```bash
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```

7. **Publish:**
   - Create GitHub release
   - Publish to package registries
   - Update documentation

8. **Deploy:**
   - Deploy to production
   - Monitor for issues
   - Communicate to users

### Release Notes Template

```markdown
## [1.2.0] - 2024-01-15

### Added
- Support for Outlook.com (#42)
- New analytics export feature (#38)
- Dark mode for admin dashboard (#35)

### Changed
- Improved tracking pixel injection performance
- Updated dependencies to latest versions

### Fixed
- Database connection timeout issue (#40)
- Analytics chart rendering bug (#37)

### Deprecated
- Python 3.10 support (use 3.11+)

### Security
- Fixed XSS vulnerability in recipient description
```

## Getting Help

- **Documentation:** Check other docs in this directory
- **Issues:** [GitHub Issues](https://github.com/yasn77/readreceipt/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yasn77/readreceipt/discussions)
- **Code of Conduct:** Be respectful and inclusive

---

**Ready to contribute?** Start with a [good first issue](https://github.com/yasn77/readreceipt/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).
