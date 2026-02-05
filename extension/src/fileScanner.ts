/**
 * Workspace file scanner for discovering source files
 * 
 * This module handles recursive traversal of workspace directories to discover
 * source files with supported extensions (.py, .js, .java). It applies ignore
 * patterns to exclude files and directories that should not be documented.
 * 
 * Validates: Requirements 2.1, 2.2, 2.3
 */

import * as fs from 'fs';
import * as path from 'path';
import { FileDiscoveryResult, IgnorePattern } from './types';
import { matchesPattern } from './ignoreParser';

/**
 * Supported source file extensions
 */
const SUPPORTED_EXTENSIONS = ['.py', '.js', '.java'];

/**
 * Recursively scan a workspace directory to discover source files.
 * 
 * This function:
 * - Recursively traverses all directories in the workspace
 * - Identifies files with extensions .py, .js, and .java
 * - Applies ignore patterns to exclude files and directories
 * - Returns absolute paths to all discovered files
 * 
 * @param workspacePath - Absolute path to the workspace root directory
 * @param ignorePatterns - Array of ignore patterns to apply
 * @returns FileDiscoveryResult containing discovered files, ignored count, and errors
 * 
 * Validates: Requirements 2.1, 2.2, 2.3
 */
export function scanWorkspace(
  workspacePath: string,
  ignorePatterns: IgnorePattern[] = []
): FileDiscoveryResult {
  const result: FileDiscoveryResult = {
    files: [],
    ignoredCount: 0,
    errors: []
  };

  // Verify workspace path exists
  if (!fs.existsSync(workspacePath)) {
    result.errors.push(`Workspace path does not exist: ${workspacePath}`);
    return result;
  }

  // Verify workspace path is a directory
  const stats = fs.statSync(workspacePath);
  if (!stats.isDirectory()) {
    result.errors.push(`Workspace path is not a directory: ${workspacePath}`);
    return result;
  }

  // Start recursive scan
  scanDirectory(workspacePath, workspacePath, ignorePatterns, result);

  return result;
}

/**
 * Recursively scan a directory and its subdirectories.
 * 
 * @param dirPath - Absolute path to the directory to scan
 * @param workspaceRoot - Absolute path to the workspace root (for relative path calculation)
 * @param ignorePatterns - Array of ignore patterns to apply
 * @param result - FileDiscoveryResult object to accumulate results
 */
function scanDirectory(
  dirPath: string,
  workspaceRoot: string,
  ignorePatterns: IgnorePattern[],
  result: FileDiscoveryResult
): void {
  try {
    // Read directory contents
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);
      const relativePath = path.relative(workspaceRoot, fullPath);

      // Check if this path should be ignored
      if (shouldIgnore(relativePath, ignorePatterns)) {
        result.ignoredCount++;
        continue;
      }

      if (entry.isDirectory()) {
        // Recursively scan subdirectory
        scanDirectory(fullPath, workspaceRoot, ignorePatterns, result);
      } else if (entry.isFile()) {
        // Check if file has a supported extension
        const ext = path.extname(entry.name);
        if (SUPPORTED_EXTENSIONS.includes(ext)) {
          result.files.push(fullPath);
        }
      }
      // Ignore symbolic links and other special file types
    }
  } catch (error) {
    // Handle errors reading directory (e.g., permission denied)
    const errorMessage = error instanceof Error ? error.message : String(error);
    result.errors.push(`Error scanning directory ${dirPath}: ${errorMessage}`);
  }
}

/**
 * Check if a file path should be ignored based on ignore patterns.
 * 
 * @param relativePath - File path relative to workspace root
 * @param ignorePatterns - Array of ignore patterns to check against
 * @returns true if the path should be ignored, false otherwise
 */
function shouldIgnore(relativePath: string, ignorePatterns: IgnorePattern[]): boolean {
  // Check if the path matches any ignore pattern
  for (const pattern of ignorePatterns) {
    if (matchesPattern(relativePath, pattern)) {
      return true;
    }
  }
  return false;
}
