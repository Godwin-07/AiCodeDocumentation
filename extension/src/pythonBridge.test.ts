/**
 * Unit tests for pythonBridge module
 * 
 * Requirements: 8.4, 8.5
 */

import { spawn } from 'child_process';
import { spawnPythonEngine } from './pythonBridge';
import { PythonEngineInput, PythonEngineOutput } from './types';

// Mock child_process.spawn
jest.mock('child_process');

describe('pythonBridge', () => {
  const mockSpawn = spawn as jest.MockedFunction<typeof spawn>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('spawnPythonEngine', () => {
    it('should successfully spawn Python process and parse output', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py', 'file2.js'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const expectedOutput: PythonEngineOutput = {
        success: true,
        documentationPath: '/test/workspace/DOCUMENTATION.md',
        filesProcessed: 2,
        filesSkipped: 0,
        errors: [],
      };

      // Create mock process
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              // Simulate stdout data
              callback(Buffer.from(JSON.stringify(expectedOutput)));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            // Simulate successful exit
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      const result = await spawnPythonEngine(input);

      // Assert
      expect(mockSpawn).toHaveBeenCalledWith('python3', ['-m', 'analysis_engine.main'], {
        cwd: process.cwd(),
        stdio: ['pipe', 'pipe', 'pipe'],
      });
      expect(mockProcess.stdin.write).toHaveBeenCalledWith(JSON.stringify(input));
      expect(mockProcess.stdin.end).toHaveBeenCalled();
      expect(result).toEqual(expectedOutput);
    });

    it('should handle non-zero exit code', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const stderrMessage = 'Python error occurred';

      // Create mock process
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn(),
        },
        stderr: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              callback(Buffer.from(stderrMessage));
            }
          }),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            // Simulate error exit
            callback(1);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act & Assert
      await expect(spawnPythonEngine(input)).rejects.toThrow(
        'Python process exited with code 1'
      );
      await expect(spawnPythonEngine(input)).rejects.toThrow(stderrMessage);
    });

    it('should handle invalid JSON output', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const invalidJson = 'This is not valid JSON';

      // Create mock process
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              callback(Buffer.from(invalidJson));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act & Assert
      await expect(spawnPythonEngine(input)).rejects.toThrow(
        'Failed to parse Python output as JSON'
      );
    });

    it('should handle process spawn error', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const spawnError = new Error('Python not found');

      // Create mock process
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn(),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'error') {
            callback(spawnError);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act & Assert
      await expect(spawnPythonEngine(input)).rejects.toThrow(
        'Failed to spawn Python process: Python not found'
      );
    });

    it('should capture and log stderr output', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const expectedOutput: PythonEngineOutput = {
        success: true,
        documentationPath: '/test/workspace/DOCUMENTATION.md',
        filesProcessed: 1,
        filesSkipped: 0,
        errors: [],
      };

      const stderrMessage = 'Warning: Some warning message';
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      // Create mock process
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              callback(Buffer.from(JSON.stringify(expectedOutput)));
            }
          }),
        },
        stderr: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              callback(Buffer.from(stderrMessage));
            }
          }),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      await spawnPythonEngine(input);

      // Assert
      expect(consoleErrorSpy).toHaveBeenCalledWith('[Python Engine]', stderrMessage);
      consoleErrorSpy.mockRestore();
    });

    it('should handle output with errors but success=true', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py', 'file2.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const expectedOutput: PythonEngineOutput = {
        success: true,
        documentationPath: '/test/workspace/DOCUMENTATION.md',
        filesProcessed: 1,
        filesSkipped: 1,
        errors: ['Parse error in file2.py'],
      };

      // Create mock process
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              callback(Buffer.from(JSON.stringify(expectedOutput)));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      const result = await spawnPythonEngine(input);

      // Assert
      expect(result).toEqual(expectedOutput);
      expect(result.errors).toHaveLength(1);
    });

    it('should handle empty file list', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: [],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const expectedOutput: PythonEngineOutput = {
        success: true,
        filesProcessed: 0,
        filesSkipped: 0,
        errors: ['No files provided for processing'],
      };

      // Create mock process
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              callback(Buffer.from(JSON.stringify(expectedOutput)));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      const result = await spawnPythonEngine(input);

      // Assert
      expect(result).toEqual(expectedOutput);
    });

    it('should handle multiple stdout chunks', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const expectedOutput: PythonEngineOutput = {
        success: true,
        documentationPath: '/test/workspace/DOCUMENTATION.md',
        filesProcessed: 1,
        filesSkipped: 0,
        errors: [],
      };

      const outputJson = JSON.stringify(expectedOutput);
      const chunk1 = outputJson.substring(0, 20);
      const chunk2 = outputJson.substring(20);

      // Create mock process
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              // Simulate multiple chunks
              callback(Buffer.from(chunk1));
              callback(Buffer.from(chunk2));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      const result = await spawnPythonEngine(input);

      // Assert
      expect(result).toEqual(expectedOutput);
    });

    it('should pass correct input parameters to Python', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/custom/workspace',
        files: ['test1.py', 'test2.js', 'test3.java'],
        llmEndpoint: 'https://custom-llm:8080/api',
        llmTimeout: 60,
        llmModel: 'custom-model',
      };

      const expectedOutput: PythonEngineOutput = {
        success: true,
        documentationPath: '/custom/workspace/DOCUMENTATION.md',
        filesProcessed: 3,
        filesSkipped: 0,
        errors: [],
      };

      // Create mock process
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              callback(Buffer.from(JSON.stringify(expectedOutput)));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      await spawnPythonEngine(input);

      // Assert
      expect(mockProcess.stdin.write).toHaveBeenCalledWith(JSON.stringify(input));
      const writtenInput = JSON.parse(mockProcess.stdin.write.mock.calls[0][0]);
      expect(writtenInput.workspacePath).toBe('/custom/workspace');
      expect(writtenInput.files).toHaveLength(3);
      expect(writtenInput.llmEndpoint).toBe('https://custom-llm:8080/api');
      expect(writtenInput.llmTimeout).toBe(60);
      expect(writtenInput.llmModel).toBe('custom-model');
    });

    it('should handle progress messages and call progress callback', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: Array.from({ length: 105 }, (_, i) => `file${i}.py`),
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const progressCallback = jest.fn();

      // Create mock process that emits progress messages
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              // Simulate progress messages
              callback(Buffer.from('{"type": "progress", "processed": 10, "total": 105}\n'));
              callback(Buffer.from('{"type": "progress", "processed": 20, "total": 105}\n'));
              callback(Buffer.from('{"type": "progress", "processed": 30, "total": 105}\n'));
              // Final result
              callback(Buffer.from('{"type": "result", "success": true, "filesProcessed": 105, "filesSkipped": 0, "errors": []}\n'));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      const result = await spawnPythonEngine(input, progressCallback);

      // Assert
      expect(progressCallback).toHaveBeenCalledTimes(3);
      expect(progressCallback).toHaveBeenCalledWith(10, 105);
      expect(progressCallback).toHaveBeenCalledWith(20, 105);
      expect(progressCallback).toHaveBeenCalledWith(30, 105);
      expect(result.success).toBe(true);
      expect(result.filesProcessed).toBe(105);
    });

    it('should work without progress callback', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: Array.from({ length: 105 }, (_, i) => `file${i}.py`),
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      // Create mock process that emits progress messages
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              // Simulate progress messages (should be ignored without callback)
              callback(Buffer.from('{"type": "progress", "processed": 10, "total": 105}\n'));
              callback(Buffer.from('{"type": "progress", "processed": 20, "total": 105}\n'));
              // Final result
              callback(Buffer.from('{"type": "result", "success": true, "filesProcessed": 105, "filesSkipped": 0, "errors": []}\n'));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      const result = await spawnPythonEngine(input); // No progress callback

      // Assert
      expect(result.success).toBe(true);
      expect(result.filesProcessed).toBe(105);
    });

    it('should handle mixed progress and result messages', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py', 'file2.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const progressCallback = jest.fn();

      // Create mock process with interleaved messages
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              // Send all messages in one chunk
              const messages = [
                '{"type": "progress", "processed": 1, "total": 2}',
                '{"type": "progress", "processed": 2, "total": 2}',
                '{"type": "result", "success": true, "filesProcessed": 2, "filesSkipped": 0, "errors": []}',
              ].join('\n') + '\n';
              callback(Buffer.from(messages));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      const result = await spawnPythonEngine(input, progressCallback);

      // Assert
      expect(progressCallback).toHaveBeenCalledTimes(2);
      expect(progressCallback).toHaveBeenCalledWith(1, 2);
      expect(progressCallback).toHaveBeenCalledWith(2, 2);
      expect(result.success).toBe(true);
      expect(result.filesProcessed).toBe(2);
    });

    it('should handle partial JSON lines across chunks', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const progressCallback = jest.fn();

      // Create mock process that splits JSON across chunks
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              // Split a progress message across two chunks
              callback(Buffer.from('{"type": "progress", "processed": 1'));
              callback(Buffer.from(', "total": 1}\n'));
              // Complete result message
              callback(Buffer.from('{"type": "result", "success": true, "filesProcessed": 1, "filesSkipped": 0, "errors": []}\n'));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      const result = await spawnPythonEngine(input, progressCallback);

      // Assert
      expect(progressCallback).toHaveBeenCalledTimes(1);
      expect(progressCallback).toHaveBeenCalledWith(1, 1);
      expect(result.success).toBe(true);
    });

    it('should handle invalid JSON lines gracefully', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      // Create mock process with invalid JSON
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              // Invalid JSON line
              callback(Buffer.from('This is not JSON\n'));
              // Valid result
              callback(Buffer.from('{"type": "result", "success": true, "filesProcessed": 1, "filesSkipped": 0, "errors": []}\n'));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      const result = await spawnPythonEngine(input);

      // Assert
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[Python Engine] Failed to parse JSON line:',
        'This is not JSON'
      );
      expect(result.success).toBe(true);
      consoleErrorSpy.mockRestore();
    });

    it('should maintain backward compatibility with non-typed output', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      const legacyOutput: PythonEngineOutput = {
        success: true,
        documentationPath: '/test/workspace/DOCUMENTATION.md',
        filesProcessed: 1,
        filesSkipped: 0,
        errors: [],
      };

      // Create mock process with old-style output (no "type" field)
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              // Old format without "type" field
              callback(Buffer.from(JSON.stringify(legacyOutput)));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act
      const result = await spawnPythonEngine(input);

      // Assert
      expect(result).toEqual(legacyOutput);
    });

    it('should reject when no result message is received', async () => {
      // Arrange
      const input: PythonEngineInput = {
        workspacePath: '/test/workspace',
        files: ['file1.py'],
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2',
      };

      // Create mock process that only emits progress, no result
      const mockProcess = {
        stdin: {
          write: jest.fn(),
          end: jest.fn(),
        },
        stdout: {
          on: jest.fn((event, callback) => {
            if (event === 'data') {
              // Only progress, no result
              callback(Buffer.from('{"type": "progress", "processed": 1, "total": 1}\n'));
            }
          }),
        },
        stderr: {
          on: jest.fn(),
        },
        on: jest.fn((event, callback) => {
          if (event === 'close') {
            callback(0);
          }
        }),
      };

      mockSpawn.mockReturnValue(mockProcess as any);

      // Act & Assert
      await expect(spawnPythonEngine(input)).rejects.toThrow(
        'Python process completed but no result message was received'
      );
    });
  });
});
