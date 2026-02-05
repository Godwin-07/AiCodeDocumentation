# AI Code Documentation Generator

Automatically generate comprehensive, structured Markdown documentation for your source code using static analysis and a locally hosted Large Language Model (LLM).

## Features

- **Multi-Language Support**: Analyzes Python, JavaScript, and Java source files
- **Static Analysis**: Extracts code structure without executing your code
- **AI-Enhanced Documentation**: Uses a local LLM to generate clear, human-readable explanations
- **Flexible Ignore Patterns**: Exclude files and folders using `.docignore.txt` (gitignore-style syntax)
- **Safe and Secure**: Never executes your code or modifies source files
- **Progress Tracking**: Real-time progress updates for large codebases
- **Error Resilient**: Continues processing even if individual files fail

## Installation

### Prerequisites

1. **VS Code**: Version 1.80.0 or higher
2. **Python 3**: Python 3.8 or higher must be installed and available in your PATH
3. **Local LLM**: A locally hosted LLM service (e.g., Ollama) running at `https://localhosted:11434/api/chat`

### Installing the Extension

1. Download the `.vsix` file from the releases page
2. Open VS Code
3. Go to Extensions view (`Ctrl+Shift+X` or `Cmd+Shift+X`)
4. Click the `...` menu at the top of the Extensions view
5. Select "Install from VSIX..."
6. Choose the downloaded `.vsix` file

Alternatively, install from the VS Code Marketplace:
1. Open VS Code
2. Go to Extensions view
3. Search for "AI Code Documentation Generator"
4. Click Install

### Setting Up Python Dependencies

The extension requires Python dependencies for the analysis engine. Install them using:

```bash
cd analysis_engine
pip install -r requirements.txt
```

Required Python packages:
- `requests`: For LLM API communication
- `pytest`: For running tests (development only)
- `hypothesis`: For property-based testing (development only)

### Setting Up a Local LLM

