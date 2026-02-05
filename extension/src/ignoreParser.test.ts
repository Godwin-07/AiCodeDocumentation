/**
 * Unit tests for ignoreParser module
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { parseIgnoreFile, matchesPattern } from './ignoreParser';
import { IgnorePattern } from './types';

describe('ignoreParser', () => {
  let tempDir: string;
  
  beforeEach(() => {
    // Create a temporary directory for test files
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ignoreparser-test-'));
  });
  
  afterEach(() => {
    // Clean up temporary directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });
  
  describe('parseIgnoreFile', () => {
    it('should parse simple patterns', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, 'node_modules\n*.test.js\nbuild');
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([
        { pattern: 'node_modules', isDirectory: false },
        { pattern: '*.test.js', isDirectory: false },
        { pattern: 'build', isDirectory: false }
      ]);
    });
    
    it('should skip comments', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, '# This is a comment\nnode_modules\n# Another comment\n*.log');
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([
        { pattern: 'node_modules', isDirectory: false },
        { pattern: '*.log', isDirectory: false }
      ]);
    });
    
    it('should skip empty lines', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, 'node_modules\n\n\n*.test.js\n\nbuild');
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([
        { pattern: 'node_modules', isDirectory: false },
        { pattern: '*.test.js', isDirectory: false },
        { pattern: 'build', isDirectory: false }
      ]);
    });
    
    it('should identify directory patterns', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, 'node_modules/\nbuild/\ndist/');
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([
        { pattern: 'node_modules', isDirectory: true },
        { pattern: 'build', isDirectory: true },
        { pattern: 'dist', isDirectory: true }
      ]);
    });
    
    it('should handle mixed patterns', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, 
        '# Ignore node modules\nnode_modules/\n\n# Ignore test files\n*.test.js\n\n# Ignore build output\nbuild/\ndist/'
      );
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([
        { pattern: 'node_modules', isDirectory: true },
        { pattern: '*.test.js', isDirectory: false },
        { pattern: 'build', isDirectory: true },
        { pattern: 'dist', isDirectory: true }
      ]);
    });
    
    it('should handle empty file', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, '');
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([]);
    });
    
    it('should handle file with only comments', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, '# Comment 1\n# Comment 2\n# Comment 3');
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([]);
    });
    
    it('should handle file with only empty lines', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, '\n\n\n\n');
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([]);
    });
    
    it('should trim whitespace from patterns', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, '  node_modules  \n  *.test.js  \n  build/  ');
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([
        { pattern: 'node_modules', isDirectory: false },
        { pattern: '*.test.js', isDirectory: false },
        { pattern: 'build', isDirectory: true }
      ]);
    });
    
    it('should handle patterns with special characters', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, '**/*.test.js\n__pycache__/\n*.pyc\n.DS_Store');
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([
        { pattern: '**/*.test.js', isDirectory: false },
        { pattern: '__pycache__', isDirectory: true },
        { pattern: '*.pyc', isDirectory: false },
        { pattern: '.DS_Store', isDirectory: false }
      ]);
    });
    
    it('should handle Windows line endings', () => {
      const filePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(filePath, 'node_modules\r\n*.test.js\r\nbuild/');
      
      const patterns = parseIgnoreFile(filePath);
      
      expect(patterns).toEqual([
        { pattern: 'node_modules', isDirectory: false },
        { pattern: '*.test.js', isDirectory: false },
        { pattern: 'build', isDirectory: true }
      ]);
    });
    
    it('should throw error if file does not exist', () => {
      const filePath = path.join(tempDir, 'nonexistent.txt');
      
      expect(() => parseIgnoreFile(filePath)).toThrow();
    });
  });

  describe('matchesPattern', () => {
    describe('simple patterns', () => {
      it('should match exact file names', () => {
        const pattern: IgnorePattern = { pattern: 'README.md', isDirectory: false };
        
        expect(matchesPattern('README.md', pattern)).toBe(true);
        expect(matchesPattern('src/README.md', pattern)).toBe(true);
        expect(matchesPattern('docs/README.md', pattern)).toBe(true);
        expect(matchesPattern('NOTREADME.md', pattern)).toBe(false);
      });
      
      it('should match exact directory names', () => {
        const pattern: IgnorePattern = { pattern: 'node_modules', isDirectory: false };
        
        expect(matchesPattern('node_modules', pattern)).toBe(true);
        expect(matchesPattern('src/node_modules', pattern)).toBe(true);
        expect(matchesPattern('node_modules/package', pattern)).toBe(true);
      });
    });
    
    describe('glob patterns', () => {
      it('should match wildcard patterns', () => {
        const pattern: IgnorePattern = { pattern: '*.test.js', isDirectory: false };
        
        expect(matchesPattern('file.test.js', pattern)).toBe(true);
        expect(matchesPattern('src/file.test.js', pattern)).toBe(true);
        expect(matchesPattern('file.js', pattern)).toBe(false);
        expect(matchesPattern('file.test.ts', pattern)).toBe(false);
      });
      
      it('should match double-star patterns', () => {
        const pattern: IgnorePattern = { pattern: '**/*.pyc', isDirectory: false };
        
        expect(matchesPattern('file.pyc', pattern)).toBe(true);
        expect(matchesPattern('src/file.pyc', pattern)).toBe(true);
        expect(matchesPattern('src/deep/nested/file.pyc', pattern)).toBe(true);
        expect(matchesPattern('file.py', pattern)).toBe(false);
      });
      
      it('should match patterns with multiple wildcards', () => {
        const pattern: IgnorePattern = { pattern: '*.test.*', isDirectory: false };
        
        expect(matchesPattern('file.test.js', pattern)).toBe(true);
        expect(matchesPattern('file.test.ts', pattern)).toBe(true);
        expect(matchesPattern('src/file.test.py', pattern)).toBe(true);
        expect(matchesPattern('file.js', pattern)).toBe(false);
      });
    });
    
    describe('directory patterns', () => {
      it('should match directory and all contents', () => {
        const pattern: IgnorePattern = { pattern: 'node_modules', isDirectory: true };
        
        expect(matchesPattern('node_modules', pattern)).toBe(true);
        expect(matchesPattern('node_modules/package', pattern)).toBe(true);
        expect(matchesPattern('node_modules/package/file.js', pattern)).toBe(true);
        expect(matchesPattern('src/node_modules', pattern)).toBe(true);
        expect(matchesPattern('src/node_modules/package/file.js', pattern)).toBe(true);
      });
      
      it('should match nested directories', () => {
        const pattern: IgnorePattern = { pattern: 'build', isDirectory: true };
        
        expect(matchesPattern('build', pattern)).toBe(true);
        expect(matchesPattern('build/output.js', pattern)).toBe(true);
        expect(matchesPattern('src/build', pattern)).toBe(true);
        expect(matchesPattern('src/build/output.js', pattern)).toBe(true);
        expect(matchesPattern('builder.js', pattern)).toBe(false);
      });
      
      it('should match __pycache__ directories', () => {
        const pattern: IgnorePattern = { pattern: '__pycache__', isDirectory: true };
        
        expect(matchesPattern('__pycache__', pattern)).toBe(true);
        expect(matchesPattern('__pycache__/file.pyc', pattern)).toBe(true);
        expect(matchesPattern('src/__pycache__', pattern)).toBe(true);
        expect(matchesPattern('src/__pycache__/file.pyc', pattern)).toBe(true);
      });
    });
    
    describe('special cases', () => {
      it('should handle paths with backslashes (Windows)', () => {
        const pattern: IgnorePattern = { pattern: '*.test.js', isDirectory: false };
        
        expect(matchesPattern('src\\file.test.js', pattern)).toBe(true);
        expect(matchesPattern('src\\deep\\file.test.js', pattern)).toBe(true);
      });
      
      it('should handle dot files', () => {
        const pattern: IgnorePattern = { pattern: '.DS_Store', isDirectory: false };
        
        expect(matchesPattern('.DS_Store', pattern)).toBe(true);
        expect(matchesPattern('src/.DS_Store', pattern)).toBe(true);
        expect(matchesPattern('DS_Store', pattern)).toBe(false);
      });
      
      it('should handle patterns with dots', () => {
        const pattern: IgnorePattern = { pattern: '*.pyc', isDirectory: false };
        
        expect(matchesPattern('file.pyc', pattern)).toBe(true);
        expect(matchesPattern('src/file.pyc', pattern)).toBe(true);
        expect(matchesPattern('.pyc', pattern)).toBe(true);
      });
      
      it('should not match partial file names', () => {
        const pattern: IgnorePattern = { pattern: 'test', isDirectory: false };
        
        expect(matchesPattern('test', pattern)).toBe(true);
        expect(matchesPattern('src/test', pattern)).toBe(true);
        expect(matchesPattern('test.js', pattern)).toBe(false);
        expect(matchesPattern('testing.js', pattern)).toBe(false);
      });
    });
    
    describe('edge cases', () => {
      it('should handle empty paths', () => {
        const pattern: IgnorePattern = { pattern: '*.js', isDirectory: false };
        
        expect(matchesPattern('', pattern)).toBe(false);
      });
      
      it('should handle root-level files', () => {
        const pattern: IgnorePattern = { pattern: '*.md', isDirectory: false };
        
        expect(matchesPattern('README.md', pattern)).toBe(true);
        expect(matchesPattern('CHANGELOG.md', pattern)).toBe(true);
      });
      
      it('should handle deeply nested paths', () => {
        const pattern: IgnorePattern = { pattern: '*.test.js', isDirectory: false };
        
        expect(matchesPattern('a/b/c/d/e/f/file.test.js', pattern)).toBe(true);
      });
    });
  });
});
