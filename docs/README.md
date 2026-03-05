# Read Receipt Documentation

This directory contains the comprehensive documentation for Read Receipt.

## Building the Documentation

### Prerequisites

Install the documentation dependencies:

```bash
pip install -r docs-requirements.txt
```

### Serve Locally

To preview the documentation during development:

```bash
mkdocs serve
```

This starts a local server at `http://localhost:8000` with live reload.

### Build Static Site

To build the static documentation site:

```bash
mkdocs build
```

This generates the site in the `site/` directory.

### Deploy to Production

```bash
# Build
mkdocs build

# Deploy (configure remote in mkdocs.yml)
mkdocs gh-deploy
```

## Documentation Structure

```
docs/
├── index.md                    # Documentation home page
├── architecture.md             # System architecture
├── getting-started.md          # Installation and setup
├── admin-guide.md              # Admin dashboard guide
├── extension-guide.md          # Browser extension guide
├── api-reference.md            # API documentation
├── deployment.md               # Deployment guide
├── development.md              # Development guide
├── troubleshooting.md          # Troubleshooting guide
├── glossary.md                 # Glossary of terms
├── changelog.md                # Version history
├── stylesheets/
│   └── extra.css               # Custom CSS
└── javascripts/
    └── extra.js                # Custom JavaScript
```

## Writing Guidelines

### Style Guide

- Use **British English** (Oxford spelling)
- Write in clear, professional language
- Use active voice where possible
- Keep sentences concise
- Use code examples where appropriate

### Formatting

- Use Markdown for all documentation
- Follow the existing structure and formatting
- Use admonitions for notes, warnings, and tips
- Include screenshots where helpful (note location if not providing image)

### Admonitions

Use MkDocs admonitions for special content:

```markdown
!!! note
    This is a note.

!!! tip
    This is a helpful tip.

!!! warning
    This is a warning.

!!! danger
    This indicates danger.
```

### Code Blocks

Use syntax-highlighted code blocks:

````markdown
```python
def example():
    return "Hello, World!"
```
````

### Links

- Use relative links for internal documentation
- Use absolute links for external resources
- Include descriptive link text

## Contributing

1. Create or edit documentation files
2. Test locally with `mkdocs serve`
3. Check for broken links
4. Submit a pull request

## Documentation Standards

- **Accuracy**: Ensure all information is correct and up-to-date
- **Completeness**: Cover all relevant aspects of the topic
- **Clarity**: Write clearly and concisely
- **Consistency**: Follow established patterns and formatting
- **Accessibility**: Make documentation accessible to all users

## Version Control

- Documentation version matches the software version
- Update changelog when adding significant documentation
- Tag documentation releases with software releases

## Testing

Before submitting documentation changes:

1. Build locally: `mkdocs build`
2. Check for warnings
3. Test all links
4. Verify code examples work
5. Check formatting on mobile

## Tools

- **MkDocs**: Static site generator
- **Material Theme**: Documentation theme
- **PyMdown Extensions**: Markdown extensions
- **Git**: Version control

## Contact

For questions about documentation:
- Open an issue on GitHub
- Start a discussion
- Contact the maintainers

---

**Last Updated:** 2024-01-15
**Maintained By:** Read Receipt Team
