"""
Unit tests for Markdown generator
"""
import pytest
import os
import tempfile
from analysis_engine.markdown_generator import (
    generate_markdown,
    write_documentation,
    _generate_table_of_contents,
    _generate_overview,
    _generate_file_documentation,
    _generate_class_documentation,
    _generate_function_documentation,
    _format_parameters_inline,
    _create_anchor,
)
from analysis_engine.models import (
    FileMetadata,
    ClassMetadata,
    FunctionMetadata,
    Parameter,
)


class TestMarkdownGenerator:
    """Test suite for Markdown generator functionality"""
    
    def test_generate_markdown_empty_list(self):
        """Test generating markdown with no files"""
        result = generate_markdown([])
        
        assert "# Project Documentation" in result
        assert "## Table of Contents" in result
        assert "## Overview" in result
        assert "## Files" in result
        assert "0 source file(s)" in result
    
    def test_generate_markdown_with_single_file(self):
        """Test generating markdown with a single file"""
        file_meta = FileMetadata(
            file_path="src/example.py",
            language="python",
            functions=[
                FunctionMetadata(
                    name="test_func",
                    parameters=[
                        Parameter(name="arg1", type_hint="str", default_value=None),
                        Parameter(name="arg2", type_hint="int", default_value="42"),
                    ],
                    return_type="bool",
                    docstring="Test function",
                    line_number=10,
                )
            ],
            classes=[],
            parse_errors=[],
        )
        
        result = generate_markdown([file_meta])
        
        # Check main sections
        assert "# Project Documentation" in result
        assert "## Table of Contents" in result
        assert "## Overview" in result
        assert "## Files" in result
        
        # Check file is listed
        assert "src/example.py" in result
        assert "### src/example.py" in result
        
        # Check function is documented
        assert "test_func" in result
        assert "Test function" in result
        assert "arg1" in result
        assert "arg2" in result
        
        # Check statistics
        assert "1 source file(s)" in result
        assert "1 top-level function(s)" in result
    
    def test_generate_markdown_with_class(self):
        """Test generating markdown with a class"""
        file_meta = FileMetadata(
            file_path="src/myclass.py",
            language="python",
            functions=[],
            classes=[
                ClassMetadata(
                    name="MyClass",
                    docstring="A sample class",
                    methods=[
                        FunctionMetadata(
                            name="my_method",
                            parameters=[
                                Parameter(name="self"),
                                Parameter(name="value", type_hint="int"),
                            ],
                            return_type="None",
                            docstring="A sample method",
                            line_number=15,
                        )
                    ],
                    line_number=10,
                )
            ],
            parse_errors=[],
        )
        
        result = generate_markdown([file_meta])
        
        # Check class is documented
        assert "MyClass" in result
        assert "A sample class" in result
        
        # Check method is documented
        assert "my_method" in result
        assert "A sample method" in result
        assert "value" in result
        
        # Check statistics
        assert "1 class(es)" in result
        assert "1 method(s)" in result
    
    def test_generate_table_of_contents(self):
        """Test table of contents generation"""
        files = [
            FileMetadata("src/file1.py", "python", [], []),
            FileMetadata("src/file2.js", "javascript", [], []),
        ]
        
        result = _generate_table_of_contents(files)
        
        assert "## Table of Contents" in result
        assert "[Overview](#overview)" in result
        assert "[Files](#files)" in result
        assert "src/file1.py" in result
        assert "src/file2.js" in result
    
    def test_generate_overview(self):
        """Test overview section generation"""
        files = [
            FileMetadata(
                "file1.py",
                "python",
                classes=[
                    ClassMetadata("Class1", None, [
                        FunctionMetadata("method1", [], None, None, 1)
                    ], 1)
                ],
                functions=[
                    FunctionMetadata("func1", [], None, None, 10)
                ],
            ),
            FileMetadata(
                "file2.js",
                "javascript",
                classes=[],
                functions=[
                    FunctionMetadata("func2", [], None, None, 5)
                ],
            ),
        ]
        
        result = _generate_overview(files)
        
        assert "## Overview" in result
        assert "2 source file(s)" in result
        assert "1 class(es)" in result
        assert "2 top-level function(s)" in result
        assert "1 method(s)" in result
        assert "Python: 1 file(s)" in result
        assert "Javascript: 1 file(s)" in result
    
    def test_generate_file_documentation_with_errors(self):
        """Test file documentation with parse errors"""
        file_meta = FileMetadata(
            file_path="src/broken.py",
            language="python",
            functions=[],
            classes=[],
            parse_errors=["Syntax error at line 5", "Unexpected token"],
        )
        
        result = _generate_file_documentation(file_meta)
        
        assert "src/broken.py" in result
        assert "⚠️ Parse Errors:" in result
        assert "Syntax error at line 5" in result
        assert "Unexpected token" in result
    
    def test_generate_file_documentation_empty(self):
        """Test file documentation with no content"""
        file_meta = FileMetadata(
            file_path="src/empty.py",
            language="python",
            functions=[],
            classes=[],
            parse_errors=[],
        )
        
        result = _generate_file_documentation(file_meta)
        
        assert "src/empty.py" in result
        assert "No classes or functions found" in result
    
    def test_generate_class_documentation(self):
        """Test class documentation generation"""
        cls = ClassMetadata(
            name="TestClass",
            docstring="This is a test class",
            methods=[
                FunctionMetadata(
                    name="test_method",
                    parameters=[Parameter("self"), Parameter("arg")],
                    return_type="str",
                    docstring="Test method",
                    line_number=20,
                )
            ],
            line_number=10,
        )
        
        result = _generate_class_documentation(cls, "python")
        
        assert "TestClass" in result
        assert "This is a test class" in result
        assert "test_method" in result
        assert "Test method" in result
    
    def test_generate_function_documentation(self):
        """Test function documentation generation"""
        func = FunctionMetadata(
            name="calculate",
            parameters=[
                Parameter("x", "int", None),
                Parameter("y", "int", "10"),
            ],
            return_type="int",
            docstring="Calculate something",
            line_number=5,
        )
        
        result = _generate_function_documentation(func, "python")
        
        assert "calculate" in result
        assert "Calculate something" in result
        assert "x" in result
        assert "y" in result
        assert "Default: `10`" in result
        assert "**Returns:** int" in result
        assert "```python" in result
        assert "def calculate" in result
    
    def test_format_parameters_inline_empty(self):
        """Test formatting empty parameter list"""
        result = _format_parameters_inline([])
        assert result == ""
    
    def test_format_parameters_inline_with_types(self):
        """Test formatting parameters with type hints"""
        params = [
            Parameter("name", "str", None),
            Parameter("age", "int", "18"),
        ]
        
        result = _format_parameters_inline(params)
        
        assert "name: str" in result
        assert "age: int=18" in result
    
    def test_format_parameters_inline_without_types(self):
        """Test formatting parameters without type hints"""
        params = [
            Parameter("arg1", None, None),
            Parameter("arg2", None, "default"),
        ]
        
        result = _format_parameters_inline(params)
        
        assert "arg1" in result
        assert "arg2=default" in result
    
    def test_create_anchor(self):
        """Test anchor creation from text"""
        assert _create_anchor("src/file.py") == "srcfilepy"
        assert _create_anchor("My File.js") == "my-filejs"
        assert _create_anchor("path/to/file.java") == "pathtofilejava"
        assert _create_anchor("file_name.py") == "filenamepy"
    
    def test_markdown_heading_hierarchy(self):
        """Test that proper heading hierarchy is used"""
        file_meta = FileMetadata(
            file_path="test.py",
            language="python",
            classes=[
                ClassMetadata(
                    name="TestClass",
                    docstring="Test",
                    methods=[
                        FunctionMetadata("method", [], None, None, 1)
                    ],
                    line_number=1,
                )
            ],
            functions=[
                FunctionMetadata("func", [], None, None, 10)
            ],
        )
        
        result = generate_markdown([file_meta])
        
        # Check heading hierarchy
        assert "# Project Documentation" in result  # H1 for title
        assert "## Table of Contents" in result  # H2 for major sections
        assert "## Overview" in result
        assert "## Files" in result
        assert "### test.py" in result  # H3 for file names
        assert "#### Classes" in result  # H4 for subsections
        assert "##### TestClass" in result  # H5 for class/function names
        assert "###### method" in result  # H6 for methods
    
    def test_code_blocks_with_language_tags(self):
        """Test that code blocks use appropriate language tags"""
        # Python
        py_func = FunctionMetadata("py_func", [], None, None, 1)
        py_result = _generate_function_documentation(py_func, "python")
        assert "```python" in py_result
        
        # JavaScript
        js_func = FunctionMetadata("js_func", [], None, None, 1)
        js_result = _generate_function_documentation(js_func, "javascript")
        assert "```javascript" in js_result
        
        # Java
        java_func = FunctionMetadata("javaFunc", [], None, None, 1)
        java_result = _generate_function_documentation(java_func, "java")
        assert "```java" in java_result
    
    def test_parameters_formatted_as_bulleted_list(self):
        """Test that parameters are formatted as bulleted lists"""
        func = FunctionMetadata(
            name="test",
            parameters=[
                Parameter("param1", "str"),
                Parameter("param2", "int", "42"),
            ],
            return_type=None,
            docstring=None,
            line_number=1,
        )
        
        result = _generate_function_documentation(func, "python")
        
        assert "**Parameters:**" in result
        assert "- `param1`" in result
        assert "- `param2`" in result
    
    def test_multiple_files_with_different_languages(self):
        """Test generating documentation for multiple files with different languages"""
        files = [
            FileMetadata(
                "app.py",
                "python",
                functions=[FunctionMetadata("py_func", [], None, None, 1)],
                classes=[],
            ),
            FileMetadata(
                "script.js",
                "javascript",
                functions=[FunctionMetadata("js_func", [], None, None, 1)],
                classes=[],
            ),
            FileMetadata(
                "Main.java",
                "java",
                classes=[ClassMetadata("Main", None, [], 1)],
                functions=[],
            ),
        ]
        
        result = generate_markdown(files)
        
        # Check all files are included
        assert "app.py" in result
        assert "script.js" in result
        assert "Main.java" in result
        
        # Check language labels
        assert "**Language:** Python" in result
        assert "**Language:** Javascript" in result
        assert "**Language:** Java" in result
        
        # Check statistics
        assert "3 source file(s)" in result
        assert "Python: 1 file(s)" in result
        assert "Javascript: 1 file(s)" in result
        assert "Java: 1 file(s)" in result


