/**
 * Unit tests for fileScanner module
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { scanWorkspace } from './fileScanner';
import { IgnorePattern } from './types';

describe('fileScanner', () => {
  let tempDir: string;

  beforeEach(() => {
    // Create a temporary directory for testing
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'fileScanner-test-'));
  });

  afterEach(() => {
    // Clean up temporary directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('scanWorkspace', () => {
    it('should discover Python files in workspace', () => {
      // Create test files
      fs.writeFileSync(path.join(tempDir, 'test.py'), '# Python file');
      fs.writeFileSync(path.join(tempDir, 'readme.md'), '# Readme');

      const result = scanWorkspace(tempDir);

      expect(result.files).toHaveLength(1);
      expect(result.files[0]).toContain('test.py');
      expect(result.errors).toHaveLength(0);
    });

    it('should discover JavaScript files in workspace', () => {
      // Create test files
      fs.writeFileSync(path.join(tempDir, 'app.js'), '// JavaScript file');
      fs.writeFileSync(path.join(tempDir, 'readme.md'), '# Readme');

      const result = scanWorkspace(tempDir);

      expect(result.files).toHaveLength(1);
      expect(result.files[0]).toContain('app.js');
      expect(result.errors).toHaveLength(0);
    });

    it('should discover Java files in workspace', () => {
      // Create test files
      fs.writeFileSync(path.join(tempDir, 'Main.java'), '// Java file');
      fs.writeFileSync(path.join(tempDir, 'readme.md'), '# Readme');

      const result = scanWorkspace(tempDir);

      expect(result.files).toHaveLength(1);
      expect(result.files[0]).toContain('Main.java');
      expect(result.errors).toHaveLength(0);
    });

    it('should discover all supported file types', () => {
      // Create test files
      fs.writeFileSync(path.join(tempDir, 'test.py'), '# Python');
      fs.writeFileSync(path.join(tempDir, 'app.js'), '// JavaScript');
      fs.writeFileSync(path.join(tempDir, 'Main.java'), '// Java');
      fs.writeFileSync(path.join(tempDir, 'readme.md'), '# Readme');

      const result = scanWorkspace(tempDir);

      expect(result.files).toHaveLength(3);
      expect(result.errors).toHaveLength(0);
    });

    it('should recursively scan nested directories', () => {
      // Create nested directory structure
      const srcDir = path.join(tempDir, 'src');
      const utilsDir = path.join(srcDir, 'utils');
      fs.mkdirSync(srcDir);
      fs.mkdirSync(utilsDir);

      fs.writeFileSync(path.join(tempDir, 'main.py'), '# Root');
      fs.writeFileSync(path.join(srcDir, 'app.js'), '// Src');
      fs.writeFileSync(path.join(utilsDir, 'helper.java'), '// Utils');

      const result = scanWorkspace(tempDir);

      expect(result.files).toHaveLength(3);
      expect(result.files.some(f => f.includes('main.py'))).toBe(true);
      expect(result.files.some(f => f.includes('app.js'))).toBe(true);
      expect(result.files.some(f => f.includes('helper.java'))).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should return empty list for empty workspace', () => {
      const result = scanWorkspace(tempDir);

      expect(result.files).toHaveLength(0);
      expect(result.ignoredCount).toBe(0);
      expect(result.errors).toHaveLength(0);
    });

    it('should return empty list when no supported files exist', () => {
      // Create unsupported files
      fs.writeFileSync(path.join(tempDir, 'readme.md'), '# Readme');
      fs.writeFileSync(path.join(tempDir, 'config.json'), '{}');

      const result = scanWorkspace(tempDir);

      expect(result.files).toHaveLength(0);
      expect(result.errors).toHaveLength(0);
    });

    it('should handle non-existent workspace path', () => {
      const nonExistentPath = path.join(tempDir, 'does-not-exist');

      const result = scanWorkspace(nonExistentPath);

      expect(result.files).toHaveLength(0);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0]).toContain('does not exist');
    });

    it('should handle workspace path that is a file', () => {
      const filePath = path.join(tempDir, 'test.txt');
      fs.writeFileSync(filePath, 'content');

      const result = scanWorkspace(filePath);

      expect(result.files).toHaveLength(0);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0]).toContain('not a directory');
    });

    it('should apply ignore patterns to exclude files', () => {
      // Create test files
      fs.writeFileSync(path.join(tempDir, 'main.py'), '# Main');
      fs.writeFileSync(path.join(tempDir, 'test.py'), '# Test');

      const ignorePatterns: IgnorePattern[] = [
        { pattern: 'test.py', isDirectory: false }
      ];

      const result = scanWorkspace(tempDir, ignorePatterns);

      expect(result.files).toHaveLength(1);
      expect(result.files[0]).toContain('main.py');
      expect(result.ignoredCount).toBe(1);
      expect(result.errors).toHaveLength(0);
    });

    it('should apply ignore patterns to exclude directories', () => {
      // Create directory structure
      const nodeModules = path.join(tempDir, 'node_modules');
      fs.mkdirSync(nodeModules);
      fs.writeFileSync(path.join(tempDir, 'main.js'), '// Main');
      fs.writeFileSync(path.join(nodeModules, 'package.js'), '// Package');

      const ignorePatterns: IgnorePattern[] = [
        { pattern: 'node_modules', isDirectory: true }
      ];

      const result = scanWorkspace(tempDir, ignorePatterns);

      expect(result.files).toHaveLength(1);
      expect(result.files[0]).toContain('main.js');
      expect(result.ignoredCount).toBeGreaterThan(0);
      expect(result.errors).toHaveLength(0);
    });

    it('should apply glob patterns to exclude files', () => {
      // Create test files
      fs.writeFileSync(path.join(tempDir, 'main.py'), '# Main');
      fs.writeFileSync(path.join(tempDir, 'test.py'), '# Test');
      fs.writeFileSync(path.join(tempDir, 'app.js'), '// App');

      const ignorePatterns: IgnorePattern[] = [
        { pattern: '*.py', isDirectory: false }
      ];

      const result = scanWorkspace(tempDir, ignorePatterns);

      expect(result.files).toHaveLength(1);
      expect(result.files[0]).toContain('app.js');
      expect(result.ignoredCount).toBe(2);
      expect(result.errors).toHaveLength(0);
    });

    it('should handle deeply nested directories', () => {
      // Create deeply nested structure
      let currentDir = tempDir;
      for (let i = 0; i < 5; i++) {
        currentDir = path.join(currentDir, `level${i}`);
        fs.mkdirSync(currentDir);
      }
      fs.writeFileSync(path.join(currentDir, 'deep.py'), '# Deep file');

      const result = scanWorkspace(tempDir);

      expect(result.files).toHaveLength(1);
      expect(result.files[0]).toContain('deep.py');
      expect(result.errors).toHaveLength(0);
    });

    it('should return absolute paths', () => {
      fs.writeFileSync(path.join(tempDir, 'test.py'), '# Test');

      const result = scanWorkspace(tempDir);

      expect(result.files).toHaveLength(1);
      expect(path.isAbsolute(result.files[0])).toBe(true);
    });

    it('should handle multiple ignore patterns', () => {
      // Create test files
      fs.writeFileSync(path.join(tempDir, 'main.py'), '# Main');
      fs.writeFileSync(path.join(tempDir, 'test.py'), '# Test');
      fs.writeFileSync(path.join(tempDir, 'app.js'), '// App');
      fs.writeFileSync(path.join(tempDir, 'test.js'), '// Test JS');

      const ignorePatterns: IgnorePattern[] = [
        { pattern: 'test.py', isDirectory: false },
        { pattern: 'test.js', isDirectory: false }
      ];

      const result = scanWorkspace(tempDir, ignorePatterns);

      expect(result.files).toHaveLength(2);
      expect(result.files.some(f => f.includes('main.py'))).toBe(true);
      expect(result.files.some(f => f.includes('app.js'))).toBe(true);
      expect(result.ignoredCount).toBe(2);
      expect(result.errors).toHaveLength(0);
    });

    it('should handle workspace with only ignored files', () => {
      fs.writeFileSync(path.join(tempDir, 'test.py'), '# Test');

      const ignorePatterns: IgnorePattern[] = [
        { pattern: '*.py', isDirectory: false }
      ];

      const result = scanWorkspace(tempDir, ignorePatterns);

      expect(result.files).toHaveLength(0);
      expect(result.ignoredCount).toBe(1);
      expect(result.errors).toHaveLength(0);
    });
  });
});
