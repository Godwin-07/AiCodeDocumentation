/**
 * Sidebar provider for AI Code Documentation Generator
 * Provides a custom UI panel in the VS Code sidebar
 */

import * as vscode from 'vscode';
import { generateDocumentation, generateForCurrentFile, addDocstringsToCurrentFile } from './commands';

export class DocGeneratorSidebarProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'aiCodeDocGenerator.sidebar';
  private _view?: vscode.WebviewView;

  constructor(private readonly _extensionUri: vscode.Uri) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ) {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri]
    };

    webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

    // Handle messages from the webview
    webviewView.webview.onDidReceiveMessage(async (data) => {
      switch (data.type) {
        case 'generateWorkspace':
          await generateDocumentation();
          break;
        case 'generateCurrentFile':
          await generateForCurrentFile();
          break;
        case 'addDocstrings':
          await addDocstringsToCurrentFile();
          break;
        case 'updateSetting':
          await this._updateSetting(data.setting, data.value);
          break;
        case 'requestSettings':
          await this._sendCurrentSettings();
          break;
      }
    });

    // Send initial settings
    this._sendCurrentSettings();
  }

  private async _updateSetting(setting: string, value: any) {
    const config = vscode.workspace.getConfiguration('aiCodeDocGenerator');
    await config.update(setting, value, vscode.ConfigurationTarget.Global);
    
    // Send updated settings back to webview
    await this._sendCurrentSettings();
    
    // Show confirmation
    vscode.window.showInformationMessage(`Setting updated: ${setting}`);
  }

  private async _sendCurrentSettings() {
    if (!this._view) {
      return;
    }

    const config = vscode.workspace.getConfiguration('aiCodeDocGenerator');
    const settings = {
      llmEndpoint: config.get<string>('llmEndpoint', 'http://localhost:11434/api/chat'),
      llmModel: config.get<string>('llmModel', 'codellama:7b'),
      llmTimeout: config.get<number>('llmTimeout', 120),
      documentationTemplate: config.get<string>('documentationTemplate', 'standard')
    };

    this._view.webview.postMessage({
      type: 'settingsUpdate',
      settings: settings
    });
  }

  private _getHtmlForWebview(webview: vscode.Webview) {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Code Doc Generator</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      color: var(--vscode-foreground);
      background-color: var(--vscode-sideBar-background);
      padding: 16px;
    }

    h2 {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 16px;
      color: var(--vscode-foreground);
    }

    h3 {
      font-size: 13px;
      font-weight: 600;
      margin-top: 20px;
      margin-bottom: 12px;
      color: var(--vscode-foreground);
    }

    .section {
      margin-bottom: 24px;
    }

    .button {
      width: 100%;
      padding: 10px 16px;
      margin-bottom: 8px;
      background-color: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      border-radius: 2px;
      cursor: pointer;
      font-size: 13px;
      font-family: var(--vscode-font-family);
      text-align: left;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: background-color 0.2s;
    }

    .button:hover {
      background-color: var(--vscode-button-hoverBackground);
    }

    .button:active {
      transform: translateY(1px);
    }

    .button-icon {
      font-size: 16px;
    }

    .setting-group {
      margin-bottom: 16px;
    }

    .setting-label {
      display: block;
      font-size: 12px;
      font-weight: 500;
      margin-bottom: 6px;
      color: var(--vscode-foreground);
    }

    .setting-description {
      display: block;
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
      margin-bottom: 6px;
    }

    input[type="text"],
    input[type="number"],
    select {
      width: 100%;
      padding: 6px 8px;
      background-color: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-input-border);
      border-radius: 2px;
      font-size: 13px;
      font-family: var(--vscode-font-family);
    }

    input:focus,
    select:focus {
      outline: 1px solid var(--vscode-focusBorder);
      outline-offset: -1px;
    }

    .divider {
      height: 1px;
      background-color: var(--vscode-panel-border);
      margin: 20px 0;
    }

    .template-option {
      padding: 8px;
      margin-bottom: 4px;
      border: 1px solid var(--vscode-panel-border);
      border-radius: 2px;
      cursor: pointer;
      transition: background-color 0.2s;
    }

    .template-option:hover {
      background-color: var(--vscode-list-hoverBackground);
    }

    .template-option.selected {
      background-color: var(--vscode-list-activeSelectionBackground);
      border-color: var(--vscode-focusBorder);
    }

    .template-title {
      font-weight: 600;
      font-size: 12px;
      margin-bottom: 4px;
    }

    .template-desc {
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
    }

    .info-box {
      padding: 12px;
      background-color: var(--vscode-textBlockQuote-background);
      border-left: 3px solid var(--vscode-textLink-foreground);
      border-radius: 2px;
      font-size: 12px;
      margin-bottom: 16px;
    }

    .status {
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
      margin-top: 8px;
      padding: 8px;
      background-color: var(--vscode-textBlockQuote-background);
      border-radius: 2px;
    }
  </style>
