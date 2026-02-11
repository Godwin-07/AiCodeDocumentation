/**
 * Command handlers for the AI Code Documentation Generator extension
 * 
 * This module implements the main command handler for generating documentation.
 * It orchestrates the entire workflow: reading ignore patterns, scanning the workspace,
 * spawning the Python analysis engine, and displaying progress/results to the user.
 * 
 * Validates: Requirements 7.2, 7.3, 7.4, 7.5
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { parseIgnoreFile } from './ignoreParser';
import { scanWorkspace } from './fileScanner';
import { spawnPythonEngine } from './pythonBridge';
import { IgnorePattern, PythonEngineInput } from './types';

/**
 * Command handler for "Generate Code Documentation"
 * 
 * This function:
 * - Gets the active workspace folder (Requirement 7.2)
 * - Displays progress notifications (Requirement 7.3)
 * - Loads ignore patterns from .docignore.txt (Requirement 1.2)
 * - Scans workspace for source files (Requirement 2.1)
 * - Spawns Python analysis engine (Requirement 8.1)
 * - Displays success/error messages (Requirement 7.4, 7.5)
 * 
 * Validates: Requirements 7.2, 7.3, 7.4, 7.5
 */
export async function generateDocumentation(): Promise<void> {
  // Get active workspace folder (Requirement 7.2)
  const workspaceFolders = vscode.workspace.workspaceFolders;
  
  if (!workspaceFolders || workspaceFolders.length === 0) {
    vscode.window.showErrorMessage('No workspace folder open. Please open a folder to generate documentation.');
    return;
  }
  
  // Use the first workspace folder
  const workspaceFolder = workspaceFolders[0];
  const workspacePath = workspaceFolder.uri.fsPath;
  
  // Display progress notification (Requirement 7.3)
  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: 'Generating documentation...',
      cancellable: false
    },
    async (progress) => {
      try {
        // Step 1: Load ignore patterns from .docignore.txt (Requirement 1.2)
        progress.report({ message: 'Loading ignore patterns...' });
        const ignorePatterns = await loadIgnorePatterns(workspacePath);
        
        // Step 2: Scan workspace for source files (Requirement 2.1)
        progress.report({ message: 'Scanning workspace...' });
        const scanResult = scanWorkspace(workspacePath, ignorePatterns);
        
        // Check for scan errors
        if (scanResult.errors.length > 0) {
          console.warn('Workspace scan encountered errors:', scanResult.errors);
        }
        
        // Check if any files were found
        if (scanResult.files.length === 0) {
          vscode.window.showWarningMessage(
            'No source files found in workspace. Supported extensions: .py, .js, .java'
          );
          return;
        }
        
        console.log(`Found ${scanResult.files.length} source files (${scanResult.ignoredCount} ignored)`);
        
        // Step 3: Get LLM configuration from VS Code settings
        const config = vscode.workspace.getConfiguration('aiCodeDocGenerator');
        const llmEndpoint = config.get<string>('llmEndpoint', 'https://localhosted:11434/api/chat');
        const llmTimeout = config.get<number>('llmTimeout', 50);
        const llmModel = config.get<string>('llmModel', 'llama2:13b');
        const template = config.get<string>('documentationTemplate', 'standard');
        
        // Step 4: Prepare input for Python engine
        const pythonInput: PythonEngineInput = {
          workspacePath,
          files: scanResult.files,
          llmEndpoint,
          llmTimeout,
          llmModel,
          template
        };
        
        // Step 5: Spawn Python analysis engine (Requirement 8.1)
        progress.report({ message: 'Analyzing code...' });
        const engineOutput = await spawnPythonEngine(pythonInput);
        
        // Step 6: Update progress for documentation generation
        progress.report({ message: 'Generating documentation...' });
        
        // Step 7: Handle results
        if (engineOutput.success) {
          // Display success message with DOCUMENTATION.md path (Requirement 7.4)
          const docPath = engineOutput.documentationPath || path.join(workspacePath, 'DOCUMENTATION.md');
          const relativePath = path.relative(workspacePath, docPath);
          
          let message = `Documentation generated successfully! `;
          message += `Files processed: ${engineOutput.filesProcessed}`;
          
          if (engineOutput.filesSkipped > 0) {
            message += `, skipped: ${engineOutput.filesSkipped}`;
          }
          
          // Display error summary if there were any errors (Requirement 10.4, 10.5)
          if (engineOutput.errors.length > 0) {
            console.warn('Documentation generation completed with errors:', engineOutput.errors);
            
            // Show warning message with error count
            const errorCount = engineOutput.errors.length;
            const errorSummary = `Documentation generated with ${errorCount} error${errorCount > 1 ? 's' : ''}. `;
            const action = await vscode.window.showWarningMessage(
              errorSummary + message,
              'Open Documentation',
              'View Errors'
            );
            
            if (action === 'Open Documentation') {
              const docUri = vscode.Uri.file(docPath);
              await vscode.window.showTextDocument(docUri);
            } else if (action === 'View Errors') {
              // Display detailed error list in output channel
              const outputChannel = vscode.window.createOutputChannel('AI Code Doc Generator');
              outputChannel.clear();
              outputChannel.appendLine('Documentation Generation Errors:');
              outputChannel.appendLine('='.repeat(50));
              outputChannel.appendLine('');
              
              for (let i = 0; i < engineOutput.errors.length; i++) {
                outputChannel.appendLine(`${i + 1}. ${engineOutput.errors[i]}`);
              }
              
              outputChannel.appendLine('');
              outputChannel.appendLine('='.repeat(50));
              outputChannel.appendLine(`Total errors: ${errorCount}`);
              outputChannel.show();
            }
          } else {
            // No errors - show simple success message
            const action = await vscode.window.showInformationMessage(
              message,
              'Open Documentation'
            );
            
            if (action === 'Open Documentation') {
              const docUri = vscode.Uri.file(docPath);
              await vscode.window.showTextDocument(docUri);
            }
          }
        } else {
          // Display error message (Requirement 7.5)
          const errorDetails = engineOutput.errors.join('\n');
          vscode.window.showErrorMessage(
            `Documentation generation failed. ${errorDetails}`
          );
        }
      } catch (error) {
        // Handle errors and display error messages (Requirement 7.5)
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('Documentation generation error:', error);
        vscode.window.showErrorMessage(
          `Failed to generate documentation: ${errorMessage}`
        );
      }
    }
  );
}

