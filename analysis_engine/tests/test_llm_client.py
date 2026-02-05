"""
Tests for LLM client functionality
"""
import json
import pytest
from unittest.mock import Mock, patch
import requests
from analysis_engine.llm_client import (
    send_to_llm, _format_metadata_as_json, _construct_prompt, 
    generate_basic_documentation, _apply_code_safety_check, 
    _sanitize_docstring, _looks_like_code
)
from analysis_engine.models import FileMetadata, ClassMetadata, FunctionMetadata, Parameter, LLMResponse


class TestLLMClient:
    """Test cases for LLM client functionality"""
    
    def test_format_metadata_as_json_simple_function(self):
        """Test formatting simple function metadata as JSON"""
        metadata = FileMetadata(
            file_path="test.py",
            language="python",
            functions=[
                FunctionMetadata(
                    name="test_func",
                    parameters=[
                        Parameter(name="arg1", type_hint="str", default_value=None),
                        Parameter(name="arg2", type_hint="int", default_value="42")
                    ],
                    return_type="bool",
                    docstring="Test function",
                    line_number=1
                )
            ]
        )
        
        result = _format_metadata_as_json(metadata)
        parsed = json.loads(result)
        
        assert parsed["file_path"] == "test.py"
        assert parsed["language"] == "python"
        assert len(parsed["functions"]) == 1
        assert parsed["functions"][0]["name"] == "test_func"
        assert len(parsed["functions"][0]["parameters"]) == 2
        assert parsed["functions"][0]["parameters"][0]["name"] == "arg1"
        assert parsed["functions"][0]["parameters"][1]["default_value"] == "42"
    
    def test_format_metadata_as_json_with_class(self):
        """Test formatting class metadata as JSON"""
        metadata = FileMetadata(
            file_path="test.py",
            language="python",
            classes=[
                ClassMetadata(
                    name="TestClass",
                    docstring="Test class",
                    line_number=5,
                    methods=[
                        FunctionMetadata(
                            name="method1",
                            parameters=[Parameter(name="self")],
                            return_type=None,
                            docstring="Test method",
                            line_number=7
                        )
                    ]
                )
            ]
        )
        
        result = _format_metadata_as_json(metadata)
        parsed = json.loads(result)
        
        assert len(parsed["classes"]) == 1
        assert parsed["classes"][0]["name"] == "TestClass"
        assert len(parsed["classes"][0]["methods"]) == 1
        assert parsed["classes"][0]["methods"][0]["name"] == "method1"
    
    def test_construct_prompt(self):
        """Test prompt construction"""
        metadata_json = '{"file_path": "test.py", "language": "python"}'
        language = "python"
        
        result = _construct_prompt(metadata_json, language)
        
        assert "python code metadata" in result
        assert metadata_json in result
        assert "Markdown" in result
        assert "Requirements:" in result
    
    @patch('analysis_engine.llm_client.requests.post')
    def test_send_to_llm_success(self, mock_post):
        """Test successful LLM request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "message": {
                "content": "# Test Documentation\n\nThis is test documentation."
            }
        }
        mock_post.return_value = mock_response
        
        metadata = FileMetadata(
            file_path="test.py",
            language="python",
            functions=[
                FunctionMetadata(
                    name="test_func",
                    parameters=[],
                    return_type=None,
                    docstring=None,
                    line_number=1
                )
            ]
        )
        
        result = send_to_llm(metadata, "http://test.com", "test-model", 30)
        
        assert result.success is True
        assert "Test Documentation" in result.enhanced_description
        assert result.error is None
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 30
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
        
        request_data = call_args[1]["json"]
        assert request_data["model"] == "test-model"
        assert request_data["stream"] is False
        assert len(request_data["messages"]) == 2
    
    @patch('analysis_engine.llm_client.requests.post')
    def test_send_to_llm_timeout(self, mock_post):
        """Test LLM request timeout with fallback to basic documentation"""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        metadata = FileMetadata(file_path="test.py", language="python")
        result = send_to_llm(metadata, "http://test.com", "test-model", 30)
        
        assert result.success is True  # Should succeed with fallback
        assert "Used basic documentation due to LLM timeout" in result.error
        assert "## test.py" in result.enhanced_description
        assert "**Language:** Python" in result.enhanced_description
    
    @patch('analysis_engine.llm_client.requests.post')
    def test_send_to_llm_connection_error(self, mock_post):
        """Test LLM connection error with fallback to basic documentation"""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        metadata = FileMetadata(file_path="test.py", language="python")
        result = send_to_llm(metadata, "http://test.com", "test-model", 30)
        
        assert result.success is True  # Should succeed with fallback
        assert "Used basic documentation due to LLM connection error" in result.error
        assert "## test.py" in result.enhanced_description
        assert "**Language:** Python" in result.enhanced_description
    
    @patch('analysis_engine.llm_client.requests.post')
    def test_send_to_llm_http_error(self, mock_post):
        """Test LLM HTTP error with fallback to basic documentation"""
        mock_response = Mock()
        mock_response.status_code = 500
        
        # Create HTTPError with response
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response
        
        metadata = FileMetadata(file_path="test.py", language="python")
        result = send_to_llm(metadata, "http://test.com", "test-model", 30)
        
        assert result.success is True  # Should succeed with fallback
        assert "Used basic documentation due to HTTP error: 500" in result.error
        assert "## test.py" in result.enhanced_description
        assert "**Language:** Python" in result.enhanced_description
    
    @patch('analysis_engine.llm_client.requests.post')
    def test_send_to_llm_invalid_json_response(self, mock_post):
        """Test LLM invalid JSON response with fallback to basic documentation"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response
        
        metadata = FileMetadata(file_path="test.py", language="python")
        result = send_to_llm(metadata, "http://test.com", "test-model", 30)
        
        assert result.success is True  # Should succeed with fallback
        assert "Used basic documentation due to invalid JSON response" in result.error
        assert "## test.py" in result.enhanced_description
        assert "**Language:** Python" in result.enhanced_description
    
    @patch('analysis_engine.llm_client.requests.post')
    def test_send_to_llm_invalid_response_format(self, mock_post):
        """Test LLM response with invalid format and fallback to basic documentation"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"invalid": "format"}
        mock_post.return_value = mock_response
        
        metadata = FileMetadata(file_path="test.py", language="python")
        result = send_to_llm(metadata, "http://test.com", "test-model", 30)
        
        assert result.success is True  # Should succeed with fallback
        assert "Used basic documentation due to invalid LLM response format" in result.error
        assert "## test.py" in result.enhanced_description
        assert "**Language:** Python" in result.enhanced_description
    
    def test_format_metadata_empty_file(self):
        """Test formatting metadata for empty file"""
        metadata = FileMetadata(
            file_path="empty.py",
            language="python"
        )
        
        result = _format_metadata_as_json(metadata)
        parsed = json.loads(result)
        
        assert parsed["file_path"] == "empty.py"
        assert parsed["language"] == "python"
        assert parsed["classes"] == []
        assert parsed["functions"] == []
    
    def test_generate_basic_documentation_empty_file(self):
        """Test generating basic documentation for empty file"""
        metadata = FileMetadata(
            file_path="empty.py",
            language="python"
        )
        
        result = generate_basic_documentation(metadata)
        
        assert "## empty.py" in result
        assert "**Language:** Python" in result
        assert "*No classes or functions found in this file.*" in result
    
    def test_generate_basic_documentation_with_function(self):
        """Test generating basic documentation for file with function"""
        metadata = FileMetadata(
            file_path="test.py",
            language="python",
            functions=[
                FunctionMetadata(
                    name="test_func",
                    parameters=[
                        Parameter(name="arg1", type_hint="str", default_value=None),
                        Parameter(name="arg2", type_hint="int", default_value="42")
                    ],
                    return_type="bool",
                    docstring="Test function docstring",
                    line_number=5
                )
            ]
        )
        
        result = generate_basic_documentation(metadata)
        
        assert "## test.py" in result
        assert "**Language:** Python" in result
        assert "### Functions" in result
        assert "#### test_func(arg1: str, arg2: int = 42) -> bool" in result
        assert "Test function docstring" in result
    
    def test_generate_basic_documentation_with_class(self):
        """Test generating basic documentation for file with class"""
        metadata = FileMetadata(
            file_path="test.py",
            language="python",
            classes=[
                ClassMetadata(
                    name="TestClass",
                    docstring="Test class docstring",
                    line_number=10,
                    methods=[
                        FunctionMetadata(
                            name="method1",
                            parameters=[Parameter(name="self"), Parameter(name="param1", type_hint="str")],
                            return_type=None,
                            docstring="Test method docstring",
                            line_number=12
                        )
                    ]
                )
            ]
        )
        
        result = generate_basic_documentation(metadata)
        
        assert "## test.py" in result
        assert "**Language:** Python" in result
        assert "### Classes" in result
        assert "#### TestClass" in result
        assert "Test class docstring" in result
        assert "**Methods:**" in result
        assert "##### method1(self, param1: str)" in result
        assert "Test method docstring" in result
    
    def test_generate_basic_documentation_with_parse_errors(self):
        """Test generating basic documentation with parse errors"""
        metadata = FileMetadata(
            file_path="error.py",
            language="python",
            parse_errors=["Syntax error at line 5", "Unexpected token"]
        )
        
        result = generate_basic_documentation(metadata)
        
        assert "## error.py" in result
        assert "**Language:** Python" in result
        assert "**Parse Errors:**" in result
        assert "- Syntax error at line 5" in result
        assert "- Unexpected token" in result


class TestCodeSafetyCheck:
    """Test cases for code safety check functionality"""
    
    def test_looks_like_code_function_definition(self):
        """Test detection of function definition as code"""
        assert _looks_like_code("def my_function():") is True
        assert _looks_like_code("function myFunction() {") is True
        assert _looks_like_code("public void myMethod() {") is True
    
    def test_looks_like_code_class_definition(self):
        """Test detection of class definition as code"""
        assert _looks_like_code("class MyClass:") is True
        assert _looks_like_code("public class MyClass {") is True
    
    def test_looks_like_code_import_statements(self):
        """Test detection of import statements as code"""
        assert _looks_like_code("import os") is True
        assert _looks_like_code("from typing import List") is True
    
    def test_looks_like_code_control_flow(self):
        """Test detection of control flow statements as code"""
        assert _looks_like_code("if condition:") is True
        assert _looks_like_code("for item in items:") is True
        assert _looks_like_code("while True:") is True
        assert _looks_like_code("return value") is True
    
    def test_looks_like_code_assignments(self):
        """Test detection of assignment statements as code"""
        assert _looks_like_code("x = 5") is True
        assert _looks_like_code("result = calculate()") is True
        assert _looks_like_code("const x = 5;") is True
    
    def test_looks_like_code_natural_language(self):
        """Test that natural language is not detected as code"""
        assert _looks_like_code("This is a description") is False
        assert _looks_like_code("The function returns a value") is False
        assert _looks_like_code("Calculate the sum of two numbers") is False
        assert _looks_like_code("This parameter equals the input value") is False
    
    def test_looks_like_code_empty_line(self):
        """Test that empty lines are not detected as code"""
        assert _looks_like_code("") is False
        assert _looks_like_code("   ") is False
    
    def test_sanitize_docstring_with_code_blocks(self):
        """Test sanitizing docstring with code blocks"""
        docstring = """This is a description.
        