</head>
<body>
  <div class="section">
    <h2>📝 AI Code Doc Generator</h2>
    <div class="info-box">
      Generate AI-powered documentation for your codebase
    </div>
  </div>

  <div class="section">
    <h3>🚀 Quick Actions</h3>
    <button class="button" onclick="generateWorkspace()">
      <span class="button-icon">📚</span>
      <span>Generate Workspace Docs</span>
    </button>
    <button class="button" onclick="generateCurrentFile()">
      <span class="button-icon">📄</span>
      <span>Generate Current File Docs</span>
    </button>
    <button class="button" onclick="addDocstrings()">
      <span class="button-icon">✨</span>
      <span>Add AI Docstrings</span>
    </button>
  </div>

  <div class="divider"></div>

  <div class="section">
    <h3>⚙️ Settings</h3>
    
    <div class="setting-group">
      <label class="setting-label">LLM Model</label>
      <span class="setting-description">Choose the AI model for documentation</span>
      <select id="llmModel" onchange="updateSetting('llmModel', this.value)">
        <option value="codellama:7b">CodeLlama 7B (Recommended)</option>
        <option value="llama2:7b">Llama2 7B</option>
        <option value="llama2:13b">Llama2 13B</option>
        <option value="codellama:13b">CodeLlama 13B</option>
      </select>
    </div>

    <div class="setting-group">
      <label class="setting-label">Timeout (seconds)</label>
      <span class="setting-description">Maximum time to wait for LLM response</span>
      <input type="number" id="llmTimeout" min="30" max="300" step="10" 
             onchange="updateSetting('llmTimeout', parseInt(this.value))">
    </div>

    <div class="setting-group">
      <label class="setting-label">LLM Endpoint</label>
      <span class="setting-description">Ollama API endpoint URL</span>
      <input type="text" id="llmEndpoint" 
             onchange="updateSetting('llmEndpoint', this.value)">
    </div>
  </div>

  <div class="divider"></div>

  <div class="section">
    <h3>🎨 Documentation Template</h3>
    <span class="setting-description" style="display: block; margin-bottom: 12px;">
      Choose the style of generated documentation
    </span>
    
    <div class="template-option" data-template="standard" onclick="selectTemplate('standard')">
      <div class="template-title">📋 Standard</div>
      <div class="template-desc">Comprehensive with all details</div>
    </div>
    
    <div class="template-option" data-template="minimal" onclick="selectTemplate('minimal')">
      <div class="template-title">📝 Minimal</div>
      <div class="template-desc">Brief overview only</div>
    </div>
    
    <div class="template-option" data-template="api" onclick="selectTemplate('api')">
      <div class="template-title">🔧 API Reference</div>
      <div class="template-desc">Function signatures & parameters</div>
    </div>
    
    <div class="template-option" data-template="tutorial" onclick="selectTemplate('tutorial')">
      <div class="template-title">📖 Tutorial</div>
      <div class="template-desc">Explanatory for learning</div>
    </div>
  </div>

  <div class="status" id="status">
    Ready to generate documentation
  </div>

  <script>
    const vscode = acquireVsCodeApi();
    let currentSettings = {};

    // Request initial settings
    vscode.postMessage({ type: 'requestSettings' });

    // Listen for settings updates from extension
    window.addEventListener('message', event => {
      const message = event.data;
      if (message.type === 'settingsUpdate') {
        currentSettings = message.settings;
        updateUI();
      }
    });

    function updateUI() {
      // Update form fields
      document.getElementById('llmModel').value = currentSettings.llmModel || 'codellama:7b';
      document.getElementById('llmTimeout').value = currentSettings.llmTimeout || 120;
      document.getElementById('llmEndpoint').value = currentSettings.llmEndpoint || 'http://localhost:11434/api/chat';
      
      // Update template selection
      const template = currentSettings.documentationTemplate || 'standard';
      document.querySelectorAll('.template-option').forEach(el => {
        el.classList.remove('selected');
        if (el.dataset.template === template) {
          el.classList.add('selected');
        }
      });
    }

    function generateWorkspace() {
      vscode.postMessage({ type: 'generateWorkspace' });
      updateStatus('Generating workspace documentation...');
    }

    function generateCurrentFile() {
      vscode.postMessage({ type: 'generateCurrentFile' });
      updateStatus('Generating current file documentation...');
    }

    function addDocstrings() {
      vscode.postMessage({ type: 'addDocstrings' });
      updateStatus('Adding AI docstrings...');
    }

    function updateSetting(setting, value) {
      vscode.postMessage({ 
        type: 'updateSetting', 
        setting: setting, 
        value: value 
      });
      updateStatus(\`Updated: \${setting}\`);
    }

    function selectTemplate(template) {
      updateSetting('documentationTemplate', template);
      
      // Update UI immediately for better UX
      document.querySelectorAll('.template-option').forEach(el => {
        el.classList.remove('selected');
        if (el.dataset.template === template) {
          el.classList.add('selected');
        }
      });
    }

    function updateStatus(message) {
      const status = document.getElementById('status');
      status.textContent = message;
      setTimeout(() => {
        status.textContent = 'Ready to generate documentation';
      }, 3000);
    }
  </script>
</body>
</html>`;
  }
}
