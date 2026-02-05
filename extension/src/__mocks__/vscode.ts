/**
 * Mock implementation of VS Code API for testing
 */

export const window = {
  showErrorMessage: jest.fn(),
  showWarningMessage: jest.fn(),
  showInformationMessage: jest.fn(),
  withProgress: jest.fn(),
  showTextDocument: jest.fn()
};

export const workspace = {
  workspaceFolders: undefined as any,
  getConfiguration: jest.fn()
};

export const ProgressLocation = {
  Notification: 15
};

export const Uri = {
  file: jest.fn((path: string) => ({ fsPath: path }))
};

export const commands = {
  registerCommand: jest.fn()
};
