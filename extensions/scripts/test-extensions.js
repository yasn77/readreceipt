#!/usr/bin/env node

/**
 * Extension test script
 * Validates that extensions can be loaded and have required files
 */

const fs = require('fs');
const path = require('path');

const extensionsDir = path.join(__dirname, '..');
const chromeDir = path.join(extensionsDir, 'chrome');
const firefoxDir = path.join(extensionsDir, 'firefox');

let passed = 0;
let failed = 0;

function test(name, condition, errorMessage) {
    if (condition) {
        console.log(`✓ ${name}`);
        passed++;
    } else {
        console.error(`✗ ${name}`);
        if (errorMessage) {
            console.error(`  ${errorMessage}`);
        }
        failed++;
    }
}

console.log('\n=== Extension Tests ===\n');

// Chrome tests
console.log('Chrome Extension:');
console.log('----------------');

const chromeManifestPath = path.join(chromeDir, 'manifest.json');
test(
    'manifest.json exists',
    fs.existsSync(chromeManifestPath),
    'File not found'
);

if (fs.existsSync(chromeManifestPath)) {
    try {
        const chromeManifest = require(chromeManifestPath);
        test(
            'manifest.json is valid JSON',
            true
        );
        test(
            'manifest_version is 3',
            chromeManifest.manifest_version === 3,
            `Expected 3, got ${chromeManifest.manifest_version}`
        );
        test(
            'has name field',
            typeof chromeManifest.name === 'string' && chromeManifest.name.length > 0
        );
        test(
            'has version field',
            typeof chromeManifest.version === 'string' && /^\d+\.\d+\.\d+$/.test(chromeManifest.version)
        );
        test(
            'has background service_worker',
            chromeManifest.background?.service_worker !== undefined,
            'Chrome requires a service worker'
        );
        test(
            'has action field',
            chromeManifest.action !== undefined,
            'Chrome requires an action field for the popup'
        );
        test(
            'has permissions',
            Array.isArray(chromeManifest.permissions) && chromeManifest.permissions.length > 0
        );
    } catch (error) {
        test('manifest.json is valid JSON', false, error.message);
    }
}

test(
    'background.js exists',
    fs.existsSync(path.join(chromeDir, 'background.js')),
    'File not found'
);

test(
    'content.js exists',
    fs.existsSync(path.join(chromeDir, 'content.js')),
    'File not found'
);

test(
    'popup.html exists',
    fs.existsSync(path.join(chromeDir, 'popup.html')),
    'File not found'
);

console.log('\nFirefox Extension:');
console.log('------------------');

const firefoxManifestPath = path.join(firefoxDir, 'manifest.json');
test(
    'manifest.json exists',
    fs.existsSync(firefoxManifestPath),
    'File not found'
);

if (fs.existsSync(firefoxManifestPath)) {
    try {
        const firefoxManifest = require(firefoxManifestPath);
        test(
            'manifest.json is valid JSON',
            true
        );
        test(
            'manifest_version is 2',
            firefoxManifest.manifest_version === 2,
            `Expected 2, got ${firefoxManifest.manifest_version}`
        );
        test(
            'has name field',
            typeof firefoxManifest.name === 'string' && firefoxManifest.name.length > 0
        );
        test(
            'has version field',
            typeof firefoxManifest.version === 'string' && /^\d+\.\d+\.\d+$/.test(firefoxManifest.version)
        );
        test(
            'has background scripts',
            Array.isArray(firefoxManifest.background?.scripts),
            'Firefox requires background scripts array'
        );
        test(
            'has browser_action',
            firefoxManifest.browser_action !== undefined,
            'Firefox requires browser_action field'
        );
        test(
            'has permissions',
            Array.isArray(firefoxManifest.permissions) && firefoxManifest.permissions.length > 0
        );
        test(
            'has applications.gecko',
            firefoxManifest.applications?.gecko !== undefined,
            'Firefox should have gecko application ID'
        );
    } catch (error) {
        test('manifest.json is valid JSON', false, error.message);
    }
}

test(
    'background.js exists',
    fs.existsSync(path.join(firefoxDir, 'background.js')),
    'File not found'
);

test(
    'content.js exists',
    fs.existsSync(path.join(firefoxDir, 'content.js')),
    'File not found'
);

test(
    'popup.html exists',
    fs.existsSync(path.join(firefoxDir, 'popup.html')),
    'File not found'
);

// JavaScript linting check (basic syntax validation)
console.log('\nJavaScript Syntax Check:');
console.log('------------------------');

['chrome', 'firefox'].forEach(browser => {
    const dir = browser === 'chrome' ? chromeDir : firefoxDir;
    ['background.js', 'content.js'].forEach(file => {
        const filePath = path.join(dir, file);
        if (fs.existsSync(filePath)) {
            try {
                const content = fs.readFileSync(filePath, 'utf8');
                new Function(content);
                test(`${browser}/${file} syntax valid`, true);
            } catch (error) {
                test(`${browser}/${file} syntax valid`, false, error.message);
            }
        }
    });
});

// Summary
console.log('\n=== Test Summary ===\n');
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);
console.log(`Total:  ${passed + failed}`);

if (failed > 0) {
    console.log('\n✗ Some tests failed');
    process.exit(1);
} else {
    console.log('\n✓ All tests passed');
    process.exit(0);
}
