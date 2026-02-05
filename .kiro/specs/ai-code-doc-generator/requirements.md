# Requirements Document

## Introduction

This document specifies the requirements for an AI-Enhanced Code Documentation Generator VS Code Extension. The system automatically generates structured Markdown documentation for source code using static analysis and a locally hosted LLM. The extension operates without executing any project code and respects user-defined ignore patterns.

## Glossary

- **Extension**: The VS Code extension component that provides the user interface and workspace integration
- **Analysis_Engine**: The Python-based component that performs static code analysis
- **LLM**: Large Language Model hosted locally at https://localhosted:11434/api/chat
- **Workspace**: The VS Code workspace containing source files to be documented
- **Ignore_List**: A .docignore.txt file containing patterns for files/folders to exclude from documentation
- **Metadata**: Extracted code structure information including classes, functions, parameters, and comments
- **Documentation_File**: The generated DOCUMENTATION.md file in the project root

## Requirements

### Requirement 1: Ignore List Processing

**User Story:** As a developer, I want to define which files and folders should be excluded from documentation, so that I can avoid documenting generated code, dependencies, and irrelevant files.

#### Acceptance Criteria

1. WHEN the Extension starts documentation generation, THE Extension SHALL check for a .docignore.txt file in the workspace root
2. IF a .docignore.txt file exists, THEN THE Extension SHALL parse the ignore patterns before scanning any files
3. WHEN scanning workspace folders, THE Extension SHALL exclude any file or folder matching patterns in the Ignore_List
4. WHEN a file path matches an ignore pattern, THE Extension SHALL skip that file without attempting to read or analyze it
5. IF no .docignore.txt file exists, THEN THE Extension SHALL proceed to scan all supported source files in the workspace

### Requirement 2: Workspace Scanning

**User Story:** As a developer, I want the extension to automatically discover all relevant source files in my project, so that I don't have to manually specify which files to document.

#### Acceptance Criteria

1. WHEN the user invokes the "Generate Code Documentation" command, THE Extension SHALL recursively scan all folders in the Workspace
2. WHEN scanning folders, THE Extension SHALL identify files with extensions .py, .js, and .java
3. WHEN a supported file is found, THE Extension SHALL add it to the processing queue unless it matches the Ignore_List
4. WHILE scanning is in progress, THE Extension SHALL display a progress indicator to the user
5. WHEN scanning completes, THE Extension SHALL pass the list of discovered files to the Analysis_Engine

### Requirement 3: Python Code Analysis

**User Story:** As a developer, I want the system to extract structural information from Python files, so that accurate documentation can be generated without executing the code.

#### Acceptance Criteria

1. WHEN the Analysis_Engine receives a Python file, THE Analysis_Engine SHALL parse it using the Python ast module
2. WHEN parsing a Python file, THE Analysis_Engine SHALL extract all class names and their methods
3. WHEN parsing a Python file, THE Analysis_Engine SHALL extract all function names at module level
4. WHEN extracting functions or methods, THE Analysis_Engine SHALL capture parameter names and default values
5. WHEN a function, method, or class has a docstring, THE Analysis_Engine SHALL extract the docstring text
6. IF parsing fails due to syntax errors, THEN THE Analysis_Engine SHALL log the error and continue processing other files

### Requirement 4: JavaScript and Java Code Analysis

**User Story:** As a developer, I want the system to extract structural information from JavaScript and Java files using static analysis, so that documentation can be generated for multi-language projects.

#### Acceptance Criteria

1. WHEN the Analysis_Engine receives a JavaScript or Java file, THE Analysis_Engine SHALL parse it using regex-based pattern matching
2. WHEN parsing JavaScript files, THE Analysis_Engine SHALL extract function declarations, arrow functions, and class definitions
3. WHEN parsing Java files, THE Analysis_Engine SHALL extract class names, method signatures, and method parameters
4. WHEN extracting functions or methods from JavaScript or Java, THE Analysis_Engine SHALL capture parameter names
5. WHEN a function or method has a comment block immediately preceding it, THE Analysis_Engine SHALL extract the comment text
6. THE Analysis_Engine SHALL NOT execute any JavaScript or Java code during parsing

### Requirement 5: LLM Integration

**User Story:** As a developer, I want the system to enhance extracted code metadata with clear explanations using a local LLM, so that the generated documentation is more helpful and readable.

#### Acceptance Criteria

1. WHEN the Analysis_Engine has extracted Metadata from a file, THE Analysis_Engine SHALL format the Metadata as structured JSON
2. WHEN sending data to the LLM, THE Analysis_Engine SHALL make HTTP POST requests to https://localhosted:11434/api/chat
3. WHEN constructing LLM prompts, THE Analysis_Engine SHALL include the extracted Metadata and request Markdown-formatted explanations
4. WHEN the LLM responds, THE Analysis_Engine SHALL validate that the response contains valid Markdown content
5. IF the LLM is unreachable or returns an error, THEN THE Analysis_Engine SHALL generate basic documentation using only the extracted Metadata
6. THE Analysis_Engine SHALL NOT send any code for execution to the LLM, only structural metadata

### Requirement 6: Documentation Generation

