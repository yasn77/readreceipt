#!/bin/bash
set -e

# Build script for Read Receipt browser extensions
# Usage: ./build.sh [chrome|firefox|all|package-chrome|package-firefox|clean]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$SCRIPT_DIR/dist"
CHROME_DIR="$SCRIPT_DIR/chrome"
FIREFOX_DIR="$SCRIPT_DIR/firefox"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
        echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
        echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
        echo -e "${RED}[ERROR]${NC} $1"
}

# Create dist directory
mkdir -p "$DIST_DIR"

# Clean build artifacts
clean() {
        log_info "Cleaning build artifacts..."
        rm -rf "$DIST_DIR"
        log_info "Clean complete"
}

# Build Chrome extension
build_chrome() {
        log_info "Building Chrome extension..."

        cd "$CHROME_DIR"

        # Validate manifest
        if ! node -e "require('./manifest.json')" 2>/dev/null; then
                log_error "Invalid Chrome manifest.json"
                exit 1
        fi

        # Check for required files
        REQUIRED_FILES=("manifest.json" "background.js" "content.js" "popup.html")
        for file in "${REQUIRED_FILES[@]}"; do
                if [ ! -f "$file" ]; then
                        log_error "Missing required file: $file"
                        exit 1
                fi
        done

        log_info "Chrome extension build complete"
        cd "$SCRIPT_DIR"
}

# Build Firefox extension
build_firefox() {
        log_info "Building Firefox extension..."

        cd "$FIREFOX_DIR"

        # Validate manifest
        if ! node -e "require('./manifest.json')" 2>/dev/null; then
                log_error "Invalid Firefox manifest.json"
                exit 1
        fi

        # Check for required files
        REQUIRED_FILES=("manifest.json" "background.js" "content.js" "popup.html")
        for file in "${REQUIRED_FILES[@]}"; do
                if [ ! -f "$file" ]; then
                        log_error "Missing required file: $file"
                        exit 1
                fi
        done

        log_info "Firefox extension build complete"
        cd "$SCRIPT_DIR"
}

# Package Chrome extension as zip
package_chrome() {
        log_info "Packaging Chrome extension..."

        build_chrome

        cd "$CHROME_DIR"

        VERSION=$(node -p "require('./manifest.json').version")
        PACKAGE_NAME="readreceipt-chrome-v${VERSION}.zip"

        # Create zip package
        if [ -d "icons" ]; then
                zip -r "$DIST_DIR/$PACKAGE_NAME" \
                        manifest.json \
                        background.js \
                        content.js \
                        popup.html \
                        icons/
        else
                zip -r "$DIST_DIR/$PACKAGE_NAME" \
                        manifest.json \
                        background.js \
                        content.js \
                        popup.html
        fi

        log_info "Chrome package created: $DIST_DIR/$PACKAGE_NAME"
        cd "$SCRIPT_DIR"
}

# Package Firefox extension as xpi
package_firefox() {
        log_info "Packaging Firefox extension..."

        build_firefox

        cd "$FIREFOX_DIR"

        VERSION=$(node -p "require('./manifest.json').version")
        PACKAGE_NAME="readreceipt-firefox-v${VERSION}.xpi"

        # Use web-ext if available, otherwise create zip manually
        if command -v web-ext &>/dev/null; then
                web-ext build \
                        --source-dir . \
                        --artifacts-dir "$DIST_DIR" \
                        --filename "$PACKAGE_NAME"
                log_info "Firefox package created: $DIST_DIR/$PACKAGE_NAME"
        else
                log_warn "web-ext not found, creating zip package instead"
                if [ -d "icons" ]; then
                        zip -r "$DIST_DIR/${PACKAGE_NAME%.xpi}.zip" \
                                manifest.json \
                                background.js \
                                content.js \
                                popup.html \
                                icons/
                else
                        zip -r "$DIST_DIR/${PACKAGE_NAME%.xpi}.zip" \
                                manifest.json \
                                background.js \
                                content.js \
                                popup.html
                fi
                log_info "Firefox package created: $DIST_DIR/${PACKAGE_NAME%.xpi}.zip"
        fi

        cd "$SCRIPT_DIR"
}

# Run extension tests
test_extensions() {
        log_info "Running extension tests..."

        local test_passed=0
        local test_failed=0

        # Test Chrome manifest
        if node -e "const m=require('$CHROME_DIR/manifest.json'); process.exit(m.manifest_version===3?0:1)" 2>/dev/null; then
                log_info "Chrome manifest validation: PASSED"
                test_passed=$((test_passed + 1))
        else
                log_error "Chrome manifest validation: FAILED"
                test_failed=$((test_failed + 1))
        fi

        # Test Firefox manifest
        if node -e "const m=require('$FIREFOX_DIR/manifest.json'); process.exit(m.manifest_version===2?0:1)" 2>/dev/null; then
                log_info "Firefox manifest validation: PASSED"
                test_passed=$((test_passed + 1))
        else
                log_error "Firefox manifest validation: FAILED"
                test_failed=$((test_failed + 1))
        fi

        # Check required files for Chrome
        for file in manifest.json background.js content.js popup.html; do
                if [ -f "$CHROME_DIR/$file" ]; then
                        log_info "Chrome $file: EXISTS"
                        test_passed=$((test_passed + 1))
                else
                        log_error "Chrome $file: MISSING"
                        test_failed=$((test_failed + 1))
                fi
        done

        # Check required files for Firefox
        for file in manifest.json background.js content.js popup.html; do
                if [ -f "$FIREFOX_DIR/$file" ]; then
                        log_info "Firefox $file: EXISTS"
                        test_passed=$((test_passed + 1))
                else
                        log_error "Firefox $file: MISSING"
                        test_failed=$((test_failed + 1))
                fi
        done

        echo ""
        log_info "Tests passed: $test_passed"
        if [ $test_failed -gt 0 ]; then
                log_error "Tests failed: $test_failed"
                exit 1
        fi
}

# Show usage
usage() {
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  chrome          Build Chrome extension"
        echo "  firefox         Build Firefox extension"
        echo "  all             Build both extensions"
        echo "  package-chrome  Package Chrome extension as zip"
        echo "  package-firefox Package Firefox extension as xpi"
        echo "  test            Run extension tests"
        echo "  clean           Clean build artifacts"
        echo "  help            Show this help message"
}

# Main command handler
case "${1:-all}" in
chrome)
        build_chrome
        ;;
firefox)
        build_firefox
        ;;
all)
        build_chrome
        build_firefox
        ;;
package-chrome)
        package_chrome
        ;;
package-firefox)
        package_firefox
        ;;
package)
        package_chrome
        package_firefox
        ;;
test)
        test_extensions
        ;;
clean)
        clean
        ;;
help | --help | -h)
        usage
        ;;
*)
        log_error "Unknown command: $1"
        usage
        exit 1
        ;;
esac
