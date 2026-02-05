"""
Unit tests for Python AST-based parser
"""
import pytest
import tempfile
import os
from pathlib import Path
from analysis_engine.parsers.python_parser import parse_python_file
from analysis_engine.models import FileMetadata, ClassMetadata, FunctionMetadata, Parameter


class TestPythonParser:
    """Test suite for Python parser functionality"""
    
    def test_parse_simple_function(self):
        """Test parsing a simple function with parameters"""
        code = '''
def greet(name, greeting="Hello"):
    """Greet someone with a message"""
    return f"{greeting}, {name}!"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert result.language == 'python'
            assert len(result.functions) == 1
            assert len(result.classes) == 0
            assert len(result.parse_errors) == 0
            
            func = result.functions[0]
            assert func.name == 'greet'
            assert func.docstring == 'Greet someone with a message'
            assert len(func.parameters) == 2
            assert func.parameters[0].name == 'name'
            assert func.parameters[0].default_value is None
            assert func.parameters[1].name == 'greeting'
            # ast.unparse normalizes quotes, so accept either single or double quotes
            assert func.parameters[1].default_value in ['"Hello"', "'Hello'"]
        finally:
            os.unlink(temp_path)
    
    def test_parse_function_with_type_hints(self):
        """Test parsing a function with type hints"""
        code = '''
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.functions) == 1
            func = result.functions[0]
            assert func.name == 'add'
            assert func.return_type == 'int'
            assert len(func.parameters) == 2
            assert func.parameters[0].type_hint == 'int'
            assert func.parameters[1].type_hint == 'int'
        finally:
            os.unlink(temp_path)
    
    def test_parse_class_with_methods(self):
        """Test parsing a class with methods"""
        code = '''
class Calculator:
    """A simple calculator class"""
    
    def add(self, a, b):
        """Add two numbers"""
        return a + b
    
    def subtract(self, a, b):
        """Subtract b from a"""
        return a - b
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.classes) == 1
            assert len(result.functions) == 0
            
            cls = result.classes[0]
            assert cls.name == 'Calculator'
            assert cls.docstring == 'A simple calculator class'
            assert len(cls.methods) == 2
            
            add_method = cls.methods[0]
            assert add_method.name == 'add'
            assert add_method.docstring == 'Add two numbers'
            assert len(add_method.parameters) == 3  # self, a, b
            assert add_method.parameters[0].name == 'self'
            
            subtract_method = cls.methods[1]
            assert subtract_method.name == 'subtract'
            assert subtract_method.docstring == 'Subtract b from a'
        finally:
            os.unlink(temp_path)
    
    def test_parse_nested_functions(self):
        """Test that nested functions are not extracted at module level"""
        code = '''
def outer():
    """Outer function"""
    def inner():
        """Inner function"""
        pass
    return inner
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            # Only the outer function should be extracted at module level
            assert len(result.functions) == 1
            assert result.functions[0].name == 'outer'
        finally:
            os.unlink(temp_path)
    
    def test_parse_function_with_varargs_kwargs(self):
        """Test parsing functions with *args and **kwargs"""
        code = '''
def flexible_func(a, b=10, *args, **kwargs):
    """A function with various parameter types"""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.functions) == 1
            func = result.functions[0]
            assert len(func.parameters) == 4
            assert func.parameters[0].name == 'a'
            assert func.parameters[1].name == 'b'
            assert func.parameters[1].default_value == '10'
            assert func.parameters[2].name == '*args'
            assert func.parameters[3].name == '**kwargs'
        finally:
            os.unlink(temp_path)
    
    def test_parse_async_function(self):
        """Test parsing async functions"""
        code = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from a URL"""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.functions) == 1
            func = result.functions[0]
            assert func.name == 'fetch_data'
            assert func.return_type == 'dict'
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_with_syntax_error(self):
        """Test handling of syntax errors (Requirement 3.6)"""
        code = '''
