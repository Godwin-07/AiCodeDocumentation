"""
Integration test for markdown generation with realistic data
"""
import pytest
from analysis_engine.markdown_generator import generate_markdown
from analysis_engine.models import (
    FileMetadata,
    ClassMetadata,
    FunctionMetadata,
    Parameter,
)


def test_realistic_project_documentation():
    """Test generating documentation for a realistic multi-file project"""
    
    # Python file with class and functions
    python_file = FileMetadata(
        file_path="src/calculator.py",
        language="python",
        classes=[
            ClassMetadata(
                name="Calculator",
                docstring="A simple calculator class for basic arithmetic operations.",
                methods=[
                    FunctionMetadata(
                        name="__init__",
                        parameters=[Parameter("self")],
                        return_type=None,
                        docstring="Initialize the calculator.",
                        line_number=5,
                    ),
                    FunctionMetadata(
                        name="add",
                        parameters=[
                            Parameter("self"),
                            Parameter("a", "float"),
                            Parameter("b", "float"),
                        ],
                        return_type="float",
                        docstring="Add two numbers and return the result.",
                        line_number=10,
                    ),
                    FunctionMetadata(
                        name="subtract",
                        parameters=[
                            Parameter("self"),
                            Parameter("a", "float"),
                            Parameter("b", "float"),
                        ],
                        return_type="float",
                        docstring="Subtract b from a and return the result.",
                        line_number=15,
                    ),
                ],
                line_number=3,
            )
        ],
        functions=[
            FunctionMetadata(
                name="main",
                parameters=[],
                return_type=None,
                docstring="Main entry point for the calculator application.",
                line_number=25,
            )
        ],
        parse_errors=[],
    )
    
    # JavaScript file with functions
    js_file = FileMetadata(
        file_path="src/utils.js",
        language="javascript",
        classes=[],
        functions=[
            FunctionMetadata(
                name="formatNumber",
                parameters=[
                    Parameter("num"),
                    Parameter("decimals", default_value="2"),
                ],
                return_type="string",
                docstring="Format a number with specified decimal places.",
                line_number=5,
            ),
            FunctionMetadata(
                name="validateInput",
                parameters=[Parameter("input")],
                return_type="boolean",
                docstring="Validate user input for numeric values.",
                line_number=12,
            ),
        ],
        parse_errors=[],
    )
    
    # Java file with class
    java_file = FileMetadata(
        file_path="src/Main.java",
        language="java",
        classes=[
            ClassMetadata(
                name="Main",
                docstring="Main application class.",
                methods=[
                    FunctionMetadata(
                        name="main",
                        parameters=[Parameter("args", "String[]")],
                        return_type="void",
                        docstring="Application entry point.",
                        line_number=8,
                    )
                ],
                line_number=5,
            )
        ],
        functions=[],
        parse_errors=[],
    )
    
    # Generate documentation
    all_files = [python_file, js_file, java_file]
    result = generate_markdown(all_files)
    
    # Verify structure
    assert "# Project Documentation" in result
    assert "*Generated on:" in result
    
    # Verify table of contents
    assert "## Table of Contents" in result
    assert "[Overview](#overview)" in result
    assert "[Files](#files)" in result
    assert "src/calculator.py" in result
    assert "src/utils.js" in result
    assert "src/Main.java" in result
    
    # Verify overview statistics
    assert "## Overview" in result
    assert "3 source file(s)" in result
    assert "2 class(es)" in result
    assert "3 top-level function(s)" in result or "1 top-level function(s)" in result
    assert "Python: 1 file(s)" in result
    assert "Javascript: 1 file(s)" in result
    assert "Java: 1 file(s)" in result
    
    # Verify files section
    assert "## Files" in result
    
    # Verify Python file documentation
    assert "### src/calculator.py" in result
    assert "**Language:** Python" in result
    assert "#### Classes" in result
    assert "##### Calculator" in result
    assert "A simple calculator class" in result
    assert "###### add" in result
    assert "###### subtract" in result
    assert "**Parameters:**" in result
    assert "`a`" in result
    assert "`b`" in result
    assert "```python" in result
    assert "def add" in result
    
    # Verify JavaScript file documentation
    assert "### src/utils.js" in result
    assert "**Language:** Javascript" in result
    assert "#### Functions" in result
    assert "##### formatNumber" in result
    assert "##### validateInput" in result
    assert "```javascript" in result
    
    # Verify Java file documentation
    assert "### src/Main.java" in result
    assert "**Language:** Java" in result
    assert "##### Main" in result
    assert "```java" in result
    
    # Verify separators between files
    assert result.count("---") >= 2  # At least 2 separators for 3 files
    
    # Verify proper heading hierarchy (no H7 or deeper)
    assert "#######" not in result
    
    # Print a sample of the output for manual inspection
    print("\n" + "="*80)
    print("GENERATED DOCUMENTATION SAMPLE:")
    print("="*80)
    lines = result.split("\n")
    print("\n".join(lines[:50]))  # Print first 50 lines
    print("\n... (truncated) ...")
    print("="*80)


def test_documentation_with_parse_errors():
    """Test that parse errors are properly documented"""
    
    file_with_errors = FileMetadata(
        file_path="src/broken.py",
        language="python",
        classes=[],
        functions=[],
        parse_errors=[
            "SyntaxError: invalid syntax at line 10",
            "IndentationError: unexpected indent at line 15",
        ],
    )
    
    result = generate_markdown([file_with_errors])
    
    assert "src/broken.py" in result
    assert "⚠️ Parse Errors:" in result
    assert "SyntaxError: invalid syntax at line 10" in result
    assert "IndentationError: unexpected indent at line 15" in result
    assert "No classes or functions found" in result


def test_documentation_markdown_validity():
    """Test that generated markdown follows proper syntax"""
    
    file_meta = FileMetadata(
        file_path="test.py",
        language="python",
        classes=[
            ClassMetadata(
                name="TestClass",
                docstring="Test class",
                methods=[
                    FunctionMetadata(
                        name="test_method",
                        parameters=[Parameter("self"), Parameter("x", "int")],
                        return_type="str",
                        docstring="Test method",
                        line_number=5,
                    )
                ],
                line_number=1,
            )
        ],
        functions=[
            FunctionMetadata(
                name="test_func",
                parameters=[Parameter("arg", "str", "'default'")],
                return_type="bool",
                docstring="Test function",
                line_number=20,
            )
        ],
        parse_errors=[],
    )
    
    result = generate_markdown([file_meta])
    
    # Check for proper markdown elements
    # Headers
    assert result.count("# Project Documentation") == 1
    assert "## Table of Contents" in result
    assert "## Overview" in result
    assert "## Files" in result
    
    # Lists
    assert "- [Overview]" in result
    assert "- [Files]" in result
    
    # Code blocks
    assert "```python" in result
    assert result.count("```") % 2 == 0  # All code blocks should be closed
    
    # Bold text
    assert "**Language:**" in result
    assert "**Parameters:**" in result
    assert "**Returns:**" in result
    
    # Inline code
    assert "`self`" in result
    assert "`x`" in result
    assert "`arg`" in result
    
    # Links (in TOC)
    assert "(#overview)" in result
    assert "(#files)" in result
    
    # Separators
    assert "---" in result


if __name__ == "__main__":
    # Run the realistic test to see output
    test_realistic_project_documentation()
