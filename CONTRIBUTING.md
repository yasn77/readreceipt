# Contributing to Read Receipt

Thank you for considering contributing to Read Receipt! This document provides guidelines and instructions for contributing.

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt
```

### 2. Set Up Python Environment

We use `mise` for environment management:

```bash
# Install mise
curl https://mise.run | sh

# Install Python
mise use python@3.11

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
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
pip install pre-commit
pre-commit install
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

### 3. Sign-Off Your Commits

We require all commits to be signed off using the Developer Certificate of Origin (DCO). By signing off, you certify that you have the right to submit the code under the project's license.

Add the `-s` or `--signoff` flag to your commit command:

```bash
git commit -s -m "feat: Add analytics endpoint for geographic data"
```

This adds a `Signed-off-by` line to the commit message:

```
feat: Add analytics endpoint for geographic data

Signed-off-by: Your Name <your.email@example.com>
```

**Why sign-off?**
- Confirms you wrote the code or have the right to submit it
- Ensures contributions can be legally included in the project
- Follows industry best practices (Linux kernel, Kubernetes, etc.)

### 4. Commit Messages

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
git commit -s -m "feat: Add analytics endpoint for geographic data"
```

### 5. Open a Pull Request

1. Push to your branch: `git push origin feature/description`
2. Navigate to the repository on GitHub
3. Click "New Pull Request"
4. Select your branch
5. Fill in the PR template
6. Ensure your PR references the relevant issue (e.g., `Fixes #123`)

### 6. PR Requirements

Before your PR can be merged, it must meet the following requirements:

**Code Quality:**
- [ ] All tests pass
- [ ] Coverage >90% (enforced in CI)
- [ ] CI pipeline succeeds
- [ ] Code follows project style guidelines
- [ ] No linting errors or warnings

**Documentation:**
- [ ] README.md updated (if user-facing changes)
- [ ] API documentation updated (if new endpoints)
- [ ] Docstrings added/updated for new functions
- [ ] Changelog updated (if applicable)

**Process:**
- [ ] All commits are signed off (`-s` flag)
- [ ] PR description is clear and complete
- [ ] Related issue is referenced
- [ ] Breaking changes are documented

### 7. Approval Criteria

See [governance.md](governance.md) for detailed approval criteria. Briefly:

**Definition of Done:**
1. ✅ Code Complete: All required code written and syntactically correct
2. ✅ Unit Tests Pass: All relevant tests passing
3. ✅ Integration Tests Pass: Applicable integration tests passing
4. ✅ Acceptance Criteria Met: All acceptance criteria satisfied
5. ✅ Two-Eye Review: Code reviewed by at least one other developer
6. ✅ Documentation Updated: All necessary documentation updated
7. ✅ No Regressions: Existing functionality unaffected
8. ✅ CI/CD Success: All automated checks passing

**Review Process:**
- A reviewer will review your code within 3-5 business days
- Address all review comments and suggestions
- Request re-review after making changes
- Once approved and all criteria met, the PR will be merged

**Approver Responsibilities:**
- Verify code meets Definition of Done
- Check code quality, maintainability, and adherence to standards
- Ensure solution is appropriate for the problem
- Provide constructive, actionable feedback
- Approve only when satisfied with the changes

### 8. Merge Process

Once your PR is approved:
1. Maintainer will squash and merge your commits
2. Branch will be deleted automatically
3. Changes will be deployed to staging (if applicable)
4. You'll be notified when merged

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

## Code of Conduct

This project adheres to a Code of Conduct that all contributors must follow. By participating, you are expected to uphold this code.

Please read the full [Code of Conduct](CODE_OF_CONDUCT.md) for details.

**Summary:**
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Report unacceptable behavior to maintainers

Thank you for your contributions! 🎉