This extension requires a locally hosted LLM. We recommend using [Ollama](https://ollama.ai/):

1. Install Ollama from https://ollama.ai/
2. Pull a model: `ollama pull llama2`
3. Start the Ollama service (it runs on `http://localhost:11434` by default)
4. Configure the extension to use your LLM endpoint (see Configuration section)

## Usage

### Basic Usage

1. Open a workspace/folder in VS Code containing your source code
2. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
3. Type "Generate Code Documentation" and select the command
4. Wait for the analysis to complete (progress is shown in the notification)
5. Find the generated `DOCUMENTATION.md` file in your workspace root

### Using .docignore.txt

Create a `.docignore.txt` file in your workspace root to exclude files and folders from documentation:

```
# Ignore node_modules
node_modules/

# Ignore test files
*.test.js
*.test.py
**/*_test.java

# Ignore build outputs
build/
dist/
out/

# Ignore Python cache
__pycache__/
*.pyc

# Ignore specific files
README.md
LICENSE
```

### Workflow Example

```bash
# 1. Create a .docignore.txt file
echo "node_modules/" > .docignore.txt
echo "*.test.js" >> .docignore.txt

# 2. Open VS Code in your project
code .

# 3. Run the command (Ctrl+Shift+P)
# Type: "Generate Code Documentation"

# 4. View the generated documentation
# Open: DOCUMENTATION.md in your workspace root
```

## Configuration

Configure the extension through VS Code settings (`File > Preferences > Settings` or `Ctrl+,`):

### Available Settings

#### `aiCodeDocGenerator.llmEndpoint`
- **Type**: `string`
- **Default**: `"https://localhosted:11434/api/chat"`
- **Description**: The URL endpoint for your local LLM API

Example:
```json
{
  "aiCodeDocGenerator.llmEndpoint": "http://localhost:11434/api/chat"
}
```

#### `aiCodeDocGenerator.llmTimeout`
- **Type**: `number`
- **Default**: `30`
- **Description**: Timeout for LLM requests in seconds. If a request exceeds this time, the extension falls back to basic documentation.

Example:
```json
{
  "aiCodeDocGenerator.llmTimeout": 60
}
```

#### `aiCodeDocGenerator.llmModel`
- **Type**: `string`
- **Default**: `"llama2"`
- **Description**: The name of the LLM model to use

Example:
```json
{
  "aiCodeDocGenerator.llmModel": "llama2:13b"
}
```

### Configuration File Example

Add these settings to your `.vscode/settings.json`:

```json
{
  "aiCodeDocGenerator.llmEndpoint": "http://localhost:11434/api/chat",
  "aiCodeDocGenerator.llmTimeout": 45,
  "aiCodeDocGenerator.llmModel": "codellama"
}
```

## .docignore.txt Syntax

The `.docignore.txt` file uses gitignore-style syntax to specify which files and folders to exclude from documentation.

### Syntax Rules

| Pattern | Description | Example |
|---------|-------------|---------|
| `#` | Comment line (ignored) | `# This is a comment` |
| `filename` | Matches file anywhere in tree | `README.md` |
| `*.ext` | Glob pattern for file extension | `*.test.js` |
| `directory/` | Matches directory and all contents | `node_modules/` |
| `**/pattern` | Matches in any directory | `**/*.pyc` |
| `path/to/file` | Matches specific path | `src/generated/code.js` |

### Pattern Examples

```
# Comments start with hash
# Empty lines are ignored

# Ignore all node_modules directories
node_modules/

# Ignore all test files
*.test.js
*.test.py
*_test.java

# Ignore build outputs
build/
dist/
out/
target/

# Ignore Python cache files
__pycache__/
*.pyc
*.pyo

# Ignore specific directories
.git/
.vscode/
.idea/

# Ignore generated code
**/generated/**
src/proto/*.java

# Ignore documentation files
*.md
!IMPORTANT.md  # Note: Negation patterns are NOT supported
```

### Pattern Matching Behavior

- **Case Sensitive**: Patterns are case-sensitive on Linux/macOS, case-insensitive on Windows
- **Relative Paths**: All patterns are relative to the workspace root
- **Directory Matching**: Patterns ending with `/` match directories and all their contents
- **Glob Support**: Supports `*` (any characters) and `**` (any directories)
- **No Negation**: Unlike gitignore, negation patterns (`!pattern`) are not supported

### Common Patterns

```
# JavaScript/TypeScript projects
node_modules/
*.test.ts
*.spec.ts
dist/
build/
coverage/

# Python projects
__pycache__/
*.pyc
venv/
.venv/
*.egg-info/
dist/
build/

# Java projects
target/
*.class
.gradle/
build/

# General
.git/
.DS_Store
*.log
```

## Generated Documentation Structure

The generated `DOCUMENTATION.md` file includes:

1. **Project Overview**: AI-generated summary of your codebase
2. **Table of Contents**: Links to all documented files
3. **File-wise Documentation**: For each source file:
   - File path and language
   - Classes with methods
   - Functions with parameters
   - AI-enhanced descriptions and explanations

### Example Output

```markdown
# Project Documentation

*Generated on: 2024-01-15 10:30:00*

## Table of Contents
- [Overview](#overview)
- [Files](#files)
  - [src/utils.py](#srcutilspy)
  - [src/main.js](#srcmainjs)

## Overview

This project implements a web application with Python backend and JavaScript frontend...

## Files

### src/utils.py

**Language:** Python  
**Path:** `src/utils.py`

#### Functions

##### calculate_total(items, tax_rate=0.1)

Calculates the total cost of items including tax.

- **Parameters:**
  - `items`: List of item prices to sum
  - `tax_rate`: Tax rate to apply (default: 0.1 for 10%)
- **Returns:** Total cost including tax
- **Purpose:** Provides a utility function for calculating order totals with configurable tax rates.
```

## Troubleshooting

### Extension Not Working

**Problem**: Command doesn't appear in Command Palette

**Solution**:
- Ensure the extension is installed and enabled
- Reload VS Code window (`Ctrl+Shift+P` → "Reload Window")
- Check the Output panel (`View > Output`) for error messages

---

**Problem**: "Python 3 not found in PATH" error

**Solution**:
- Install Python 3.8 or higher from https://python.org
- Ensure Python is added to your system PATH
- Restart VS Code after installing Python
- Verify installation: Open terminal and run `python --version` or `python3 --version`

---

**Problem**: "No workspace folder open" error

**Solution**:
- Open a folder in VS Code (`File > Open Folder`)
- The extension requires a workspace to analyze

### LLM Connection Issues

**Problem**: "LLM is unreachable" warning

**Solution**:
- Verify your local LLM service is running
- Check the endpoint URL in settings matches your LLM service
- Test the endpoint: `curl http://localhost:11434/api/chat`
- The extension will generate basic documentation without LLM enhancement

---

**Problem**: LLM requests timing out

**Solution**:
- Increase the timeout in settings: `aiCodeDocGenerator.llmTimeout`
- Use a faster/smaller model
- Check your LLM service performance

### Documentation Quality Issues

**Problem**: Generated documentation is incomplete

**Solution**:
- Check the Output panel for parsing errors
- Ensure source files have valid syntax
- Files with syntax errors are skipped automatically
- Review `.docignore.txt` to ensure files aren't accidentally excluded

---

**Problem**: Documentation doesn't include certain files

**Solution**:
- Verify file extensions are supported (`.py`, `.js`, `.java`)
- Check if files are excluded by `.docignore.txt` patterns
- Ensure files are within the workspace folder

### Performance Issues

**Problem**: Documentation generation is slow

**Solution**:
- Use `.docignore.txt` to exclude unnecessary files
- Increase LLM timeout if requests are timing out
- Consider using a faster LLM model
- For large codebases (>100 files), expect 3-5 minutes

---

**Problem**: High memory usage

**Solution**:
- The extension processes files sequentially to minimize memory usage
- Close other applications if memory is constrained
- Exclude large generated files using `.docignore.txt`

## Limitations

- **Supported Languages**: Only Python, JavaScript, and Java are currently supported
- **Static Analysis Only**: The extension uses static analysis (no code execution), so dynamic behavior is not captured
- **LLM Required**: Best results require a local LLM; basic documentation is generated if LLM is unavailable
- **No Incremental Updates**: Each run regenerates the entire `DOCUMENTATION.md` file
- **Single Output File**: All documentation is written to one file (no per-file documentation)

## Privacy and Security

- **No Code Execution**: Your code is never executed, only parsed statically
- **Local Processing**: All analysis happens locally on your machine
- **Local LLM**: Uses a locally hosted LLM (no data sent to external services)
- **No File Modification**: Only creates/updates `DOCUMENTATION.md`, never modifies source files
- **Safe for Untrusted Code**: Safe to use on incomplete or untrusted codebases

## Contributing

Contributions are welcome! Please see the project repository for:
- Bug reports and feature requests
- Development setup instructions
- Contribution guidelines
- Testing requirements

## License

[Your License Here]

## Support

- **Issues**: Report bugs and request features on GitHub
- **Documentation**: Full documentation available in the repository
- **Community**: Join our discussions on GitHub

## Changelog

### Version 0.1.0
- Initial release
- Support for Python, JavaScript, and Java
- Static analysis with LLM enhancement
- .docignore.txt support
- Progress tracking for large codebases
