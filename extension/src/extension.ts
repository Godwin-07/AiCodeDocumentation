/**
 * Main entry point for the AI Code Documentation Generator VS Code extension
 */

import * as vscode from 'vscode';
import { generateDocumentation, generateForCurrentFile, addDocstringsToCurrentFile } from './commands';
import { DocGeneratorSidebarProvider } from './sidebarProvider';

/**
 * Called when the extension is activated
 * Registers commands and sets up the extension
 */
export function activate(context: vscode.ExtensionContext): void {
  console.log('AI Code Documentation Generator extension is now active');

  // Register the sidebar provider
  const sidebarProvider = new DocGeneratorSidebarProvider(context.extensionUri);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      DocGeneratorSidebarProvider.viewType,
      sidebarProvider
    )
  );

  // Register the "Generate Code Documentation" command
  const generateDocCommand = vscode.commands.registerCommand(
    'ai-code-doc-generator.generateDocumentation',
    generateDocumentation
  );

  // Register the "Generate Documentation for Current File" command
  const generateCurrentFileCommand = vscode.commands.registerCommand(
    'ai-code-doc-generator.generateForCurrentFile',
    generateForCurrentFile
  );

  // Register the "Add AI Docstrings to Current File" command
  const addDocstringsCommand = vscode.commands.registerCommand(
    'ai-code-doc-generator.addDocstrings',
    addDocstringsToCurrentFile
  );

  // Add commands to subscriptions for proper cleanup
  context.subscriptions.push(
    generateDocCommand,
    generateCurrentFileCommand,
    addDocstringsCommand
  );
}

/**
 * Called when the extension is deactivated
 */
export function deactivate(): void {
  console.log('AI Code Documentation Generator extension is now deactivated');
}
