# AI-Enhanced Code Documentation Generator

A powerful VS Code extension that automatically generates comprehensive Markdown documentation for your codebase using static analysis and a locally hosted LLM (Large Language Model).

## Overview

This project consists of two main components:

1. **VS Code Extension** (`extension/`): TypeScript-based extension providing the user interface and workspace integration
2. **Python Analysis Engine** (`analysis_engine/`): Python-based static code analyzer and documentation generator

## Features

### Core Features
- 🔍 **Automatic Discovery**: Recursively scans workspace for Python, JavaScript, and Java files
- 🚫 **Ignore Patterns**: Supports `.docignore.txt` for excluding files (gitignore-style syntax)
- 🔒 **Safe Analysis**: Uses only static analysis - never executes your code
- 🤖 **AI Enhancement**: Leverages local LLM (Ollama) to generate clear, readable documentation
- 📝 **Markdown Output**: Generates well-structured documentation with table of contents
- ⚡ **Error Resilient**: Continues processing even if individual files fail
- 🎯 **Multi-Language**: Supports Python (AST), JavaScript (regex), and Java (regex)

### New Features (v0.2.0)
- 📄 **Single File Documentation**: Generate documentation for the currently open file only
- ✨ **AI Docstring Injection**: Add AI-generated docstrings directly to your source code
- 💾 **Automatic Backups**: Creates backup files before modifying source code
- 🎨 **Smart Formatting**: Language-aware docstring formatting (Python `"""`, JS/Java `/** */`)

## Quick Start

### Prerequisites

- VS Code 1.80.0 or higher
- Node.js 16+ and npm
- Python 3.8 or higher
- **Ollama** with a code model installed (recommended: `codellama:7b` or `llama2:7b`)
  - Install Ollama: https://ollama.ai/
  - Pull a model: `ollama pull codellama:7b`
  - Start Ollama: It runs automatically on `http://localhost:11434`

### Installation

1. **Install Extension Dependencies**:
   ```bash
   cd extension
   npm install
   npm run compile
   ```

2. **Install Python Engine**:
   ```bash
   cd ../analysis_engine
   pip install -r requirements.txt
   ```

3. **Run Tests** (optional):
   ```bash
   # Extension tests
   cd extension
   npm test
   
   # Python tests
   cd ../analysis_engine
   pytest
   ```

### Usage

#### 1. Generate Workspace Documentation
1. Open your project workspace in VS Code
2. (Optional) Create `.docignore.txt` in workspace root:
   ```
   node_modules/
   *.test.js
   build/
   dist/
   __pycache__/
   ```
3. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
4. Run: **Generate Code Documentation**
5. View the generated `DOCUMENTATION.md` in your workspace root

#### 2. Generate Single File Documentation
1. Open any Python, JavaScript, or Java file
2. Open Command Palette (Ctrl+Shift+P)
3. Run: **Generate Documentation for Current File**
4. View the generated `<filename>_DOCUMENTATION.md` in the same directory

#### 3. Add AI Docstrings to File
1. Open any Python, JavaScript, or Java file
2. Save the file (if unsaved)
3. Open Command Palette (Ctrl+Shift+P)
4. Run: **Add AI Docstrings to Current File**
5. Confirm the action
6. AI-generated docstrings will be added to your code
7. A backup file (`<filename>.backup`) is automatically created

## Configuration

Configure in VS Code settings (File → Preferences → Settings):

```json
{
  "aiCodeDocGenerator.llmEndpoint": "http://localhost:11434/api/chat",
  "aiCodeDocGenerator.llmTimeout": 120,
  "aiCodeDocGenerator.llmModel": "codellama:7b"
}
```

### Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `llmEndpoint` | `http://localhost:11434/api/chat` | Ollama API endpoint |
| `llmTimeout` | `120` | Request timeout in seconds |
| `llmModel` | `codellama:7b` | LLM model name |

### Recommended Models

- **codellama:7b** - Best for code documentation (6GB VRAM)
- **llama2:7b** - Good general-purpose model (6GB VRAM)
- **llama2:13b** - Better quality, slower (8GB VRAM)

## Project Structure

