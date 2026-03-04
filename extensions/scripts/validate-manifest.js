#!/usr/bin/env node

/**
 * Manifest validation script for browser extensions
 * Usage: node scripts/validate-manifest.js [chrome|firefox]
 */

const fs = require('fs');
const path = require('path');

const browser = process.argv[2];
const validBrowsers = ['chrome', 'firefox'];

if (!browser || !validBrowsers.includes(browser)) {
    console.error(`Usage: node ${process.argv[1]} [chrome|firefox]`);
    process.exit(1);
}

const manifestPath = path.join(__dirname, '..', browser, 'manifest.json');

if (!fs.existsSync(manifestPath)) {
    console.error(`Error: Manifest not found at ${manifestPath}`);
    process.exit(1);
}

let manifest;
try {
    manifest = require(manifestPath);
} catch (error) {
    console.error(`Error: Invalid JSON in manifest.json`);
    console.error(error.message);
    process.exit(1);
}

let isValid = true;
const errors = [];
const warnings = [];

// Validate common fields
if (!manifest.name || typeof manifest.name !== 'string') {
    errors.push('Missing or invalid "name" field');
}

if (!manifest.version || !/^\d+\.\d+\.\d+$/.test(manifest.version)) {
    errors.push('Missing or invalid "version" field (expected semver format)');
}

if (!manifest.description || typeof manifest.description !== 'string') {
    warnings.push('Missing or invalid "description" field');
}

// Browser-specific validation
if (browser === 'chrome') {
    if (manifest.manifest_version !== 3) {
        errors.push('Chrome extension must use manifest_version 3');
    }
    
    if (!manifest.background?.service_worker) {
        errors.push('Chrome extension must have a background.service_worker');
    }
    
    if (!manifest.action) {
        errors.push('Chrome extension must have an "action" field for the popup');
    }
    
    if (manifest.browser_action) {
        errors.push('Chrome extension should not use "browser_action" (use "action" instead)');
    }
} else if (browser === 'firefox') {
    if (manifest.manifest_version !== 2) {
        errors.push('Firefox extension must use manifest_version 2');
    }
    
    if (!manifest.background?.scripts) {
        errors.push('Firefox extension must have background.scripts array');
    }
    
    if (!manifest.browser_action) {
        errors.push('Firefox extension must have a "browser_action" field');
    }
    
    if (!manifest.applications?.gecko) {
        warnings.push('Firefox extension should have applications.gecko for extension ID');
    }
}

// Validate permissions
if (!manifest.permissions || !Array.isArray(manifest.permissions)) {
    warnings.push('No permissions defined');
}

// Validate content scripts
if (manifest.content_scripts) {
    if (!Array.isArray(manifest.content_scripts)) {
        errors.push('content_scripts must be an array');
    } else {
        manifest.content_scripts.forEach((script, index) => {
            if (!script.matches || !Array.isArray(script.matches)) {
                errors.push(`content_scripts[${index}]: missing or invalid "matches"`);
            }
            if (!script.js || !Array.isArray(script.js)) {
                errors.push(`content_scripts[${index}]: missing or invalid "js"`);
            }
        });
    }
}

// Output results
console.log(`\nValidating ${browser} extension manifest...\n`);

if (errors.length > 0) {
    console.error('ERRORS:');
    errors.forEach(error => console.error(`  ✗ ${error}`));
    isValid = false;
}

if (warnings.length > 0) {
    console.warn('WARNINGS:');
    warnings.forEach(warning => console.warn(`  ⚠ ${warning}`));
}

if (isValid) {
    console.log('✓ Manifest validation passed');
    if (warnings.length === 0) {
        console.log('✓ No warnings');
    }
    process.exit(0);
} else {
    console.error('\n✗ Manifest validation failed');
    process.exit(1);
}