```python
def example():
    return True
```

More description here."""
        
        result = _sanitize_docstring(docstring)
        
        assert "This is a description" in result
        assert "More description here" in result
        assert "def example():" not in result
        assert "return True" not in result
        assert "```" not in result
    
    def test_sanitize_docstring_with_interactive_prompt(self):
        """Test sanitizing docstring with Python interactive prompt"""
        docstring = """Example usage:
        
>>> my_function()
True
>>> another_call()
42

This shows the results."""
        
        result = _sanitize_docstring(docstring)
        
        assert "Example usage:" in result
        assert "This shows the results" in result
        assert ">>> my_function()" not in result
        assert ">>> another_call()" not in result
    
    def test_sanitize_docstring_with_code_statements(self):
        """Test sanitizing docstring with code statements"""
        docstring = """This function does something.
        
def helper():
    pass
    
It uses a helper function."""
        
        result = _sanitize_docstring(docstring)
        
        assert "This function does something" in result
        assert "It uses a helper function" in result
        assert "def helper():" not in result
        assert "pass" not in result
    
    def test_sanitize_docstring_preserves_natural_language(self):
        """Test that natural language is preserved in sanitization"""
        docstring = """Calculate the sum of two numbers.
        
This function takes two parameters and returns their sum.
The result is always a number."""
        
        result = _sanitize_docstring(docstring)
        
        assert "Calculate the sum of two numbers" in result
        assert "This function takes two parameters" in result
        assert "The result is always a number" in result
    
    def test_sanitize_docstring_empty(self):
        """Test sanitizing empty docstring"""
        assert _sanitize_docstring("") == ""
        assert _sanitize_docstring(None) == ""
    
    def test_apply_code_safety_check_with_clean_metadata(self):
        """Test code safety check with clean metadata (no code in docstrings)"""
        metadata = FileMetadata(
            file_path="test.py",
            language="python",
            functions=[
                FunctionMetadata(
                    name="test_func",
                    parameters=[Parameter(name="arg1")],
                    return_type="str",
                    docstring="This function does something useful.",
                    line_number=1
                )
            ]
        )
        
        result = _apply_code_safety_check(metadata)
        
        assert result.file_path == "test.py"
        assert result.language == "python"
        assert len(result.functions) == 1
        assert result.functions[0].name == "test_func"
        assert result.functions[0].docstring == "This function does something useful."
    
    def test_apply_code_safety_check_strips_code_from_docstrings(self):
        """Test that code safety check strips code from docstrings"""
        metadata = FileMetadata(
            file_path="test.py",
            language="python",
            functions=[
                FunctionMetadata(
                    name="test_func",
                    parameters=[Parameter(name="arg1")],
                    return_type="str",
                    docstring="""This function does something.
                    
