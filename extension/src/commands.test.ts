/**
 * Unit tests for commands module
 * 
 * Tests the generateDocumentation command handler including:
 * - Successful documentation generation
 * - Error handling for no workspace
 * - Error handling for Python process failure
 * - Progress notification updates
 * 
 * Validates: Requirements 7.2, 7.3, 7.4, 7.5
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { generateDocumentation } from './commands';
import * as ignoreParser from './ignoreParser';
import * as fileScanner from './fileScanner';
import * as pythonBridge from './pythonBridge';
import { FileDiscoveryResult, PythonEngineOutput } from './types';

// Mock VS Code API
jest.mock('vscode', () => ({
  workspace: {
    workspaceFolders: [],
    getConfiguration: jest.fn()
  },
  window: {
    showErrorMessage: jest.fn(),
    showWarningMessage: jest.fn(),
    showInformationMessage: jest.fn(),
    showTextDocument: jest.fn(),
    withProgress: jest.fn(),
    createOutputChannel: jest.fn()
  },
  ProgressLocation: {
    Notification: 15
  },
  Uri: {
    file: (path: string) => ({ fsPath: path })
  }
}));

// Mock modules
jest.mock('./ignoreParser');
jest.mock('./fileScanner');
jest.mock('./pythonBridge');

describe('commands', () => {
  let tempDir: string;
  
  beforeEach(() => {
    // Create a temporary directory for test files
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'commands-test-'));
    
    // Reset all mocks
    jest.clearAllMocks();
    
    // Setup default mock implementations
    (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
      get: jest.fn((key: string, defaultValue: any) => defaultValue)
    });
    
    // Mock withProgress to immediately call the callback
    (vscode.window.withProgress as jest.Mock).mockImplementation(
      async (options: any, callback: any) => {
        const progress = {
          report: jest.fn()
        };
        return await callback(progress);
      }
    );
    
    // Mock createOutputChannel
    (vscode.window.createOutputChannel as jest.Mock).mockReturnValue({
      clear: jest.fn(),
      appendLine: jest.fn(),
      show: jest.fn()
    });
  });
  
  afterEach(() => {
    // Clean up temporary directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });
  
  describe('generateDocumentation', () => {
    it('should show error when no workspace folder is open', async () => {
      // Setup: No workspace folders
      (vscode.workspace as any).workspaceFolders = undefined;
      
      // Execute
      await generateDocumentation();
      
      // Verify
      expect(vscode.window.showErrorMessage).toHaveBeenCalledWith(
        'No workspace folder open. Please open a folder to generate documentation.'
      );
    });
    
    it('should show error when workspace folders array is empty', async () => {
      // Setup: Empty workspace folders array
      (vscode.workspace as any).workspaceFolders = [];
      
      // Execute
      await generateDocumentation();
      
      // Verify
      expect(vscode.window.showErrorMessage).toHaveBeenCalledWith(
        'No workspace folder open. Please open a folder to generate documentation.'
      );
    });
    
    it('should show warning when no source files are found', async () => {
      // Setup: Workspace with no source files
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      // Execute
      await generateDocumentation();
      
      // Verify
      expect(vscode.window.showWarningMessage).toHaveBeenCalledWith(
        'No source files found in workspace. Supported extensions: .py, .js, .java'
      );
    });
    
    it('should successfully generate documentation', async () => {
      // Setup: Workspace with source files
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      // Create a test .docignore.txt file
      const ignoreFilePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(ignoreFilePath, 'node_modules/\n*.test.js');
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([
        { pattern: 'node_modules', isDirectory: true },
        { pattern: '*.test.js', isDirectory: false }
      ]);
      
      const scanResult: FileDiscoveryResult = {
        files: [
          path.join(tempDir, 'file1.py'),
          path.join(tempDir, 'file2.js')
        ],
        ignoredCount: 5,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: path.join(tempDir, 'DOCUMENTATION.md'),
        filesProcessed: 2,
        filesSkipped: 0,
        errors: []
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      (vscode.window.showInformationMessage as jest.Mock).mockResolvedValue(undefined);
      
      // Execute
      await generateDocumentation();
      
      // Verify
      expect(ignoreParser.parseIgnoreFile).toHaveBeenCalledWith(ignoreFilePath);
      expect(fileScanner.scanWorkspace).toHaveBeenCalledWith(tempDir, [
        { pattern: 'node_modules', isDirectory: true },
        { pattern: '*.test.js', isDirectory: false }
      ]);
      expect(pythonBridge.spawnPythonEngine).toHaveBeenCalledWith({
        workspacePath: tempDir,
        files: scanResult.files,
        llmEndpoint: 'https://localhosted:11434/api/chat',
        llmTimeout: 30,
        llmModel: 'llama2'
      });
      expect(vscode.window.showInformationMessage).toHaveBeenCalledWith(
        'Documentation generated successfully! Files processed: 2',
        'Open Documentation'
      );
    });
    
    it('should handle documentation generation with skipped files', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: path.join(tempDir, 'DOCUMENTATION.md'),
        filesProcessed: 3,
        filesSkipped: 2,
        errors: ['Error parsing file1.js', 'Error parsing file2.java']
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      (vscode.window.showWarningMessage as jest.Mock).mockResolvedValue(undefined);
      
      // Execute
      await generateDocumentation();
      
      // Verify - should show warning message because there are errors
      expect(vscode.window.showWarningMessage).toHaveBeenCalledWith(
        expect.stringContaining('Documentation generated with 2 errors'),
        'Open Documentation',
        'View Errors'
      );
    });
    
    it('should open documentation when user clicks "Open Documentation"', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const docPath = path.join(tempDir, 'DOCUMENTATION.md');
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: docPath,
        filesProcessed: 1,
        filesSkipped: 0,
        errors: []
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      // User clicks "Open Documentation"
      (vscode.window.showInformationMessage as jest.Mock).mockResolvedValue('Open Documentation');
      
      // Execute
      await generateDocumentation();
      
      // Verify
      expect(vscode.window.showTextDocument).toHaveBeenCalledWith({ fsPath: docPath });
    });
    
    it('should handle Python engine failure', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: false,
        filesProcessed: 0,
        filesSkipped: 1,
        errors: ['Python process crashed', 'Failed to parse file']
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      // Execute
      await generateDocumentation();
      
      // Verify
      expect(vscode.window.showErrorMessage).toHaveBeenCalledWith(
        'Documentation generation failed. Python process crashed\nFailed to parse file'
      );
    });
    
    it('should handle Python process exception', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const error = new Error('Python not found in PATH');
      (pythonBridge.spawnPythonEngine as jest.Mock).mockRejectedValue(error);
      
      // Execute
      await generateDocumentation();
      
      // Verify
      expect(vscode.window.showErrorMessage).toHaveBeenCalledWith(
        'Failed to generate documentation: Python not found in PATH'
      );
    });
    
    it('should proceed without ignore patterns if .docignore.txt does not exist', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      // No .docignore.txt file exists
      // parseIgnoreFile will be called but should handle missing file
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: path.join(tempDir, 'DOCUMENTATION.md'),
        filesProcessed: 1,
        filesSkipped: 0,
        errors: []
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      (vscode.window.showInformationMessage as jest.Mock).mockResolvedValue(undefined);
      
      // Execute
      await generateDocumentation();
      
      // Verify - should call scanWorkspace with empty ignore patterns
      expect(fileScanner.scanWorkspace).toHaveBeenCalledWith(tempDir, []);
    });
    
    it('should use custom LLM configuration from settings', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      // Mock custom configuration
      (vscode.workspace.getConfiguration as jest.Mock).mockReturnValue({
        get: jest.fn((key: string, defaultValue: any) => {
          if (key === 'llmEndpoint') return 'http://custom-llm:8080/api';
          if (key === 'llmTimeout') return 60;
          if (key === 'llmModel') return 'custom-model';
          return defaultValue;
        })
      });
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: path.join(tempDir, 'DOCUMENTATION.md'),
        filesProcessed: 1,
        filesSkipped: 0,
        errors: []
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      (vscode.window.showInformationMessage as jest.Mock).mockResolvedValue(undefined);
      
      // Execute
      await generateDocumentation();
      
      // Verify - should use custom configuration
      expect(pythonBridge.spawnPythonEngine).toHaveBeenCalledWith({
        workspacePath: tempDir,
        files: scanResult.files,
        llmEndpoint: 'http://custom-llm:8080/api',
        llmTimeout: 60,
        llmModel: 'custom-model'
      });
    });
    
    it('should handle scan errors gracefully', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: ['Permission denied: /some/directory', 'Cannot read: /another/directory']
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: path.join(tempDir, 'DOCUMENTATION.md'),
        filesProcessed: 1,
        filesSkipped: 0,
        errors: []
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      (vscode.window.showInformationMessage as jest.Mock).mockResolvedValue(undefined);
      
      // Execute
      await generateDocumentation();
      
      // Verify - should still proceed with documentation generation
      expect(pythonBridge.spawnPythonEngine).toHaveBeenCalled();
      expect(vscode.window.showInformationMessage).toHaveBeenCalled();
    });
    
    it('should show warning if .docignore.txt parsing fails', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      // Create a .docignore.txt file
      const ignoreFilePath = path.join(tempDir, '.docignore.txt');
      fs.writeFileSync(ignoreFilePath, 'node_modules/');
      
      // Mock parseIgnoreFile to throw an error
      (ignoreParser.parseIgnoreFile as jest.Mock).mockImplementation(() => {
        throw new Error('Failed to read file');
      });
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: path.join(tempDir, 'DOCUMENTATION.md'),
        filesProcessed: 1,
        filesSkipped: 0,
        errors: []
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      (vscode.window.showInformationMessage as jest.Mock).mockResolvedValue(undefined);
      
      // Execute
      await generateDocumentation();
      
      // Verify - should show warning and proceed with empty ignore patterns
      expect(vscode.window.showWarningMessage).toHaveBeenCalledWith(
        'Failed to parse .docignore.txt file. Proceeding without ignore patterns.'
      );
      expect(fileScanner.scanWorkspace).toHaveBeenCalledWith(tempDir, []);
    });
    
    it('should display error summary when errors occur during processing', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: path.join(tempDir, 'DOCUMENTATION.md'),
        filesProcessed: 3,
        filesSkipped: 2,
        errors: [
          'file1.py: Parse error on line 5',
          'file2.js: Used basic documentation due to LLM timeout',
          'file3.java: File not found'
        ]
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      (vscode.window.showWarningMessage as jest.Mock).mockResolvedValue(undefined);
      
      // Execute
      await generateDocumentation();
      
      // Verify - should show warning message with error count
      expect(vscode.window.showWarningMessage).toHaveBeenCalledWith(
        expect.stringContaining('Documentation generated with 3 error'),
        'Open Documentation',
        'View Errors'
      );
    });
    
    it('should open output channel when user clicks "View Errors"', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: path.join(tempDir, 'DOCUMENTATION.md'),
        filesProcessed: 2,
        filesSkipped: 1,
        errors: [
          'file1.py: Parse error',
          'file2.js: LLM timeout'
        ]
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      // User clicks "View Errors"
      (vscode.window.showWarningMessage as jest.Mock).mockResolvedValue('View Errors');
      
      // Mock output channel
      const mockOutputChannel = {
        clear: jest.fn(),
        appendLine: jest.fn(),
        show: jest.fn()
      };
      (vscode.window.createOutputChannel as jest.Mock).mockReturnValue(mockOutputChannel);
      
      // Execute
      await generateDocumentation();
      
      // Verify - should create and show output channel with errors
      expect(vscode.window.createOutputChannel).toHaveBeenCalledWith('AI Code Doc Generator');
      expect(mockOutputChannel.clear).toHaveBeenCalled();
      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith('Documentation Generation Errors:');
      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(expect.stringContaining('1. file1.py: Parse error'));
      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(expect.stringContaining('2. file2.js: LLM timeout'));
      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith('Total errors: 2');
      expect(mockOutputChannel.show).toHaveBeenCalled();
    });
    
    it('should show simple success message when no errors occur', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: path.join(tempDir, 'DOCUMENTATION.md'),
        filesProcessed: 5,
        filesSkipped: 0,
        errors: []  // No errors
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      (vscode.window.showInformationMessage as jest.Mock).mockResolvedValue(undefined);
      
      // Execute
      await generateDocumentation();
      
      // Verify - should show information message (not warning)
      expect(vscode.window.showInformationMessage).toHaveBeenCalledWith(
        'Documentation generated successfully! Files processed: 5',
        'Open Documentation'
      );
      expect(vscode.window.showWarningMessage).not.toHaveBeenCalled();
    });
    
    it('should handle single error correctly (singular form)', async () => {
      // Setup
      (vscode.workspace as any).workspaceFolders = [
        { uri: { fsPath: tempDir } }
      ];
      
      (ignoreParser.parseIgnoreFile as jest.Mock).mockReturnValue([]);
      
      const scanResult: FileDiscoveryResult = {
        files: [path.join(tempDir, 'file1.py')],
        ignoredCount: 0,
        errors: []
      };
      (fileScanner.scanWorkspace as jest.Mock).mockReturnValue(scanResult);
      
      const engineOutput: PythonEngineOutput = {
        success: true,
        documentationPath: path.join(tempDir, 'DOCUMENTATION.md'),
        filesProcessed: 2,
        filesSkipped: 1,
        errors: ['file1.py: Parse error']  // Single error
      };
      (pythonBridge.spawnPythonEngine as jest.Mock).mockResolvedValue(engineOutput);
      
      (vscode.window.showWarningMessage as jest.Mock).mockResolvedValue(undefined);
      
      // Execute
      await generateDocumentation();
      
      // Verify - should use singular "error" not "errors"
      expect(vscode.window.showWarningMessage).toHaveBeenCalledWith(
        expect.stringContaining('Documentation generated with 1 error.'),
        'Open Documentation',
        'View Errors'
      );
    });
  });
});