def broken_function(
    """This has a syntax error"""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            # Should return metadata with errors, not crash
            assert len(result.parse_errors) > 0
            assert 'Syntax error' in result.parse_errors[0]
            assert len(result.functions) == 0
            assert len(result.classes) == 0
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_with_syntax_error_logs_error(self, caplog):
        """Test that syntax errors are logged (Requirement 3.6)"""
        import logging
        code = '''
def broken_function(
    """This has a syntax error"""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            with caplog.at_level(logging.ERROR):
                result = parse_python_file(temp_path)
            
            # Verify error was logged
            assert len(caplog.records) > 0
            assert any('Failed to parse' in record.message for record in caplog.records)
            assert any('Syntax error' in record.message for record in caplog.records)
            
            # Verify error is in parse_errors
            assert len(result.parse_errors) > 0
            assert 'Syntax error' in result.parse_errors[0]
        finally:
            os.unlink(temp_path)
    
    def test_parse_nonexistent_file(self):
        """Test handling of file not found errors"""
        result = parse_python_file('/nonexistent/path/file.py')
        
        assert len(result.parse_errors) > 0
        assert 'File not found' in result.parse_errors[0]
    
    def test_parse_nonexistent_file_logs_error(self, caplog):
        """Test that file not found errors are logged"""
        import logging
        
        with caplog.at_level(logging.ERROR):
            result = parse_python_file('/nonexistent/path/file.py')
        
        # Verify error was logged
        assert len(caplog.records) > 0
        assert any('File not found' in record.message for record in caplog.records)
        
        # Verify error is in parse_errors
        assert len(result.parse_errors) > 0
        assert 'File not found' in result.parse_errors[0]
    
    def test_parse_empty_file(self):
        """Test parsing an empty file"""
        code = ''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.functions) == 0
            assert len(result.classes) == 0
            assert len(result.parse_errors) == 0
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_with_only_comments(self):
        """Test parsing a file with only comments"""
        code = '''
# This is a comment
# Another comment
"""
This is a module docstring
"""
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.functions) == 0
            assert len(result.classes) == 0
            assert len(result.parse_errors) == 0
        finally:
            os.unlink(temp_path)
    
    def test_parse_multiple_classes_and_functions(self):
        """Test parsing a file with multiple classes and functions"""
        code = '''
def helper_function():
    """A helper function"""
    pass

class FirstClass:
    """First class"""
    def method1(self):
        pass

class SecondClass:
    """Second class"""
    def method2(self):
        pass

def another_function():
    """Another function"""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.functions) == 2
            assert len(result.classes) == 2
            assert result.functions[0].name == 'helper_function'
            assert result.functions[1].name == 'another_function'
            assert result.classes[0].name == 'FirstClass'
            assert result.classes[1].name == 'SecondClass'
        finally:
            os.unlink(temp_path)
    
    def test_parse_function_without_docstring(self):
        """Test parsing a function without a docstring"""
        code = '''
def no_docs(x, y):
    return x + y
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.functions) == 1
            func = result.functions[0]
            assert func.name == 'no_docs'
            assert func.docstring is None
        finally:
            os.unlink(temp_path)
    
    def test_parse_class_without_docstring(self):
        """Test parsing a class without a docstring"""
        code = '''
class NoDocsClass:
    def method(self):
        pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert cls.name == 'NoDocsClass'
            assert cls.docstring is None
        finally:
            os.unlink(temp_path)
    
    def test_line_numbers_are_captured(self):
        """Test that line numbers are correctly captured"""
        code = '''
def first_function():
    pass

class MyClass:
    def method(self):
        pass

def second_function():
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert result.functions[0].line_number == 2
            assert result.classes[0].line_number == 5
            assert result.functions[1].line_number == 9
        finally:
            os.unlink(temp_path)
    
    def test_parse_function_with_complex_defaults(self):
        """Test parsing functions with complex default values"""
        code = '''
def complex_defaults(a=[], b={}, c=None, d=[1, 2, 3]):
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.functions) == 1
            func = result.functions[0]
            assert len(func.parameters) == 4
            assert func.parameters[0].default_value == '[]'
            assert func.parameters[1].default_value == '{}'
            assert func.parameters[2].default_value == 'None'
            assert func.parameters[3].default_value == '[1, 2, 3]'
        finally:
            os.unlink(temp_path)

    def test_parse_function_with_keyword_only_args(self):
        """Test parsing functions with keyword-only arguments"""
        code = '''