class TestWriteDocumentation:
    """Test suite for write_documentation function"""
    
    def test_write_documentation_creates_new_file(self):
        """Test creating a new DOCUMENTATION.md file"""
        content = "# Test Documentation\n\nThis is a test."
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "DOCUMENTATION.md")
            
            # Write documentation
            write_documentation(content, output_path)
            
            # Verify file was created
            assert os.path.exists(output_path)
            
            # Verify content is correct
            with open(output_path, 'r', encoding='utf-8') as f:
                written_content = f.read()
            assert written_content == content
    
    def test_write_documentation_overwrites_existing_file(self):
        """Test overwriting an existing DOCUMENTATION.md file"""
        old_content = "# Old Documentation\n\nThis is old content."
        new_content = "# New Documentation\n\nThis is new content."
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "DOCUMENTATION.md")
            
            # Create existing file with old content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(old_content)
            
            # Verify old content exists
            with open(output_path, 'r', encoding='utf-8') as f:
                assert f.read() == old_content
            
            # Write new documentation
            write_documentation(new_content, output_path)
            
            # Verify file was overwritten with new content
            with open(output_path, 'r', encoding='utf-8') as f:
                written_content = f.read()
            assert written_content == new_content
            assert old_content not in written_content
    
    def test_write_documentation_handles_permission_error(self):
        """Test handling write permission errors"""
        content = "# Test Documentation"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "DOCUMENTATION.md")
            
            # Create file and make it read-only
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("initial")
            os.chmod(output_path, 0o444)  # Read-only
            
            try:
                # Attempt to write should raise PermissionError
                with pytest.raises(PermissionError) as exc_info:
                    write_documentation(content, output_path)
                
                # Verify error message contains file path
                assert output_path in str(exc_info.value)
                assert "Permission denied" in str(exc_info.value)
            finally:
                # Restore permissions for cleanup
                os.chmod(output_path, 0o644)
    
    def test_write_documentation_handles_invalid_path(self):
        """Test handling invalid file paths"""
        content = "# Test Documentation"
        
        # Use an invalid path (directory that doesn't exist)
        invalid_path = "/nonexistent/directory/DOCUMENTATION.md"
        
        # Attempt to write should raise OSError
        with pytest.raises(OSError) as exc_info:
            write_documentation(content, invalid_path)
        
        # Verify error message contains file path
        assert invalid_path in str(exc_info.value)
    
    def test_write_documentation_with_unicode_content(self):
        """Test writing documentation with Unicode characters"""
        content = "# Documentation\n\n✓ Unicode: 你好 🎉 café"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "DOCUMENTATION.md")
            
            # Write documentation with Unicode
            write_documentation(content, output_path)
            
            # Verify content is correctly written with UTF-8 encoding
            with open(output_path, 'r', encoding='utf-8') as f:
                written_content = f.read()
            assert written_content == content
    
    def test_write_documentation_with_empty_content(self):
        """Test writing empty documentation"""
        content = ""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "DOCUMENTATION.md")
            
            # Write empty documentation
            write_documentation(content, output_path)
            
            # Verify file was created and is empty
            assert os.path.exists(output_path)
            with open(output_path, 'r', encoding='utf-8') as f:
                written_content = f.read()
            assert written_content == ""
    
    def test_write_documentation_with_large_content(self):
        """Test writing large documentation file"""
        # Generate large content
        content = "# Large Documentation\n\n"
        content += "\n".join([f"## Section {i}\n\nContent for section {i}." for i in range(1000)])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "DOCUMENTATION.md")
            
            # Write large documentation
            write_documentation(content, output_path)
            
            # Verify content is correctly written
            with open(output_path, 'r', encoding='utf-8') as f:
                written_content = f.read()
            assert written_content == content
            assert "Section 999" in written_content
