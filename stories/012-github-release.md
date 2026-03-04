# Story: GitHub Release and Assets

## Description
As a user, I want easy access to pre-built extension packages and deployment artifacts, so that I can quickly install and use the application.

## Acceptance Criteria
- [ ] GitHub Release created with version tag
- [ ] Chrome extension .zip attached
- [ ] Firefox extension .xpi attached
- [ ] Docker image published
- [ ] Helm chart versioned
- [ ] Release notes generated
- [ ] Changelog updated

## Release Process

### 1. Version Bumping
- Update version in manifest.json
- Update version in package.json (if applicable)
- Update version in Python package (if applicable)
- Update CHANGELOG.md

### 2. Build Artifacts
- Build Chrome extension zip
- Build Firefox extension xpi
- Build and push Docker image
- Package Helm chart

### 3. GitHub Release
- Create release tag (vX.Y.Z)
- Write release notes
- Upload artifacts
- Set as latest release

### 4. Distribution
- Submit to Chrome Web Store
- Submit to Firefox Add-ons
- Update documentation links

## Release Notes Template
```markdown
## What's Changed
- Feature 1
- Feature 2
- Bug fix 1

## New Contributors
- @contributor1

## Full Changelog
https://github.com/yasn77/readreceipt/compare/v0.1.0...v0.2.0
```

## Automated Release Workflow
- GitHub Actions workflow triggers on tag
- Builds all artifacts
- Creates GitHub Release
- Optionally publishes to stores

## Definition of Done
- [ ] Release tag created
- [ ] All artifacts attached
- [ ] Release notes complete
- [ ] Docker image published
- [ ] Helm chart updated
- [ ] Documentation links updated
- [ ] PR reviewed and approved