def keyword_only(a, b, *, c, d=10):
    """Function with keyword-only args"""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.functions) == 1
            func = result.functions[0]
            assert len(func.parameters) == 4
            assert func.parameters[0].name == 'a'
            assert func.parameters[1].name == 'b'
            assert func.parameters[2].name == 'c'
            assert func.parameters[2].default_value is None
            assert func.parameters[3].name == 'd'
            assert func.parameters[3].default_value == '10'
        finally:
            os.unlink(temp_path)
    
    def test_parse_function_with_positional_only_args(self):
        """Test parsing functions with positional-only arguments (Python 3.8+)"""
        code = '''
def positional_only(a, b, /, c, d=5):
    """Function with positional-only args"""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_python_file(temp_path)
            
            assert len(result.functions) == 1
            func = result.functions[0]
            # Should have all 4 parameters
            assert len(func.parameters) == 4
            # Check that positional-only args are captured
            param_names = [p.name for p in func.parameters]
            assert 'a' in param_names
            assert 'b' in param_names
            assert 'c' in param_names
            assert 'd' in param_names
        finally:
            os.unlink(temp_path)

    def test_parse_comprehensive_sample_file(self):
        """Test parsing a comprehensive sample Python file with all features"""
        sample_file = Path(__file__).parent / 'sample_python_file.py'
        
        result = parse_python_file(str(sample_file))
        
        # Verify no parse errors
        assert len(result.parse_errors) == 0
        assert result.language == 'python'
        
        # Should have 3 module-level functions
        assert len(result.functions) == 3
        function_names = [f.name for f in result.functions]
        assert 'module_function' in function_names
        assert 'async_fetch' in function_names
        assert 'flexible_function' in function_names
        
        # Should have 1 class
        assert len(result.classes) == 1
        calc_class = result.classes[0]
        assert calc_class.name == 'Calculator'
        assert calc_class.docstring is not None
        assert 'calculator class' in calc_class.docstring.lower()
        
        # Calculator should have 4 methods
        assert len(calc_class.methods) == 4
        method_names = [m.name for m in calc_class.methods]
        assert '__init__' in method_names
        assert 'add' in method_names
        assert 'subtract' in method_names
        assert 'reset' in method_names
        
        # Check module_function details
        module_func = next(f for f in result.functions if f.name == 'module_function')
        assert module_func.return_type == 'int'
        assert len(module_func.parameters) == 2
        assert module_func.parameters[0].name == 'x'
        assert module_func.parameters[0].type_hint == 'int'
        assert module_func.parameters[1].name == 'y'
        assert module_func.parameters[1].default_value == '10'
        assert module_func.docstring is not None
        
        # Check async_fetch details
        async_func = next(f for f in result.functions if f.name == 'async_fetch')
        assert async_func.return_type == 'dict'
        assert len(async_func.parameters) == 2
        
        # Check flexible_function with *args and **kwargs
        flex_func = next(f for f in result.functions if f.name == 'flexible_function')
        assert len(flex_func.parameters) == 2
        assert flex_func.parameters[0].name == '*args'
        assert flex_func.parameters[1].name == '**kwargs'
    
    def test_error_handling_returns_partial_metadata(self, caplog):
        """Test that error handling returns partial metadata (Requirement 3.6)"""
        import logging
        
        # Create a file with valid code followed by syntax error
        code = '''
def valid_function():
    """This is valid"""
    return 42

class ValidClass:
    """This is also valid"""
    pass

# Now introduce a syntax error
def broken_function(
    """Missing closing parenthesis"""
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            with caplog.at_level(logging.ERROR):
                result = parse_python_file(temp_path)
            
            # Should have logged the error
            assert len(caplog.records) > 0
            assert any('Syntax error' in record.message for record in caplog.records)
            
            # Should have error in parse_errors
            assert len(result.parse_errors) > 0
            assert 'Syntax error' in result.parse_errors[0]
            
            # Should return empty metadata (since parsing failed)
            # Note: When ast.parse fails, we get no metadata at all
            assert len(result.functions) == 0
            assert len(result.classes) == 0
            
            # But the FileMetadata object should still be returned
            assert result.file_path == temp_path
            assert result.language == 'python'
        finally:
            os.unlink(temp_path)
    
    def test_multiple_error_types_are_handled(self, caplog):
        """Test that different error types are all handled gracefully"""
        import logging
        
        # Test 1: File not found error
        with caplog.at_level(logging.ERROR):
            result1 = parse_python_file('/nonexistent/file.py')
        assert len(result1.parse_errors) > 0
        assert 'File not found' in result1.parse_errors[0]
        
        # Count errors logged so far
        errors_after_test1 = len(caplog.records)
        assert errors_after_test1 >= 1
        
        # Test 2: File with syntax error
        code = 'def broken('
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            with caplog.at_level(logging.ERROR):
                result2 = parse_python_file(temp_path)
            assert len(result2.parse_errors) > 0
            assert 'Syntax error' in result2.parse_errors[0]
        finally:
            os.unlink(temp_path)
        
        # Verify both errors were logged
        errors_after_test2 = len(caplog.records)
        assert errors_after_test2 >= 2
        
        # Verify the log messages contain expected content
        log_messages = [record.message for record in caplog.records]
        assert any('File not found' in msg for msg in log_messages)
        assert any('Syntax error' in msg for msg in log_messages)
