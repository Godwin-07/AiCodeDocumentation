# AI Code Documentation Generator - Analysis Engine

Python-based static code analysis engine that extracts metadata from source files and generates comprehensive Markdown documentation using AI enhancement.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
  - [Component Overview](#component-overview)
  - [Data Flow](#data-flow)
  - [Module Structure](#module-structure)
- [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Development Setup](#development-setup)
- [Usage](#usage)
  - [Command Line Interface](#command-line-interface)
  - [Input Format](#input-format)
  - [Output Format](#output-format)
- [Testing](#testing)
  - [Running Tests](#running-tests)
  - [Test Organization](#test-organization)
  - [Writing Tests](#writing-tests)
- [Extending the System](#extending-the-system)
  - [Adding a New Language Parser](#adding-a-new-language-parser)
  - [Customizing Markdown Output](#customizing-markdown-output)
  - [Modifying LLM Integration](#modifying-llm-integration)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Safety Guarantees](#safety-guarantees)
- [Performance Considerations](#performance-considerations)
- [Troubleshooting](#troubleshooting)

## Overview

The Analysis Engine is the core component of the AI-Enhanced Code Documentation Generator. It performs static code analysis on Python, JavaScript, and Java source files, extracts structural metadata (classes, functions, parameters, docstrings), enhances the metadata with AI-generated descriptions using a local LLM, and generates well-structured Markdown documentation.

The engine is designed to be invoked by the VS Code extension via a stdin/stdout JSON interface, making it language-agnostic and easy to integrate with other tools.

## Features

- **Multi-Language Support**: Parses Python (AST-based), JavaScript (regex-based), and Java (regex-based)
- **Static Analysis Only**: Never executes user code - safe for untrusted codebases
- **LLM Integration**: Enhances documentation with AI-generated descriptions via local LLM API
- **Fallback Mode**: Generates basic documentation if LLM is unavailable or fails
- **Error Resilience**: Continues processing even if individual files fail to parse
- **Sequential Processing**: Processes files one at a time to limit memory usage
- **Progress Reporting**: Emits progress updates for large workspaces (>100 files)
- **Comprehensive Testing**: Unit tests and property-based tests for correctness

## Architecture

### Component Overview

The analysis engine follows a modular pipeline architecture:

```
┌─────────────┐
│   main.py   │  Entry point - stdin/stdout JSON interface
└──────┬──────┘
       │
       ├──> ┌──────────────┐
       │    │   parsers/   │  Language-specific static analysis
       │    └──────┬───────┘
       │           ├─ python_parser.py (AST-based)
       │           ├─ javascript_parser.py (regex-based)
       │           └─ java_parser.py (regex-based)
       │
       ├──> ┌──────────────────┐
       │    │  llm_client.py   │  LLM API communication
       │    └──────────────────┘
       │
       └──> ┌─────────────────────────┐
            │ markdown_generator.py   │  Markdown document generation
            └─────────────────────────┘
```

### Data Flow

```
stdin (JSON) → main.py → File Loop → Parser (by extension)
                                          ↓
                                    FileMetadata
                                          ↓
                                    llm_client
                                          ↓
                                  Enhanced Metadata
                                          ↓
                                 markdown_generator
                                          ↓
                              ┌───────────┴───────────┐
                              ↓                       ↓
                      DOCUMENTATION.md          stdout (JSON)
```

### Module Structure

```
analysis_engine/
├── main.py                    # Entry point, orchestrates the pipeline
├── models.py                  # Data structures (Parameter, FunctionMetadata, etc.)
├── llm_client.py              # LLM API communication with fallback
├── markdown_generator.py      # Markdown document generation
├── parsers/
│   ├── __init__.py
│   ├── python_parser.py       # AST-based Python parsing
│   ├── javascript_parser.py   # Regex-based JavaScript parsing
│   └── java_parser.py         # Regex-based Java parsing
├── tests/
│   ├── test_main.py           # Main entry point tests
│   ├── test_main_integration.py  # Integration tests
│   ├── test_python_parser.py  # Python parser tests
│   ├── test_javascript_parser.py  # JavaScript parser tests
│   ├── test_java_parser.py    # Java parser tests
│   ├── test_llm_client.py     # LLM client tests
│   ├── test_markdown_generator.py  # Markdown generator tests
│   ├── test_markdown_integration.py  # Markdown integration tests
│   ├── test_models.py         # Data model tests
│   ├── test_file_error_handling.py  # Error handling tests
│   └── sample_*.{py,js,java}  # Test fixtures
├── requirements.txt           # Python dependencies
├── setup.py                   # Package configuration
├── pytest.ini                 # Pytest configuration
└── README.md                  # This file
```

## Installation

### Quick Start

Install the required dependencies:

```bash
cd analysis_engine
pip install -r requirements.txt
```

### Development Setup

For development with testing and code quality tools:

```bash
pip install -e ".[dev]"
```

This installs:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `hypothesis` - Property-based testing
- `black` - Code formatting
- `mypy` - Type checking

**Requirements:**
- Python 3.8 or higher
- pip package manager

## Usage

### Command Line Interface

The engine is designed to be invoked via stdin/stdout JSON interface:

```bash
python main.py < input.json > output.json
```

Or using echo:

```bash
echo '{"workspacePath": "/path/to/workspace", "files": ["file1.py", "file2.js"], "llmEndpoint": "https://localhosted:11434/api/chat", "llmTimeout": 30, "llmModel": "llama2"}' | python main.py
```

### Input Format

The engine expects a JSON object on stdin with the following structure:

```json
{
  "workspacePath": "/absolute/path/to/workspace",
  "files": [
    "/absolute/path/to/file1.py",
    "/absolute/path/to/file2.js",
    "/absolute/path/to/file3.java"
  ],
  "llmEndpoint": "https://localhosted:11434/api/chat",
  "llmTimeout": 30,
  "llmModel": "llama2"
}
```

**Fields:**
- `workspacePath` (string, required): Absolute path to the workspace root directory
- `files` (array, required): List of absolute paths to source files to analyze
- `llmEndpoint` (string, required): URL of the local LLM API endpoint
- `llmTimeout` (number, optional): Timeout in seconds for LLM requests (default: 30)
- `llmModel` (string, optional): LLM model name to use (default: "llama2")

### Output Format

The engine outputs a JSON object to stdout with the following structure:

```json
{
  "success": true,
  "documentationPath": "/absolute/path/to/DOCUMENTATION.md",
  "filesProcessed": 3,
  "filesSkipped": 0,
  "errors": []
}
```

**Fields:**
- `success` (boolean): Whether documentation generation completed successfully
- `documentationPath` (string): Absolute path to the generated DOCUMENTATION.md file
- `filesProcessed` (number): Number of files successfully processed
- `filesSkipped` (number): Number of files skipped due to errors
- `errors` (array): List of error messages encountered during processing

**Progress Updates:**

For workspaces with more than 100 files, the engine emits progress updates to stdout as separate JSON objects:

```json
{"type": "progress", "filesProcessed": 10, "totalFiles": 150}
{"type": "progress", "filesProcessed": 20, "totalFiles": 150}
...
```

## Testing

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage report:
```bash
pytest --cov=. --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

Run only unit tests:
```bash
pytest -m unit
```

Run only property-based tests:
```bash
pytest -m property
```

Run tests for a specific module:
```bash
pytest tests/test_python_parser.py
```

Run tests with verbose output:
```bash
pytest -v
```

### Test Organization

Tests are organized by module and type:

- **Unit Tests**: Test specific functions and edge cases
  - `test_python_parser.py` - Python AST parsing
  - `test_javascript_parser.py` - JavaScript regex parsing
  - `test_java_parser.py` - Java regex parsing
  - `test_llm_client.py` - LLM API communication
  - `test_markdown_generator.py` - Markdown generation
  - `test_models.py` - Data model validation
  - `test_file_error_handling.py` - Error handling scenarios

- **Integration Tests**: Test component interactions
  - `test_main_integration.py` - End-to-end pipeline tests
  - `test_markdown_integration.py` - Markdown generation with real data

- **Property-Based Tests**: Verify universal properties
  - Embedded in unit test files with `@given` decorators
  - Use Hypothesis library for randomized input generation

### Writing Tests

**Unit Test Example:**

```python
def test_parse_python_function():
    """Test parsing a simple Python function"""
    source = '''
def greet(name: str, greeting: str = "Hello") -> str:
    """Greet someone"""
    return f"{greeting}, {name}!"
'''
    metadata = parse_python_file_from_source(source)
    
    assert len(metadata.functions) == 1
    func = metadata.functions[0]
    assert func.name == "greet"
    assert len(func.parameters) == 2
    assert func.parameters[0].name == "name"
    assert func.parameters[1].default_value == '"Hello"'
    assert func.docstring == "Greet someone"
```

**Property-Based Test Example:**

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
def test_function_name_extraction(function_name):
    """Property: Any valid function name should be extractable"""
    source = f"def {function_name}(): pass"
    metadata = parse_python_file_from_source(source)
    assert len(metadata.functions) == 1
    assert metadata.functions[0].name == function_name
```

## Extending the System

### Adding a New Language Parser

To add support for a new programming language:

**1. Create a new parser module:**

```bash
touch parsers/ruby_parser.py
```

**2. Implement the parser function:**

```python
# parsers/ruby_parser.py
from models import FileMetadata, ClassMetadata, FunctionMetadata, Parameter
import re

def parse_ruby_file(file_path: str) -> FileMetadata:
    """
    Parse a Ruby source file and extract metadata.
    
    Args:
        file_path: Absolute path to the Ruby file
        
    Returns:
        FileMetadata object with extracted classes, methods, and functions
    """
    metadata = FileMetadata(
        file_path=file_path,
        language='ruby',
        classes=[],
        functions=[],
        parse_errors=[]
    )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract classes
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            # Extract methods, docstrings, etc.
            # ...
            
        # Extract module-level methods
        method_pattern = r'def\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(method_pattern, content):
            method_name = match.group(1)
            params_str = match.group(2)
            # Parse parameters
            # ...
            
    except Exception as e:
        metadata.parse_errors.append(f"Error parsing Ruby file: {str(e)}")
    
    return metadata
```

**3. Register the parser in `parsers/__init__.py`:**

```python
from .python_parser import parse_python_file
from .javascript_parser import parse_javascript_file
from .java_parser import parse_java_file
from .ruby_parser import parse_ruby_file  # Add this

__all__ = [
    'parse_python_file',
    'parse_javascript_parser',
    'parse_java_file',
    'parse_ruby_file',  # Add this
]
```

**4. Update `main.py` to dispatch to the new parser:**

```python
def parse_file(file_path: str) -> FileMetadata:
    """Dispatch to appropriate parser based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.py':
        return parse_python_file(file_path)
    elif ext == '.js':
        return parse_javascript_file(file_path)
    elif ext == '.java':
        return parse_java_file(file_path)
    elif ext == '.rb':  # Add this
        return parse_ruby_file(file_path)
    else:
        # Return empty metadata for unsupported files
        return FileMetadata(file_path=file_path, language='unknown')
```

**5. Write tests:**

```python
# tests/test_ruby_parser.py
import pytest
from parsers.ruby_parser import parse_ruby_file

def test_parse_ruby_class():
    """Test parsing a Ruby class"""
    # Create test file
    # Test parsing
    # Assert results
    pass

def test_parse_ruby_method():
    """Test parsing a Ruby method"""
    pass
```

**6. Update the VS Code extension:**

Update `extension/src/fileScanner.ts` to include `.rb` files in the scan:

```typescript
const SUPPORTED_EXTENSIONS = ['.py', '.js', '.java', '.rb'];
```

### Customizing Markdown Output

To customize the generated Markdown format, modify `markdown_generator.py`:

**Example: Add a "Dependencies" section:**

```python
def generate_markdown(all_metadata: List[FileMetadata], workspace_path: str) -> str:
    """Generate Markdown documentation from metadata"""
    sections = []
    
    # Title and timestamp
    sections.append("# Project Documentation\n")
    sections.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # Table of contents
    sections.append("## Table of Contents\n")
    # ...
    
    # NEW: Add dependencies section
    sections.append("## Dependencies\n")
    dependencies = extract_dependencies(all_metadata)
    for dep in dependencies:
        sections.append(f"- {dep}\n")
    sections.append("\n")
    
    # Files section
    sections.append("## Files\n")
    # ...
    
    return "\n".join(sections)

def extract_dependencies(all_metadata: List[FileMetadata]) -> List[str]:
    """Extract import/require statements from metadata"""
    dependencies = set()
    for metadata in all_metadata:
        # Parse imports from docstrings or add to metadata extraction
        pass
    return sorted(dependencies)
```

### Modifying LLM Integration

To customize LLM behavior, modify `llm_client.py`:

**Example: Use a different prompt template:**

```python
def send_to_llm(metadata: FileMetadata, endpoint: str, timeout: int, model: str) -> str:
    """Send metadata to LLM and get enhanced documentation"""
    
    # Custom prompt template
    prompt = f"""
You are a technical documentation expert. Generate clear, concise documentation
for the following code structure. Focus on:
1. Purpose and responsibility
2. Key parameters and return values
3. Usage examples
4. Edge cases and limitations

Code Structure:
{json.dumps(metadata_to_dict(metadata), indent=2)}

Generate documentation in Markdown format.
"""
    
    # Rest of the implementation...
```

**Example: Add retry logic:**

```python
import time

def send_to_llm_with_retry(metadata: FileMetadata, endpoint: str, timeout: int, model: str, max_retries: int = 3) -> str:
    """Send to LLM with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return send_to_llm(metadata, endpoint, timeout, model)
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"LLM request failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"LLM request failed after {max_retries} attempts, using fallback")
                return generate_basic_documentation(metadata)
```

## Data Models

The engine uses dataclasses to represent extracted metadata:

### Parameter

```python
@dataclass
class Parameter:
    name: str                      # Parameter name
    type_hint: Optional[str]       # Type annotation (Python only)
    default_value: Optional[str]   # Default value if present
```

### FunctionMetadata

```python
@dataclass
class FunctionMetadata:
    name: str                      # Function/method name
    parameters: List[Parameter]    # List of parameters
    return_type: Optional[str]     # Return type annotation (Python only)
    docstring: Optional[str]       # Docstring or comment block
    line_number: int               # Line number in source file
```

### ClassMetadata

```python
@dataclass
class ClassMetadata:
    name: str                      # Class name
    docstring: Optional[str]       # Class docstring or comment
    methods: List[FunctionMetadata]  # List of methods
    line_number: int               # Line number in source file
```

### FileMetadata

```python
@dataclass
class FileMetadata:
    file_path: str                 # Absolute path to source file
    language: str                  # 'python', 'javascript', 'java'
    classes: List[ClassMetadata]   # Extracted classes
    functions: List[FunctionMetadata]  # Module-level functions
    parse_errors: List[str]        # Errors encountered during parsing
```

## Error Handling

The engine handles errors gracefully to ensure resilience:

### File Read Errors

```python
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except PermissionError:
    metadata.parse_errors.append(f"Permission denied: {file_path}")
    return metadata
except UnicodeDecodeError:
    metadata.parse_errors.append(f"Encoding error: {file_path}")
    return metadata
```

**Behavior:** Error is logged, file is skipped, processing continues

### Parse Errors

```python
try:
    tree = ast.parse(content)
except SyntaxError as e:
    metadata.parse_errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
    return metadata
```

**Behavior:** Error is logged with line number, file is skipped, processing continues

### LLM Errors

```python
try:
    response = requests.post(endpoint, json=payload, timeout=timeout)
    response.raise_for_status()
except requests.exceptions.Timeout:
    return generate_basic_documentation(metadata)
except requests.exceptions.RequestException as e:
    return generate_basic_documentation(metadata)
```

**Behavior:** Falls back to basic documentation without LLM enhancement, processing continues

### Write Errors

```python
try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
except PermissionError:
    return {"success": False, "errors": ["Permission denied writing DOCUMENTATION.md"]}
except IOError as e:
    return {"success": False, "errors": [f"IO error: {str(e)}"]}
```

**Behavior:** Error is reported to extension via JSON output, processing stops

## Safety Guarantees

The analysis engine is designed to be safe for use on untrusted codebases:

✅ **Static Analysis Only**
- Python: Uses `ast` module (Abstract Syntax Tree parsing)
- JavaScript/Java: Uses regex pattern matching
- Never executes any user code

✅ **No Dynamic Execution**
- Never calls `eval()` or `exec()`
- Never uses `compile()` or `__import__()`
- Never invokes interpreters or runtimes

✅ **No Code Imports**
- Never imports modules from analyzed codebases
- Only imports standard library and declared dependencies
- Isolated from user code execution

✅ **Read-Only Operations**
- Only reads source files for analysis
- Never modifies source files
- Only creates/updates DOCUMENTATION.md

✅ **Resource Limits**
- Processes files sequentially (one at a time)
- Limits memory usage by releasing resources after each file
- Implements timeouts for LLM requests (default: 30s)

## Performance Considerations

### Memory Usage

- **Sequential Processing**: Files are processed one at a time to limit memory usage
- **Resource Cleanup**: Metadata objects are released after Markdown generation
- **Streaming Output**: Progress updates are emitted incrementally

### Processing Time

Typical processing times (on modern hardware):

- **Python files**: ~50-100ms per file (AST parsing)
- **JavaScript/Java files**: ~20-50ms per file (regex parsing)
- **LLM enhancement**: ~1-5s per file (depends on LLM response time)

For a workspace with 50 files:
- Without LLM: ~5-10 seconds
- With LLM: ~1-5 minutes (depends on LLM performance)

### Optimization Tips

1. **Disable LLM for large workspaces**: Set a very short timeout to force fallback mode
2. **Filter files**: Use `.docignore.txt` to exclude unnecessary files
3. **Use faster LLM models**: Smaller models respond faster but may produce lower quality docs
4. **Batch processing**: The engine processes files sequentially, but you can run multiple instances in parallel for different directories

## Troubleshooting

### Common Issues

**Issue: "Python not found in PATH"**
- **Solution**: Ensure Python 3.8+ is installed and in your system PATH
- **Check**: Run `python --version` or `python3 --version`

**Issue: "Module not found" errors**
- **Solution**: Install dependencies with `pip install -r requirements.txt`
- **Check**: Run `pip list` to verify installed packages

**Issue: "LLM connection timeout"**
- **Solution**: Verify LLM service is running at the specified endpoint
- **Check**: Run `curl -X POST https://localhosted:11434/api/chat` to test connectivity
- **Fallback**: The engine will automatically use basic documentation if LLM is unavailable

**Issue: "Permission denied" when writing DOCUMENTATION.md**
- **Solution**: Ensure write permissions for the workspace directory
- **Check**: Run `ls -la` (Unix) or `icacls` (Windows) to verify permissions

**Issue: "Syntax error" when parsing files**
- **Solution**: This is expected for files with syntax errors - they will be skipped
- **Check**: Review the `errors` array in the JSON output for details

**Issue: Tests fail with "hypothesis" errors**
- **Solution**: Install hypothesis with `pip install hypothesis`
- **Check**: Run `pip show hypothesis` to verify installation

### Debug Mode

Enable verbose logging by setting the `DEBUG` environment variable:

```bash
DEBUG=1 python main.py < input.json
```

This will print detailed information about:
- File parsing progress
- LLM requests and responses
- Error stack traces
- Timing information

### Getting Help

- **Issues**: Report bugs at the project's GitHub repository
- **Documentation**: See the main project README.md in the root directory
- **Tests**: Review test files in `tests/` for usage examples

## License

MIT License - See LICENSE file for details
