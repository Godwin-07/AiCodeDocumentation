/**
 * Ignore file parser for .docignore.txt
 * 
 * This module handles parsing of .docignore.txt files which follow gitignore-style syntax.
 * It reads patterns line by line, skips comments and empty lines, and returns an array
 * of IgnorePattern objects.
 * 
 * Validates: Requirements 1.1, 1.2, 1.3, 1.4
 */

import * as fs from 'fs';
import * as path from 'path';
import { minimatch } from 'minimatch';
import { IgnorePattern } from './types';

/**
 * Parse a .docignore.txt file and return an array of ignore patterns.
 * 
 * Parsing rules:
 * - Lines starting with '#' are comments (ignored)
 * - Empty lines are ignored
 * - Patterns ending with '/' match directories
 * - Patterns with '*' are glob patterns
 * - Patterns are relative to workspace root
 * 
 * @param filePath - Absolute path to the .docignore.txt file
 * @returns Array of IgnorePattern objects
 * @throws Error if file cannot be read
 */
export function parseIgnoreFile(filePath: string): IgnorePattern[] {
  // Read the file content
  const content = fs.readFileSync(filePath, 'utf-8');
  
  // Split into lines
  const lines = content.split(/\r?\n/);
  
  const patterns: IgnorePattern[] = [];
  
  for (const line of lines) {
    // Trim whitespace
    const trimmedLine = line.trim();
    
    // Skip empty lines
    if (trimmedLine.length === 0) {
      continue;
    }
    
    // Skip comments (lines starting with #)
    if (trimmedLine.startsWith('#')) {
      continue;
    }
    
    // Check if pattern targets directories (ends with /)
    const isDirectory = trimmedLine.endsWith('/');
    
    // Remove trailing slash for directory patterns
    const pattern = isDirectory ? trimmedLine.slice(0, -1) : trimmedLine;
    
    patterns.push({
      pattern,
      isDirectory
    });
  }
  
  return patterns;
}

/**
 * Check if a file path matches an ignore pattern.
 * 
 * This function uses the minimatch library to handle glob patterns, directory patterns,
 * and wildcards. It supports:
 * - Simple patterns: "node_modules" matches "node_modules" or "path/to/node_modules"
 * - Glob patterns: "*.test.js" matches any file ending with .test.js
 * - Wildcard patterns: "**\/*.pyc" matches .pyc files in any directory
 * - Directory patterns: When isDirectory is true, matches the directory and all its contents
 * 
 * @param filePath - The file path to check (relative to workspace root)
 * @param pattern - The ignore pattern to match against
 * @returns true if the file path matches the pattern, false otherwise
 * 
 * Validates: Requirements 1.3, 1.4
 */
export function matchesPattern(filePath: string, pattern: IgnorePattern): boolean {
  // Normalize the file path to use forward slashes
  const normalizedPath = filePath.replace(/\\/g, '/');
  
  // If the pattern is for a directory, we need to check if the file path
  // starts with the directory name or is within that directory
  if (pattern.isDirectory) {
    // Check if the path starts with the directory pattern
    // This handles cases like:
    // - pattern: "node_modules", path: "node_modules/package/file.js"
    // - pattern: "build", path: "build/output.js"
    
    // Use minimatch to check if the path matches the directory pattern
    // We need to check both the exact directory and any subdirectories
    const directoryPattern = `${pattern.pattern}/**`;
    const exactMatch = `${pattern.pattern}`;
    
    // Check if the path is the directory itself or within it
    if (minimatch(normalizedPath, directoryPattern, { dot: true }) ||
        minimatch(normalizedPath, exactMatch, { dot: true })) {
      return true;
    }
    
    // Also check if any part of the path matches the directory pattern
    // This handles nested directories like "src/node_modules"
    const pathParts = normalizedPath.split('/');
    for (let i = 0; i < pathParts.length; i++) {
      const partialPath = pathParts.slice(0, i + 1).join('/');
      if (minimatch(partialPath, exactMatch, { dot: true })) {
        // If we found a matching directory, return true
        return true;
      }
      
      // Also check if the remaining path after this point matches the pattern
      const remainingPath = pathParts.slice(i).join('/');
      if (minimatch(remainingPath, directoryPattern, { dot: true }) ||
          minimatch(remainingPath, exactMatch, { dot: true })) {
        return true;
      }
    }
  }
  
  // For file patterns, use minimatch directly
  // This handles:
  // - Exact matches: "README.md"
  // - Glob patterns: "*.test.js"
  // - Wildcard patterns: "**\/*.pyc"
  if (minimatch(normalizedPath, pattern.pattern, { dot: true })) {
    return true;
  }
  
  // Also check if the pattern matches any part of the path
  // This handles cases where the pattern is meant to match a file/directory
  // anywhere in the tree, not just at the root
  const pathParts = normalizedPath.split('/');
  for (let i = 0; i < pathParts.length; i++) {
    const partialPath = pathParts.slice(i).join('/');
    if (minimatch(partialPath, pattern.pattern, { dot: true })) {
      return true;
    }
    
    // Also check if the pattern matches the path up to this point
    // This handles gitignore-style behavior where "node_modules" matches "node_modules/package"
    const pathUpToHere = pathParts.slice(0, i + 1).join('/');
    if (minimatch(pathUpToHere, pattern.pattern, { dot: true })) {
      return true;
    }
  }
  
  return false;
}