/**
 * Load ignore patterns from .docignore.txt file
 * 
 * If the file doesn't exist, returns an empty array (Requirement 1.5)
 * If the file exists but cannot be read, logs a warning and returns an empty array
 * 
 * @param workspacePath - Absolute path to workspace root
 * @returns Array of ignore patterns
 */
async function loadIgnorePatterns(workspacePath: string): Promise<IgnorePattern[]> {
  const ignoreFilePath = path.join(workspacePath, '.docignore.txt');
  
  // Check if .docignore.txt exists (Requirement 1.1)
  if (!fs.existsSync(ignoreFilePath)) {
    console.log('No .docignore.txt file found, proceeding without ignore patterns');
    return [];
  }
  
  try {
    // Parse the ignore file (Requirement 1.2)
    const patterns = parseIgnoreFile(ignoreFilePath);
    console.log(`Loaded ${patterns.length} ignore patterns from .docignore.txt`);
    return patterns;
  } catch (error) {
    // If parsing fails, log warning and proceed without ignore patterns
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.warn(`Failed to parse .docignore.txt: ${errorMessage}`);
    vscode.window.showWarningMessage(
      'Failed to parse .docignore.txt file. Proceeding without ignore patterns.'
    );
    return [];
  }
}


/**
 * Command handler for "Generate Documentation for Current File"
 * 
 * Generates documentation for the currently active file only and saves it
 * as <filename>_DOCUMENTATION.md in the same directory as the source file.
 */
