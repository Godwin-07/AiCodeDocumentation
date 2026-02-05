/**
 * Unit tests for type definitions
 */
import {
  FileDiscoveryResult,
  IgnorePattern,
  PythonEngineInput,
  PythonEngineOutput,
  ProgressUpdate
} from './types';

describe('Type Definitions', () => {
  test('FileDiscoveryResult structure', () => {
    const result: FileDiscoveryResult = {
      files: ['/path/to/file.py'],
      ignoredCount: 5,
      errors: []
    };
    
    expect(result.files).toHaveLength(1);
    expect(result.ignoredCount).toBe(5);
    expect(result.errors).toEqual([]);
  });

  test('IgnorePattern structure', () => {
    const pattern: IgnorePattern = {
      pattern: 'node_modules/',
      isDirectory: true
    };
    
    expect(pattern.pattern).toBe('node_modules/');
    expect(pattern.isDirectory).toBe(true);
  });

  test('PythonEngineInput structure', () => {
    const input: PythonEngineInput = {
      workspacePath: '/workspace',
      files: ['file1.py', 'file2.js'],
      llmEndpoint: 'https://localhosted:11434/api/chat',
      llmTimeout: 30,
      llmModel: 'llama2'
    };
    
    expect(input.workspacePath).toBe('/workspace');
    expect(input.files).toHaveLength(2);
    expect(input.llmEndpoint).toBe('https://localhosted:11434/api/chat');
    expect(input.llmTimeout).toBe(30);
    expect(input.llmModel).toBe('llama2');
  });

  test('PythonEngineOutput structure', () => {
    const output: PythonEngineOutput = {
      success: true,
      documentationPath: '/workspace/DOCUMENTATION.md',
      filesProcessed: 10,
      filesSkipped: 2,
      errors: ['Error in file1.py']
    };
    
    expect(output.success).toBe(true);
    expect(output.documentationPath).toBe('/workspace/DOCUMENTATION.md');
    expect(output.filesProcessed).toBe(10);
    expect(output.filesSkipped).toBe(2);
    expect(output.errors).toHaveLength(1);
  });

  test('ProgressUpdate structure', () => {
    const update: ProgressUpdate = {
      type: 'progress',
      processed: 5,
      total: 20
    };
    
    expect(update.type).toBe('progress');
    expect(update.processed).toBe(5);
    expect(update.total).toBe(20);
  });
});