**User Story:** As a developer, I want the system to produce a well-structured Markdown file with comprehensive documentation, so that I can easily understand and navigate my codebase.

#### Acceptance Criteria

1. WHEN all files have been analyzed, THE Analysis_Engine SHALL generate a DOCUMENTATION.md file in the Workspace root
2. WHEN generating documentation, THE Analysis_Engine SHALL create sections for: Project Overview, File-wise documentation, Class documentation, and Function documentation
3. WHEN documenting a class, THE Documentation_File SHALL include the class name, purpose, and all methods with their parameters
4. WHEN documenting a function, THE Documentation_File SHALL include the function name, parameters with descriptions, and purpose
5. WHEN a DOCUMENTATION.md file already exists, THE Analysis_Engine SHALL overwrite it with the newly generated content
6. THE Documentation_File SHALL contain only valid Markdown syntax

### Requirement 7: Extension User Interface

**User Story:** As a developer, I want a simple command to trigger documentation generation, so that I can easily generate documentation whenever needed.

#### Acceptance Criteria

1. WHEN the Extension is activated, THE Extension SHALL register a command named "Generate Code Documentation"
2. WHEN the user invokes the command, THE Extension SHALL display a progress notification showing "Generating documentation..."
3. WHILE documentation generation is in progress, THE Extension SHALL show progress updates for scanning, analysis, and generation phases
4. WHEN documentation generation completes successfully, THE Extension SHALL display a success message with the path to DOCUMENTATION.md
5. IF an error occurs during generation, THEN THE Extension SHALL display an error message with details about the failure

### Requirement 8: Extension-Python Communication

**User Story:** As a system architect, I want reliable communication between the VS Code extension and Python analysis engine, so that the system operates correctly across different platforms.

#### Acceptance Criteria

1. WHEN the Extension needs to analyze code, THE Extension SHALL spawn a Python child process using child_process.spawn
2. WHEN spawning the Python process, THE Extension SHALL pass the workspace path and discovered file list as JSON via stdin
3. WHEN the Analysis_Engine completes processing, THE Analysis_Engine SHALL output results as JSON to stdout
4. WHEN the Extension receives output from the Python process, THE Extension SHALL parse the JSON and handle any reported errors
5. IF the Python process exits with a non-zero code, THEN THE Extension SHALL display an error message to the user

### Requirement 9: Performance and Scalability

**User Story:** As a developer working on large codebases, I want documentation generation to complete in reasonable time, so that I can use the tool regularly without disrupting my workflow.

#### Acceptance Criteria

1. WHEN processing files, THE Analysis_Engine SHALL process files sequentially to avoid excessive memory usage
2. WHEN the Workspace contains more than 100 files, THE Extension SHALL provide progress updates at least every 10 files
3. THE Analysis_Engine SHALL limit memory usage by processing one file at a time and releasing resources after each file
4. WHEN the LLM request takes longer than 30 seconds, THE Analysis_Engine SHALL timeout and proceed with basic documentation
5. THE Extension SHALL complete documentation generation for a workspace with 50 files in under 5 minutes (assuming responsive LLM)

### Requirement 10: Error Handling and Resilience

**User Story:** As a developer, I want the system to handle errors gracefully and continue processing, so that one problematic file doesn't prevent documentation of the entire project.

#### Acceptance Criteria

1. WHEN a file cannot be read due to permissions, THE Analysis_Engine SHALL log the error and continue processing remaining files
2. WHEN a file contains syntax errors, THE Analysis_Engine SHALL skip that file and continue processing
3. IF the LLM is unreachable, THEN THE Analysis_Engine SHALL generate basic documentation without LLM enhancement
4. WHEN the Python process crashes, THE Extension SHALL display an error message and allow the user to retry
5. WHEN writing DOCUMENTATION.md fails due to permissions, THE Extension SHALL display an error message with the specific failure reason

### Requirement 11: Code Safety

**User Story:** As a security-conscious developer, I want assurance that the documentation tool never executes my code, so that I can safely use it on untrusted or incomplete codebases.

#### Acceptance Criteria

1. THE Analysis_Engine SHALL use only static analysis techniques (ast module for Python, regex for JavaScript/Java)
2. THE Analysis_Engine SHALL NOT use eval, exec, or any dynamic code execution functions
3. THE Analysis_Engine SHALL NOT import or load any modules from the analyzed codebase
4. THE Extension SHALL NOT modify any source files in the Workspace
5. THE Extension SHALL only create or update the DOCUMENTATION.md file

### Requirement 12: Markdown Output Quality

**User Story:** As a developer, I want the generated documentation to be well-formatted and readable, so that it serves as effective project documentation.

#### Acceptance Criteria

1. WHEN generating Markdown, THE Analysis_Engine SHALL use proper heading hierarchy (# for title, ## for sections, ### for subsections)
2. WHEN documenting functions with parameters, THE Analysis_Engine SHALL format parameters as a bulleted list or table
3. WHEN including code examples or signatures, THE Analysis_Engine SHALL use Markdown code blocks with appropriate language tags
4. THE Documentation_File SHALL include a table of contents linking to major sections
5. WHEN the LLM provides enhanced descriptions, THE Analysis_Engine SHALL format them as readable paragraphs without excessive technical jargon