```
.
├── extension/                    # VS Code extension (TypeScript)
│   ├── src/
│   │   ├── extension.ts         # Extension entry point
│   │   ├── commands.ts          # Command handlers
│   │   ├── fileScanner.ts       # Workspace file scanner
│   │   ├── ignoreParser.ts      # .docignore parser
│   │   ├── pythonBridge.ts      # Python process manager
│   │   └── types.ts             # TypeScript types
│   ├── package.json             # Extension manifest
│   ├── tsconfig.json            # TypeScript configuration
│   └── jest.config.js           # Jest test configuration
│
├── analysis_engine/             # Python analysis engine
│   ├── parsers/
│   │   ├── python_parser.py    # Python AST parser
│   │   ├── javascript_parser.py # JavaScript regex parser
│   │   └── java_parser.py      # Java regex parser
│   ├── tests/                   # Python tests
│   ├── models.py                # Data structures
│   ├── llm_client.py            # LLM integration
│   ├── markdown_generator.py    # Documentation generation
│   ├── docstring_generator.py   # Docstring injection (NEW)
│   ├── main.py                  # Entry point
│   └── requirements.txt         # Python dependencies
│
├── test_workspace/              # Example workspace for testing
└── README.md                    # This file
```

## Development

### Extension Development

```bash
cd extension
npm run compile    # Compile TypeScript
npm run watch      # Watch mode for development
npm test           # Run tests
```

Press **F5** in VS Code to launch the Extension Development Host.

### Python Engine Development

```bash
cd analysis_engine
pytest                    # Run all tests
pytest -m unit           # Run unit tests only
pytest -m property       # Run property-based tests only
pytest --cov=.           # Run with coverage
```

## Architecture

### Communication Flow

```
User → VS Code Extension → Python Process (stdin/stdout) → Ollama API
                ↓                    ↓
         Progress UI          File Analysis
                                     ↓
                              DOCUMENTATION.md
```

### Modes of Operation

1. **Workspace Mode** (default): Generates documentation for all files in workspace
2. **Single File Mode**: Generates documentation for one file only
3. **Add Docstrings Mode**: Modifies source code to add AI-generated docstrings

### Key Design Principles

- **Safety First**: No code execution, only static analysis
- **Error Resilience**: Individual file failures don't stop the process
- **Graceful Degradation**: Works without LLM (basic documentation)
- **Sequential Processing**: One file at a time to limit memory usage
- **Progress Transparency**: Real-time progress updates for large codebases
- **Backup Protection**: Always creates backups before modifying source files

## Testing Strategy

The project uses both unit tests and property-based tests:

- **Unit Tests**: Validate specific examples and edge cases
- **Property Tests**: Verify universal correctness properties across randomized inputs

Coverage goals:
- Extension: >80% code coverage
- Python Engine: >85% code coverage

## Hardware Requirements

### Minimum
- CPU: Dual-core processor
- RAM: 8GB
- GPU: Not required (CPU-only mode works)

### Recommended
- CPU: Quad-core processor (Ryzen 5 / Intel i5 or better)
- RAM: 16GB
- GPU: 6GB VRAM (for codellama:7b or llama2:7b)

## Troubleshooting

### LLM Timeout Errors
- Increase timeout: `"aiCodeDocGenerator.llmTimeout": 180`
- Use a smaller model: `"aiCodeDocGenerator.llmModel": "codellama:7b"`
- Check Ollama is running: `ollama list`

### Python Not Found
- Install Python 3.8+: https://www.python.org/downloads/
- Ensure Python is in PATH
- Restart VS Code after installation

### Indentation Errors (Python)
- Ensure your source file has consistent indentation before adding docstrings
- Check the backup file (`.backup`) if issues occur
- The extension preserves your original indentation style

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT

## Changelog

### v0.2.0 (Latest)
- ✨ Added single file documentation generation
- ✨ Added AI docstring injection feature
- 🐛 Fixed indentation issues in Python docstrings
- 🐛 Fixed multi-line comment formatting
- 🔧 Changed default model to `codellama:7b`
- 🔧 Increased default timeout to 120 seconds
- 🔧 Fixed default endpoint to `http://localhost:11434`

### v0.1.0
- 🎉 Initial release
- 📝 Workspace documentation generation
- 🤖 LLM integration with Ollama
- 🚫 .docignore support
- 🎯 Multi-language support (Python, JavaScript, Java)

## Support

For issues, questions, or contributions, please visit the project repository.