export async function generateForCurrentFile(): Promise<void> {
  // Get the active text editor
  const editor = vscode.window.activeTextEditor;
  
  if (!editor) {
    vscode.window.showErrorMessage('No file is currently open. Please open a file to generate documentation.');
    return;
  }
  
  const document = editor.document;
  const filePath = document.uri.fsPath;
  const fileName = path.basename(filePath);
  const fileDir = path.dirname(filePath);
  
  // Check if file is saved
  if (document.isUntitled) {
    vscode.window.showErrorMessage('Please save the file before generating documentation.');
    return;
  }
  
  // Check if file has supported extension
  const ext = path.extname(fileName);
  const supportedExtensions = ['.py', '.js', '.java'];
  
  if (!supportedExtensions.includes(ext)) {
    vscode.window.showErrorMessage(
      `Unsupported file type: ${ext}. Supported types: .py, .js, .java`
    );
    return;
  }
  
  // Display progress notification
  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: `Generating documentation for ${fileName}...`,
      cancellable: false
    },
    async (progress) => {
      try {
        progress.report({ message: 'Analyzing code...' });
        
        // Get LLM configuration
        const config = vscode.workspace.getConfiguration('aiCodeDocGenerator');
        const llmEndpoint = config.get<string>('llmEndpoint', 'http://localhost:11434/api/chat');
        const llmTimeout = config.get<number>('llmTimeout', 120);
        const llmModel = config.get<string>('llmModel', 'llama2:7b');
        
        // Get workspace root (use file directory if no workspace)
        const workspaceFolders = vscode.workspace.workspaceFolders;
        const workspacePath = workspaceFolders ? workspaceFolders[0].uri.fsPath : fileDir;
        
        // Prepare input for Python engine
        const pythonInput = {
          workspacePath: fileDir,
          files: [filePath],
          llmEndpoint,
          llmTimeout,
          llmModel,
          mode: 'single-file',  // New mode for single file documentation
          outputFileName: path.basename(filePath, ext) + '_DOCUMENTATION.md'
        };
        
        progress.report({ message: 'Generating documentation...' });
        
        // Spawn Python analysis engine
        const engineOutput = await spawnPythonEngine(pythonInput);
        
        if (engineOutput.success) {
          const docPath = engineOutput.documentationPath || 
                         path.join(fileDir, path.basename(filePath, ext) + '_DOCUMENTATION.md');
          
          let message = `Documentation generated successfully for ${fileName}!`;
          
          if (engineOutput.errors.length > 0) {
            console.warn('Documentation generated with warnings:', engineOutput.errors);
            message += ` (with ${engineOutput.errors.length} warning(s))`;
          }
          
          const action = await vscode.window.showInformationMessage(
            message,
            'Open Documentation'
          );
          
          if (action === 'Open Documentation') {
            const docUri = vscode.Uri.file(docPath);
            await vscode.window.showTextDocument(docUri);
          }
        } else {
          const errorDetails = engineOutput.errors.join('\n');
          vscode.window.showErrorMessage(
            `Failed to generate documentation: ${errorDetails}`
          );
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('Documentation generation error:', error);
        vscode.window.showErrorMessage(
          `Failed to generate documentation: ${errorMessage}`
        );
      }
    }
  );
}

/**
 * Command handler for "Add AI Docstrings to Current File"
 * 
 * Adds AI-generated docstrings and comments to the currently active file.
 * Modifies the file in-place with enhanced documentation.
 */