```python
def example():
    return True
```

More description.""",
                    line_number=1
                )
            ]
        )
        
        result = _apply_code_safety_check(metadata)
        
        assert "This function does something" in result.functions[0].docstring
        assert "More description" in result.functions[0].docstring
        assert "def example():" not in result.functions[0].docstring
        assert "```" not in result.functions[0].docstring
    
    def test_apply_code_safety_check_with_class_methods(self):
        """Test code safety check with class methods"""
        metadata = FileMetadata(
            file_path="test.py",
            language="python",
            classes=[
                ClassMetadata(
                    name="TestClass",
                    docstring="""A test class.
                    
>>> obj = TestClass()
>>> obj.method()

This is the class.""",
                    line_number=1,
                    methods=[
                        FunctionMetadata(
                            name="method",
                            parameters=[Parameter(name="self")],
                            return_type=None,
                            docstring="""Method description.
                            
def internal():
    pass
    
More info.""",
                            line_number=3
                        )
                    ]
                )
            ]
        )
        
        result = _apply_code_safety_check(metadata)
        
        # Check class docstring is sanitized
        assert "A test class" in result.classes[0].docstring
        assert "This is the class" in result.classes[0].docstring
        assert ">>> obj = TestClass()" not in result.classes[0].docstring
        
        # Check method docstring is sanitized
        assert "Method description" in result.classes[0].methods[0].docstring
        assert "More info" in result.classes[0].methods[0].docstring
        assert "def internal():" not in result.classes[0].methods[0].docstring
    
    def test_apply_code_safety_check_preserves_structure(self):
        """Test that code safety check preserves metadata structure"""
        metadata = FileMetadata(
            file_path="test.py",
            language="python",
            classes=[
                ClassMetadata(
                    name="MyClass",
                    docstring="Class description",
                    line_number=5,
                    methods=[
                        FunctionMetadata(
                            name="method1",
                            parameters=[Parameter(name="self"), Parameter(name="x", type_hint="int")],
                            return_type="bool",
                            docstring="Method description",
                            line_number=7
                        )
                    ]
                )
            ],
            functions=[
                FunctionMetadata(
                    name="func1",
                    parameters=[Parameter(name="a", default_value="10")],
                    return_type="str",
                    docstring="Function description",
                    line_number=15
                )
            ],
            parse_errors=["Error 1"]
        )
        
        result = _apply_code_safety_check(metadata)
        
        # Verify all structure is preserved
        assert result.file_path == "test.py"
        assert result.language == "python"
        assert len(result.classes) == 1
        assert result.classes[0].name == "MyClass"
        assert result.classes[0].line_number == 5
        assert len(result.classes[0].methods) == 1
        assert result.classes[0].methods[0].name == "method1"
        assert len(result.classes[0].methods[0].parameters) == 2
        assert result.classes[0].methods[0].parameters[1].type_hint == "int"
        assert result.classes[0].methods[0].return_type == "bool"
        assert len(result.functions) == 1
        assert result.functions[0].name == "func1"
        assert result.functions[0].parameters[0].default_value == "10"
        assert result.parse_errors == ["Error 1"]
    
    @patch('analysis_engine.llm_client.requests.post')
    def test_send_to_llm_applies_safety_check(self, mock_post):
        """Test that send_to_llm applies code safety check before sending"""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "message": {
                "content": "# Documentation"
            }
        }
        mock_post.return_value = mock_response
        
        # Create metadata with code in docstring
        metadata = FileMetadata(
            file_path="test.py",
            language="python",
            functions=[
                FunctionMetadata(
                    name="test_func",
                    parameters=[],
                    return_type=None,
                    docstring="""Function description.
                    
```python
def example():
    return True
```

More info.""",
                    line_number=1
                )
            ]
        )
        
        result = send_to_llm(metadata, "http://test.com", "test-model", 30)
        
        # Verify request was made
        assert mock_post.called
        
        # Get the request payload
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        prompt = request_data["messages"][1]["content"]
        
        # Verify code was stripped from the prompt
        assert "Function description" in prompt
        assert "More info" in prompt
        assert "def example():" not in prompt
        assert "return True" not in prompt
        assert "```" not in prompt
