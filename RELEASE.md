# Release Guide - ReadReceipt

This document describes the release process for ReadReceipt, including version numbering, artifact generation, and distribution.

## Table of Contents

- [Version Numbering Scheme](#version-numbering-scheme)
- [Release Triggers](#release-triggers)
- [Build Artifacts](#build-artifacts)
- [Release Process](#release-process)
- [Manual Release Steps](#manual-release-steps)
- [Troubleshooting](#troubleshooting)

## Version Numbering Scheme

ReadReceipt follows [Semantic Versioning (SemVer)](https://semver.org/) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR** (X.0.0): Breaking changes that may require users to update configurations or code
- **MINOR** (1.X.0): New features added in a backwards-compatible manner
- **PATCH** (1.1.X): Backwards-compatible bug fixes and security patches

### Examples

- `1.0.0` - Initial stable release
- `1.1.0` - New feature added (e.g., new email provider support)
- `1.1.1` - Bug fix (e.g., fix Gmail selector issue)
- `2.0.0` - Breaking change (e.g., manifest v3 migration)

### Pre-release Versions

For testing and release candidates, use SemVer pre-release identifiers:

- `1.2.0-alpha.1` - Alpha release for internal testing
- `1.2.0-beta.1` - Beta release for wider testing
- `1.2.0-rc.1` - Release candidate, feature-complete

## Release Triggers

The release workflow is **automatically triggered** when you push a version tag to the `master` branch:

```bash
git tag v1.2.0
git push origin v1.2.0
```

### Branch Restriction

Releases are **only** created from the `master` branch. Tags pushed to other branches will not trigger the release workflow.

## Build Artifacts

Each release generates the following artifacts:

### 1. Browser Extensions

| Artifact | Format | Description |
|----------|--------|-------------|
| Chrome Extension | `.zip` | Unpacked Chrome extension ready for loading or Web Store submission |
| Firefox Extension | `.xpi` | Firefox add-on package ready for installation or AMO submission |

**Location:** Attached to GitHub Release

### 2. Container Image

| Artifact | Registry | Tags |
|----------|----------|------|
| Docker Image | `ghcr.io/yasn77/readreceipt` | `v1.2.0`, `v1.2`, `v1`, `latest` |

**Pull Command:**
```bash
docker pull ghcr.io/yasn77/readreceipt:v1.2.0
```

### 3. Helm Chart

| Artifact | Format | Description |
|----------|--------|-------------|
| Helm Chart | `.tgz` | Versioned Helm chart for Kubernetes deployment |

**Installation:**
```bash
helm repo add readreceipt https://yasn77.github.io/readreceipt/
helm install readreceipt readreceipt/readreceipt --version 1.2.0
```

### 4. Binary Release

| Artifact | Platform | Description |
|----------|----------|-------------|
| Linux Binary | `readreceipt-linux-amd64` | Standalone executable for Linux x64 |

### 5. Release Notes

Automatically generated from Git commit history since the last release tag.

## Release Process

### Automated Workflow

The GitHub Actions workflow (`.github/workflows/release.yml`) handles the entire release process:

1. **Validates** semantic version format
2. **Builds** Chrome extension (`.zip`)
3. **Builds** Firefox extension (`.xpi`)
4. **Builds and pushes** Docker image to GHCR
5. **Packages** Helm chart with versioned name
6. **Compiles** Python binary (Linux)
7. **Creates** GitHub Release with all artifacts
8. **Generates** release notes from commit history

### Workflow Diagram

```
Push version tag (vX.Y.Z)
         ↓
GitHub Actions Triggered
         ↓
┌────────────────────────┐
│  Build Jobs            │
│  - Extensions          │
│  - Docker Image        │
│  - Helm Chart          │
│  - Binary              │
└────────────────────────┘
         ↓
┌────────────────────────┐
│  Create Release        │
│  - Upload Assets       │
│  - Generate Notes      │
│  - Publish             │
└────────────────────────┘
         ↓
Release Published ✓
```

## Manual Release Steps

If you need to create a release manually (e.g., for testing or troubleshooting):

### 1. Ensure You're on Master

```bash
git checkout master
git pull origin master
```

### 2. Verify Version Numbers

Update version in the following files before tagging:

- `manifest.json` → `"version": "1.2.0"`
- `extensions/chrome/manifest.json` → `"version": "1.2.0"`
- `extensions/firefox/manifest.json` → `"version": "1.2.0"`
- `helm/readreceipt/Chart.yaml` → `version: 1.2.0` and `appVersion: "v1.2.0"`

### 3. Create and Push Tag

```bash
git tag v1.2.0
git push origin v1.2.0
```

### 4. Monitor Workflow

Watch the workflow progress in GitHub Actions:
- Navigate to: `https://github.com/yasn77/readreceipt/actions`
- Look for "Release" workflow run
- Verify all jobs complete successfully

### 5. Verify Release

After workflow completion:
- Check GitHub Releases page
- Verify all assets are attached
- Test Docker image pull
- Verify Helm chart is accessible

### 6. Post-Release (Optional)

Submit extensions to stores:

**Chrome Web Store:**
```bash
# Upload readreceipt-chrome-extension.zip to Chrome Web Store Developer Dashboard
```

**Firefox Add-ons (AMO):**
```bash
# Upload readreceipt-firefox-extension.xpi to Firefox Add-ons site
```

## Troubleshooting

### Workflow Fails on Tag Validation

**Symptom:** "Error: Version X.Y.Z is not a valid semantic version"

**Solution:** Ensure tag format is exactly `vX.Y.Z` (e.g., `v1.2.0`, not `1.2.0` or `v1.2`)

```bash
# Wrong
git tag 1.2.0
git tag v1.2

# Correct
git tag v1.2.0
```

### Docker Push Fails

**Symptom:** "denied: requested access to the resource is denied"

**Solution:** Verify `GITHUB_TOKEN` secret has `packages: write` permission in workflow

### Helm Chart Packaging Fails

**Symptom:** "Error: file 'helm/readreceipt' does not exist"

**Solution:** Ensure Chart.yaml exists at `helm/readreceipt/Chart.yaml`

### Release Assets Missing

**Symptom:** GitHub Release created but some assets not attached

**Solution:**
1. Check workflow logs for build errors
2. Verify file paths in the workflow match actual output locations
3. Re-run the failed job or entire workflow

### Docker Image Tags Incorrect

**Symptom:** Image pushed with wrong tags

**Solution:** Verify `docker/metadata-action` configuration in workflow. Tags should include:
- Semantic version: `v1.2.0`
- Minor version: `v1.2`
- Major version: `v1`
- Latest: `latest`

## Release Checklist

Before creating a release, verify:

- [ ] All tests passing (CI green)
- [ ] Security scans passing (no critical vulnerabilities)
- [ ] Version numbers updated in all files
- [ ] CHANGELOG.md updated (if maintaining manually)
- [ ] Documentation updated for new features
- [ ] On `master` branch with latest changes
- [ ] Tag follows SemVer format (`vX.Y.Z`)

## Release Notes Template

GitHub auto-generates release notes, but you can enhance them:

```markdown
## What's Changed

### Features
- New feature description

### Fixes
- Bug fix description

### Security
- Security improvement description

## New Contributors
- @contributor1 made their first contribution

## Full Changelog
https://github.com/yasn77/readreceipt/compare/v1.1.0...v1.2.0
```

## Asset Distribution Summary

| Asset | Primary Use Case | Distribution Channel |
|-------|-----------------|---------------------|
| Chrome Extension (.zip) | Chrome/Edge users | Chrome Web Store / Manual load |
| Firefox Extension (.xpi) | Firefox users | Firefox Add-ons / Manual install |
| Docker Image | Self-hosted backend | GHCR (ghcr.io) |
| Helm Chart | Kubernetes deployments | Helm repo / GitHub Pages |
| Linux Binary | Direct execution | GitHub Releases |

---

**Questions?** Open an issue or contact the maintainers.
