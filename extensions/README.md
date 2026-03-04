# Browser Extensions

This directory contains the Chrome and Firefox browser extensions for Read Receipt.

## Directory Structure

```
extensions/
├── chrome/           # Chrome extension (Manifest V3)
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   └── popup.html
├── firefox/          # Firefox extension (Manifest V2)
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   └── popup.html
├── scripts/          # Build and test scripts
│   ├── validate-manifest.js
│   └── test-extensions.js
├── build.sh          # Main build script
└── package.json      # NPM configuration
```

## Prerequisites

- Node.js 18 or higher
- npm 9 or higher
- web-ext (for Firefox builds) - installed automatically via npm

## Building Locally

### Quick Build

```bash
# Build both extensions
cd extensions
npm run build

# Or use the build script directly
./build.sh all
```

### Build Chrome Extension

```bash
cd extensions
npm run build:chrome
# or
./build.sh chrome
```

### Build Firefox Extension

```bash
cd extensions
npm run build:firefox
# or
./build.sh firefox
```

## Packaging for Distribution

### Package Chrome Extension

Creates a zip file in the `dist/` directory:

```bash
cd extensions
npm run package:chrome
# or
./build.sh package-chrome
```

### Package Firefox Extension

Creates an XPI file in the `dist/` directory:

```bash
cd extensions
npm run package:firefox
# or
./build.sh package-firefox
```

### Package Both Extensions

```bash
cd extensions
npm run package
# or
./build.sh package
```

## Testing and Validation

### Run All Tests

```bash
cd extensions
npm test
# or
./build.sh test
```

### Validate Manifests

```bash
cd extensions
npm run validate
```

### Lint JavaScript

```bash
cd extensions
npm run lint
```

### Firefox-specific Linting

```bash
cd extensions
npm run web-ext-lint:firefox
```

## Version Numbering

Extensions follow semantic versioning (semver):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- MAJOR: Breaking changes
- MINOR: New features (backwards compatible)
- PATCH: Bug fixes (backwards compatible)

### Updating Version

Update the version in both manifest files:

1. `extensions/chrome/manifest.json`
2. `extensions/firefox/manifest.json`

Both must have the same version number.

## Publishing to Stores

### Chrome Web Store

1. **Build and package:**
   ```bash
   cd extensions
   npm run package:chrome
   ```

2. **Upload to Chrome Web Store:**
   - Go to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole)
   - Create a new item or select existing extension
   - Upload the zip file from `dist/`

3. **Using CI/CD:**
   - Tag your release: `git tag extension-v1.0.0`
   - Push tag: `git push origin extension-v1.0.0`
   - GitHub Actions will automatically build and create a release
   - Use Chrome Web Store API for automated uploads (requires API credentials)

### Firefox Add-ons

1. **Build and package:**
   ```bash
   cd extensions
   npm run package:firefox
   ```

2. **Upload to Firefox Add-ons:**
   - Go to [Firefox Add-ons Developer Hub](https://addons.mozilla.org/developers/)
   - Submit a new add-on or select existing one
   - Upload the XPI file from `dist/`

3. **Using web-ext sign:**
   ```bash
   cd extensions/firefox
   web-ext sign --api-key $AMO_API_KEY --api-secret $AMO_API_SECRET
   ```

4. **Using CI/CD:**
   - Tag your release: `git tag extension-v1.0.0`
   - Push tag: `git push origin extension-v1.0.0`
   - GitHub Actions will automatically build, create a release, and sign the extension

## Release Process

### Manual Release

1. Update version in both manifest files
2. Run tests: `npm test`
3. Build packages: `npm run package`
4. Test packages locally
5. Commit changes
6. Create git tag: `git tag extension-vX.Y.Z`
7. Push tag: `git push origin extension-vX.Y.Z`

### Automated Release

The GitHub Actions workflow automatically:
- Builds both extensions on push to main/master
- Runs validation and linting
- Creates packages on tags matching `extension-v*`
- Creates GitHub Release with artifacts
- Prepares for store submission

## Environment Variables

For automated publishing, set these secrets in GitHub:

- `CHROME_WEB_STORE_CLIENT_ID` - Chrome Web Store API client ID
- `CHROME_WEB_STORE_CLIENT_SECRET` - Chrome Web Store API client secret
- `CHROME_WEB_STORE_REFRESH_TOKEN` - Chrome Web Store API refresh token
- `AMO_API_KEY` - Firefox Add-ons API key
- `AMO_API_SECRET` - Firefox Add-ons API secret
- `AMO_JWT_ISSUER` - Firefox Add-ons JWT issuer

## Troubleshooting

### Build fails with "web-ext not found"

Install web-ext globally:
```bash
npm install -g web-ext
```

### Manifest validation errors

Run the validation script to see detailed errors:
```bash
npm run validate:chrome
npm run validate:firefox
```

### Package not loading in browser

1. Check browser console for errors
2. Verify manifest.json syntax
3. Ensure all referenced files exist
4. Check that permissions are correctly specified

## CI/CD Workflow

The GitHub Actions workflow (`.github/workflows/build-extensions.yml`) provides:

- **On push/PR:** Build and validate both extensions
- **On tag (extension-v*):** Build, package, and create GitHub Release
- **Caching:** Uses npm cache for faster builds
- **Artifacts:** Uploads Chrome zip and Firefox XPI for download

## Contributing

1. Make changes to source files
2. Run tests: `npm test`
3. Run lint: `npm run lint`
4. Build and test locally
5. Submit pull request

For more information, see the main [CONTRIBUTING.md](../CONTRIBUTING.md).
