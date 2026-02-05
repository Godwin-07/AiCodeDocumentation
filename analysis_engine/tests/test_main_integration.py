"""
Integration tests for main.py - end-to-end testing
"""
import json
import sys
import os
from io import StringIO
from pathlib import Path
import pytest


class TestMainIntegration:
    """Integration tests for the complete workflow"""
    
    def test_end_to_end_with_mixed_files(self, tmp_path, monkeypatch):
        """Test complete workflow with Python, JavaScript, and Java files"""
        # Create test files
        py_file = tmp_path / "calculator.py"
        py_file.write_text("""
class Calculator:
    '''A simple calculator class'''
    
    def add(self, a, b):
        '''Add two numbers'''
        return a + b
    
    def subtract(self, a, b):
        '''Subtract b from a'''
        return a - b

def multiply(x, y):
    '''Multiply two numbers'''
    return x * y
""")
        
        js_file = tmp_path / "utils.js"
        js_file.write_text("""
// Utility functions
function formatDate(date) {
    return date.toISOString();
}

const parseJSON = (str) => {
    return JSON.parse(str);
}

class Logger {
    log(message) {
        console.log(message);
    }
}
""")
        
        java_file = tmp_path / "Person.java"
        java_file.write_text("""
/**
 * Represents a person
 */
public class Person {
    private String name;
    private int age;
    
    /**
     * Get the person's name
     */
    public String getName() {
        return name;
    }
    
    /**
     * Set the person's name
     */
    public void setName(String name) {
        this.name = name;
    }
}
""")
        
        # Prepare input JSON
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [str(py_file), str(js_file), str(java_file)],
            "llmEndpoint": "http://localhost:11434/api/chat",
            "llmModel": "llama2",
            "llmTimeout": 1  # Short timeout since LLM won't be available
        }
        
        # Mock stdin
        mock_stdin = StringIO(json.dumps(input_data))
        monkeypatch.setattr('sys.stdin', mock_stdin)
        
        # Mock stdout
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Import and run main
        from analysis_engine.main import main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        # Verify output
        assert output['success'] is True
        assert output['filesProcessed'] == 3
        assert output['filesSkipped'] == 0
        assert 'documentationPath' in output
        
        # Verify DOCUMENTATION.md was created
        doc_path = Path(output['documentationPath'])
        assert doc_path.exists()
        assert doc_path.name == 'DOCUMENTATION.md'
        
        # Read and verify documentation content
        doc_content = doc_path.read_text()
        
        # Check for expected sections
        assert '# Project Documentation' in doc_content
        assert '## Table of Contents' in doc_content
        assert '## Overview' in doc_content
        assert '## Files' in doc_content
        
        # Check for file-specific content
        assert 'calculator.py' in doc_content
        assert 'utils.js' in doc_content
        assert 'Person.java' in doc_content
        
        # Check for class documentation
        assert 'Calculator' in doc_content
        assert 'Logger' in doc_content
        assert 'Person' in doc_content
        
        # Check for function documentation
        assert 'add' in doc_content
        assert 'multiply' in doc_content
        assert 'formatDate' in doc_content
        assert 'getName' in doc_content
        
        # Check for language tags
        assert '**Language:** Python' in doc_content
        assert '**Language:** Javascript' in doc_content
        assert '**Language:** Java' in doc_content
    
    def test_end_to_end_with_parse_errors(self, tmp_path, monkeypatch):
        """Test workflow with files that have parse errors"""
        # Create a valid file
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("def hello():\n    return 'world'\n")
        
        # Create a file with syntax errors
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text("def broken(\n    # Missing closing paren\n")
        
        # Prepare input JSON
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [str(valid_file), str(invalid_file)],
            "llmEndpoint": "http://localhost:11434/api/chat",
            "llmModel": "llama2",
            "llmTimeout": 1
        }
        
        # Mock stdin
        mock_stdin = StringIO(json.dumps(input_data))
        monkeypatch.setattr('sys.stdin', mock_stdin)
        
        # Mock stdout
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Import and run main
        from analysis_engine.main import main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        # Verify output - should still succeed but with errors reported
        assert output['success'] is True
        assert output['filesProcessed'] == 1  # Only the valid file
        assert output['filesSkipped'] == 1  # The invalid file
        assert len(output['errors']) >= 1  # Should have error messages
        
        # Verify DOCUMENTATION.md was still created
        doc_path = Path(output['documentationPath'])
        assert doc_path.exists()
        
        # Read documentation
        doc_content = doc_path.read_text(encoding='utf-8')
        
        # Should document the valid file
        assert 'valid.py' in doc_content
        assert 'hello' in doc_content
        
        # Should also mention the invalid file with errors
        assert 'invalid.py' in doc_content
        assert 'Parse Errors' in doc_content or 'parse_errors' in doc_content.lower()
    
    def test_sequential_processing_order(self, tmp_path, monkeypatch):
        """Test that files are processed sequentially in order"""
        # Create multiple files
        files = []
        for i in range(5):
            file = tmp_path / f"file{i}.py"
            file.write_text(f"def func{i}():\n    pass\n")
            files.append(str(file))
        
        # Prepare input JSON
        input_data = {
            "workspacePath": str(tmp_path),
            "files": files,
            "llmEndpoint": "http://localhost:11434/api/chat",
            "llmModel": "llama2",
            "llmTimeout": 1
        }
        
        # Mock stdin
        mock_stdin = StringIO(json.dumps(input_data))
        monkeypatch.setattr('sys.stdin', mock_stdin)
        
        # Mock stdout
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Import and run main
        from analysis_engine.main import main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        # Verify all files were processed
        assert output['success'] is True
        assert output['filesProcessed'] == 5
        assert output['filesSkipped'] == 0
        
        # Verify documentation was created
        doc_path = Path(output['documentationPath'])
        assert doc_path.exists()
        
        # Read documentation and verify all files are documented
        doc_content = doc_path.read_text()
        for i in range(5):
            assert f'file{i}.py' in doc_content
            assert f'func{i}' in doc_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
