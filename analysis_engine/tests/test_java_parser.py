"""
Unit tests for Java regex-based parser
"""
import pytest
import tempfile
import os
from pathlib import Path
from analysis_engine.parsers.java_parser import parse_java_file
from analysis_engine.models import FileMetadata, ClassMetadata, FunctionMetadata, Parameter


class TestJavaParser:
    """Test suite for Java parser functionality"""
    
    def test_parse_simple_class(self):
        """Test parsing a simple class with methods"""
        code = '''
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    private void reset() {
        // Reset logic
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert result.language == 'java'
            assert len(result.classes) == 1
            assert len(result.functions) == 0
            assert len(result.parse_errors) == 0
            
            cls = result.classes[0]
            assert cls.name == 'Calculator'
            assert len(cls.methods) == 2
            
            # Check add method
            add_method = cls.methods[0]
            assert add_method.name == 'add'
            assert add_method.return_type == 'int'
            assert len(add_method.parameters) == 2
            assert add_method.parameters[0].name == 'a'
            assert add_method.parameters[0].type_hint == 'int'
            assert add_method.parameters[1].name == 'b'
            assert add_method.parameters[1].type_hint == 'int'
            
            # Check reset method
            reset_method = cls.methods[1]
            assert reset_method.name == 'reset'
            assert reset_method.return_type == 'void'
            assert len(reset_method.parameters) == 0
        finally:
            os.unlink(temp_path)
    
    def test_parse_class_with_javadoc(self):
        """Test parsing a class with JavaDoc comments"""
        code = '''
/**
 * A calculator class for basic arithmetic
 * @author Test Author
 */
