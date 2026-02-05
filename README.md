# AI-Enhanced Code Documentation Generator

A VS Code extension that automatically generates comprehensive Markdown documentation for your codebase using static analysis and a locally hosted LLM.

## Overview

This project consists of two main components:

1. **VS Code Extension** (`extension/`): TypeScript-based extension providing the user interface and workspace integration
2. **Python Analysis Engine** (`analysis_engine/`): Python-based static code analyzer and documentation generator

## Features

- 🔍 **Automatic Discovery**: Recursively scans workspace for Python, JavaScript, and Java files
- 🚫 **Ignore Patterns**: Supports `.docignore.txt` for excluding files (gitignore-style syntax)
- 🔒 **Safe Analysis**: Uses only static analysis - never executes your code
- 🤖 **AI Enhancement**: Leverages local LLM to generate clear, readable documentation
- 📝 **Markdown Output**: Generates well-structured `DOCUMENTATION.md` with table of contents
- ⚡ **Error Resilient**: Continues processing even if individual files fail
- 🎯 **Multi-Language**: Supports Python (AST), JavaScript (regex), and Java (regex)

## Quick Start

### Prerequisites

- VS Code 1.80.0 or higher
- Node.js 16+ and npm
- Python 3.8 or higher
- Local LLM server (e.g., Ollama) running at `https://localhosted:11434/api/chat`

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

## Configuration

Configure in VS Code settings (File → Preferences → Settings):

```json
{
  "aiCodeDocGenerator.llmEndpoint": "https://localhosted:11434/api/chat",
  "aiCodeDocGenerator.llmTimeout": 30,
  "aiCodeDocGenerator.llmModel": "llama2"
}
```

## Project Structure

```
.
├── extension/              # VS Code extension (TypeScript)
│   ├── src/               # Extension source code
│   ├── package.json       # Extension manifest
│   ├── tsconfig.json      # TypeScript configuration
│   └── jest.config.js     # Jest test configuration
│
├── analysis_engine/       # Python analysis engine
│   ├── parsers/          # Language-specific parsers
│   ├── tests/            # Python tests
│   ├── models.py         # Data structures
│   ├── llm_client.py     # LLM integration
│   ├── markdown_generator.py  # Documentation generation
│   ├── main.py           # Entry point
│   └── requirements.txt  # Python dependencies
│
└── README.md             # This file
```

## Development

### Extension Development

```bash
cd extension
npm run compile    # Compile TypeScript
npm run watch      # Watch mode for development
npm test           # Run tests
```

Press F5 in VS Code to launch the Extension Development Host.

### Python Engine Development

```bash
cd analysis_engine
pytest                    # Run all tests
pytest -m unit           # Run unit tests only
pytest -m property       # Run property-based tests only
pytest --cov=.           # Run with coverage
black .                  # Format code
mypy .                   # Type checking
```

## Architecture

### Communication Flow

```
User → VS Code Extension → Python Process (stdin/stdout) → LLM API
                ↓                    ↓
         Progress UI          File Analysis
                                     ↓
                              DOCUMENTATION.md
```

### Key Design Principles

- **Safety First**: No code execution, only static analysis
- **Error Resilience**: Individual file failures don't stop the process
- **Graceful Degradation**: Works without LLM (basic documentation)
- **Sequential Processing**: One file at a time to limit memory usage
- **Progress Transparency**: Real-time progress updates for large codebases

## Testing Strategy

The project uses both unit tests and property-based tests:

- **Unit Tests**: Validate specific examples and edge cases
- **Property Tests**: Verify universal correctness properties across randomized inputs

Coverage goals:
- Extension: >80% code coverage
- Python Engine: >85% code coverage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT

## Support

For issues, questions, or contributions, please visit the project repository.