export async function addDocstringsToCurrentFile(): Promise<void> {
  // Get the active text editor
  const editor = vscode.window.activeTextEditor;
  
  if (!editor) {
    vscode.window.showErrorMessage('No file is currently open. Please open a file to add docstrings.');
    return;
  }
  
  const document = editor.document;
  const filePath = document.uri.fsPath;
  const fileName = path.basename(filePath);
  
  // Check if file is saved
  if (document.isUntitled) {
    vscode.window.showErrorMessage('Please save the file before adding docstrings.');
    return;
  }
  
  // Check if file has unsaved changes
  if (document.isDirty) {
    const action = await vscode.window.showWarningMessage(
      'The file has unsaved changes. Save before adding docstrings?',
      'Save and Continue',
      'Cancel'
    );
    
    if (action === 'Save and Continue') {
      await document.save();
    } else {
      return;
    }
  }
  
  // Check if file has supported extension
  const ext = path.extname(fileName);
  const supportedExtensions = ['.py', '.js', '.java'];
  
  if (!supportedExtensions.includes(ext)) {
    vscode.window.showErrorMessage(
      `Unsupported file type: ${ext}. Supported types: .py, .js, .java`
    );
    return;
  }
  
  // Confirm action with user
  const confirmation = await vscode.window.showWarningMessage(
    `This will modify ${fileName} by adding AI-generated docstrings and comments. A backup will be created. Continue?`,
    'Yes, Add Docstrings',
    'Cancel'
  );
  
  if (confirmation !== 'Yes, Add Docstrings') {
    return;
  }
  
  // Display progress notification
  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: `Adding docstrings to ${fileName}...`,
      cancellable: false
    },
    async (progress) => {
      try {
        progress.report({ message: 'Creating backup...' });
        
        // Create backup file
        const backupPath = filePath + '.backup';
        fs.copyFileSync(filePath, backupPath);
        console.log(`Backup created at: ${backupPath}`);
        
        progress.report({ message: 'Analyzing code...' });
        
        // Get LLM configuration
        const config = vscode.workspace.getConfiguration('aiCodeDocGenerator');
        const llmEndpoint = config.get<string>('llmEndpoint', 'http://localhost:11434/api/chat');
        const llmTimeout = config.get<number>('llmTimeout', 120);
        const llmModel = config.get<string>('llmModel', 'llama2:7b');
        
        const fileDir = path.dirname(filePath);
        
        // Prepare input for Python engine
        const pythonInput = {
          workspacePath: fileDir,
          files: [filePath],
          llmEndpoint,
          llmTimeout,
          llmModel,
          mode: 'add-docstrings',  // New mode for adding docstrings
          backupPath: backupPath
        };
        
        progress.report({ message: 'Generating docstrings with AI...' });
        
        // Spawn Python analysis engine
        const engineOutput = await spawnPythonEngine(pythonInput);
        
        if (engineOutput.success) {
          // Reload the file to show changes
          const docUri = vscode.Uri.file(filePath);
          await vscode.window.showTextDocument(docUri);
          
          let message = `AI docstrings added successfully to ${fileName}!`;
          message += `\nBackup saved as: ${path.basename(backupPath)}`;
          
          if (engineOutput.errors.length > 0) {
            console.warn('Docstrings added with warnings:', engineOutput.errors);
            message += `\n(with ${engineOutput.errors.length} warning(s))`;
          }
          
          vscode.window.showInformationMessage(message);
        } else {
          // Restore from backup on failure
          fs.copyFileSync(backupPath, filePath);
          
          const errorDetails = engineOutput.errors.join('\n');
          vscode.window.showErrorMessage(
            `Failed to add docstrings: ${errorDetails}\nFile restored from backup.`
          );
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('Add docstrings error:', error);
        
        // Try to restore from backup
        const backupPath = filePath + '.backup';
        if (fs.existsSync(backupPath)) {
          try {
            fs.copyFileSync(backupPath, filePath);
            vscode.window.showErrorMessage(
              `Failed to add docstrings: ${errorMessage}\nFile restored from backup.`
            );
          } catch (restoreError) {
            vscode.window.showErrorMessage(
              `Failed to add docstrings and restore backup: ${errorMessage}`
            );
          }
        } else {
          vscode.window.showErrorMessage(
            `Failed to add docstrings: ${errorMessage}`
          );
        }
      }
    }
  );
}