public class Calculator {
    /**
     * Add two numbers together
     * @param a First number
     * @param b Second number
     * @return The sum
     */
    public int add(int a, int b) {
        return a + b;
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert cls.name == 'Calculator'
            assert cls.docstring is not None
            assert 'calculator class' in cls.docstring.lower()
            
            assert len(cls.methods) == 1
            method = cls.methods[0]
            assert method.name == 'add'
            assert method.docstring is not None
            assert 'Add two numbers' in method.docstring
        finally:
            os.unlink(temp_path)
    
    def test_parse_method_with_generic_types(self):
        """Test parsing methods with generic type parameters"""
        code = '''
public class GenericExample {
    public List<String> getItems(Map<String, Integer> config) {
        return null;
    }
    
    public void processArray(String[] items) {
        // Process items
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert len(cls.methods) == 2
            
            # Check method with generic types
            get_items = cls.methods[0]
            assert get_items.name == 'getItems'
            assert get_items.return_type == 'List<String>'
            assert len(get_items.parameters) == 1
            assert get_items.parameters[0].name == 'config'
            assert get_items.parameters[0].type_hint == 'Map<String, Integer>'
            
            # Check method with array type
            process_array = cls.methods[1]
            assert process_array.name == 'processArray'
            assert len(process_array.parameters) == 1
            assert process_array.parameters[0].name == 'items'
            assert process_array.parameters[0].type_hint == 'String[]'
        finally:
            os.unlink(temp_path)
    
    def test_parse_static_methods(self):
        """Test parsing static methods"""
        code = '''
public class MathUtils {
    public static int add(int a, int b) {
        return a + b;
    }
    
    private static final void initialize() {
        // Initialize
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert len(cls.methods) == 2
            
            # Both methods should be captured regardless of static modifier
            method_names = [m.name for m in cls.methods]
            assert 'add' in method_names
            assert 'initialize' in method_names
        finally:
            os.unlink(temp_path)
    
    def test_parse_method_with_varargs(self):
        """Test parsing methods with varargs (variable arguments)"""
        code = '''
public class VarArgsExample {
    public int sum(int... numbers) {
        int total = 0;
        for (int num : numbers) {
            total += num;
        }
        return total;
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert len(cls.methods) == 1
            
            method = cls.methods[0]
            assert method.name == 'sum'
            assert len(method.parameters) == 1
            assert method.parameters[0].name == 'numbers'
            # Varargs should be captured as int...
            assert 'int' in method.parameters[0].type_hint
        finally:
            os.unlink(temp_path)
    
    def test_parse_constructor_is_excluded(self):
        """Test that constructors are not included in methods list"""
        code = '''
public class Example {
    public Example() {
        // Constructor
    }
    
    public Example(int value) {
        // Parameterized constructor
    }
    
    public void regularMethod() {
        // Regular method
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            # Should only have the regular method, not constructors
            assert len(cls.methods) == 1
            assert cls.methods[0].name == 'regularMethod'
        finally:
            os.unlink(temp_path)
    
    def test_parse_multiple_classes(self):
        """Test parsing multiple classes in one file"""
        code = '''
public class FirstClass {
    public void method1() {
        // Method 1
    }
}

class SecondClass {
    private int method2(String param) {
        return 0;
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 2
            
            class_names = [c.name for c in result.classes]
            assert 'FirstClass' in class_names
            assert 'SecondClass' in class_names
            
            # Check first class
            first_class = next(c for c in result.classes if c.name == 'FirstClass')
            assert len(first_class.methods) == 1
            assert first_class.methods[0].name == 'method1'
            
            # Check second class
            second_class = next(c for c in result.classes if c.name == 'SecondClass')
            assert len(second_class.methods) == 1
            assert second_class.methods[0].name == 'method2'
        finally:
            os.unlink(temp_path)
    
    def test_parse_method_with_single_line_comment(self):
        """Test parsing method with single-line comment"""
        code = '''
public class Example {
    // This method adds two numbers
    // It returns the sum
    public int add(int a, int b) {
        return a + b;
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert len(cls.methods) == 1
            
            method = cls.methods[0]
            assert method.name == 'add'
            assert method.docstring is not None
            assert 'adds two numbers' in method.docstring
            assert 'returns the sum' in method.docstring
        finally:
            os.unlink(temp_path)
    
    def test_parse_method_with_final_parameters(self):
        """Test parsing method with final parameters"""
        code = '''
public class Example {
    public void process(final String input, final int count) {
        // Process with final parameters
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert len(cls.methods) == 1
            
            method = cls.methods[0]
            assert method.name == 'process'
            assert len(method.parameters) == 2
            assert method.parameters[0].name == 'input'
            assert method.parameters[0].type_hint == 'String'
            assert method.parameters[1].name == 'count'
            assert method.parameters[1].type_hint == 'int'
        finally:
            os.unlink(temp_path)
    
    def test_parse_empty_file(self):
        """Test parsing an empty file"""
        code = ''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.functions) == 0
            assert len(result.classes) == 0
            assert len(result.parse_errors) == 0
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_with_only_comments(self):
        """Test parsing a file with only comments"""
        code = '''
// This is a comment
/* This is a multi-line comment */
/**
 * This is a JavaDoc comment
 */
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.functions) == 0
            assert len(result.classes) == 0
            assert len(result.parse_errors) == 0
        finally:
            os.unlink(temp_path)
    
    def test_parse_nonexistent_file(self):
        """Test handling of file not found errors"""
        result = parse_java_file('/nonexistent/path/file.java')
        
        assert len(result.parse_errors) > 0
        assert 'File not found' in result.parse_errors[0]
    
    def test_parse_nonexistent_file_logs_error(self, caplog):
        """Test that file not found errors are logged"""
        import logging
        
        with caplog.at_level(logging.ERROR):
            result = parse_java_file('/nonexistent/path/file.java')
        
        # Verify error was logged
        assert len(caplog.records) > 0
        assert any('File not found' in record.message for record in caplog.records)
        
        # Verify error is in parse_errors
        assert len(result.parse_errors) > 0
        assert 'File not found' in result.parse_errors[0]
    
    def test_parse_class_with_extends_implements(self):
        """Test parsing class with extends and implements clauses"""
        code = '''
public class MyClass extends BaseClass implements Interface1, Interface2 {
    public void method() {
        // Implementation
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert cls.name == 'MyClass'
            assert len(cls.methods) == 1
            assert cls.methods[0].name == 'method'
        finally:
            os.unlink(temp_path)
    
    def test_parse_abstract_class(self):
        """Test parsing abstract class"""
        code = '''
public abstract class AbstractExample {
    public abstract void abstractMethod();
    
    public void concreteMethod() {
        // Concrete implementation
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert cls.name == 'AbstractExample'
            assert len(cls.methods) == 2
            
            method_names = [m.name for m in cls.methods]
            assert 'abstractMethod' in method_names
            assert 'concreteMethod' in method_names
        finally:
            os.unlink(temp_path)
    
    def test_line_numbers_are_captured(self):
        """Test that line numbers are correctly captured"""
        code = '''
public class FirstClass {
    public void method1() {
        // Method 1
    }
}

public class SecondClass {
    public int method2() {
        return 0;
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 2
            
            # First class should have a lower line number than second class
            first_class = result.classes[0]
            second_class = result.classes[1]
            assert first_class.line_number < second_class.line_number
            assert first_class.line_number > 0
            assert second_class.line_number > 0
        finally:
            os.unlink(temp_path)
    
    def test_parse_comprehensive_sample_file(self):
        """Test parsing a comprehensive sample Java file"""
        sample_file = Path(__file__).parent / 'sample_java_file.java'
        
        result = parse_java_file(str(sample_file))
        
        # Verify no parse errors
        assert len(result.parse_errors) == 0
        assert result.language == 'java'
        
        # Should have multiple classes
        assert len(result.classes) >= 3
        class_names = [c.name for c in result.classes]
        assert 'Calculator' in class_names
        assert 'MathUtils' in class_names
        
        # Check Calculator class details
        calc_class = next(c for c in result.classes if c.name == 'Calculator')
        assert calc_class.docstring is not None
        assert 'calculator class' in calc_class.docstring.lower()
        
        # Calculator should have multiple methods
        assert len(calc_class.methods) >= 5
        method_names = [m.name for m in calc_class.methods]
        assert 'add' in method_names
        assert 'subtract' in method_names
        assert 'reset' in method_names
        assert 'sumArray' in method_names
        assert 'processItems' in method_names
        
        # Check add method details
        add_method = next(m for m in calc_class.methods if m.name == 'add')
        assert add_method.return_type == 'int'
        assert len(add_method.parameters) == 2
        assert add_method.parameters[0].name == 'a'
        assert add_method.parameters[0].type_hint == 'int'
        assert add_method.docstring is not None
        assert 'Add two integers' in add_method.docstring
        
        # Check processItems method with generic types
        process_method = next(m for m in calc_class.methods if m.name == 'processItems')
        assert len(process_method.parameters) == 2
        assert 'List<String>' in process_method.parameters[0].type_hint
        assert 'Map<String, Integer>' in process_method.parameters[1].type_hint
        
        # Check MathUtils class
        math_class = next(c for c in result.classes if c.name == 'MathUtils')
        assert len(math_class.methods) >= 2
        math_method_names = [m.name for m in math_class.methods]
        assert 'factorial' in math_method_names
        assert 'max' in math_method_names
    
    def test_parse_method_without_comment(self):
        """Test parsing a method without a comment"""
        code = '''
public class Example {
    public int calculate(int x) {
        return x * 2;
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert len(cls.methods) == 1
            method = cls.methods[0]
            assert method.name == 'calculate'
            assert method.docstring is None
        finally:
            os.unlink(temp_path)
    
    def test_parse_class_without_comment(self):
        """Test parsing a class without a comment"""
        code = '''
public class NoComment {
    public void method() {
        // Implementation
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert cls.name == 'NoComment'
            assert cls.docstring is None
        finally:
            os.unlink(temp_path)
    
    def test_parse_interface(self):
        """Test parsing interface (should be treated like a class)"""
        code = '''
public interface Drawable {
    void draw();
    void setColor(String color);
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            # Interface should be captured as a class
            assert len(result.classes) == 1
            interface = result.classes[0]
            assert interface.name == 'Drawable'
            # Interface methods should be captured
            assert len(interface.methods) == 2
            method_names = [m.name for m in interface.methods]
            assert 'draw' in method_names
            assert 'setColor' in method_names
        finally:
            os.unlink(temp_path)
    
    def test_error_handling_logs_errors(self, caplog):
        """Test that various errors are logged properly"""
        import logging
        
        # Test with permission error simulation (using non-existent file)
        with caplog.at_level(logging.ERROR):
            result = parse_java_file('/nonexistent/path/file.java')
        
        # Verify error was logged
        assert len(caplog.records) > 0
        assert any('File not found' in record.message for record in caplog.records)
        
        # Verify error is in parse_errors
        assert len(result.parse_errors) > 0
        assert 'File not found' in result.parse_errors[0]
        
        # Verify FileMetadata is still returned
        assert result.file_path == '/nonexistent/path/file.java'
        assert result.language == 'java'
        assert len(result.classes) == 0
        assert len(result.functions) == 0
    
    def test_parse_method_with_annotations(self):
        """Test parsing method with annotations (should be stripped)"""
        code = '''
public class AnnotatedExample {
    @Override
    public String toString() {
        return "example";
    }
    
    public void process(@NotNull String input, @Nullable Integer count) {
        // Process with annotations
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        try:
            result = parse_java_file(temp_path)
            
            assert len(result.classes) == 1
            cls = result.classes[0]
            assert len(cls.methods) == 2
            
            # Check toString method
            to_string = cls.methods[0]
            assert to_string.name == 'toString'
            assert to_string.return_type == 'String'
            
            # Check process method - annotations should be stripped from parameters
            process_method = cls.methods[1]
            assert process_method.name == 'process'
            assert len(process_method.parameters) == 2
            assert process_method.parameters[0].name == 'input'
            assert process_method.parameters[0].type_hint == 'String'
            assert process_method.parameters[1].name == 'count'
            assert process_method.parameters[1].type_hint == 'Integer'
        finally:
            os.unlink(temp_path)