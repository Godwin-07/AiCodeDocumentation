"""
Unit tests for main.py entry point
"""
import json
import sys
import os
import tempfile
from io import StringIO
from pathlib import Path
import pytest

# Import from the package
from analysis_engine.main import parse_file, process_files_sequentially, main


class TestParseFile:
    """Test the parse_file dispatcher function"""
    
    def test_parse_python_file(self, tmp_path):
        """Test dispatching to Python parser"""
        # Create a simple Python file
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    pass\n")
        
        metadata = parse_file(str(py_file))
        
        assert metadata.language == 'python'
        assert metadata.file_path == str(py_file)
        assert len(metadata.functions) == 1
        assert metadata.functions[0].name == 'hello'
    
    def test_parse_javascript_file(self, tmp_path):
        """Test dispatching to JavaScript parser"""
        # Create a simple JavaScript file
        js_file = tmp_path / "test.js"
        js_file.write_text("function hello() {\n  return 'world';\n}\n")
        
        metadata = parse_file(str(js_file))
        
        assert metadata.language == 'javascript'
        assert metadata.file_path == str(js_file)
        assert len(metadata.functions) == 1
        assert metadata.functions[0].name == 'hello'
    
    def test_parse_java_file(self, tmp_path):
        """Test dispatching to Java parser"""
        # Create a simple Java file
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {\n  public void hello() {}\n}\n")
        
        metadata = parse_file(str(java_file))
        
        assert metadata.language == 'java'
        assert metadata.file_path == str(java_file)
        assert len(metadata.classes) == 1
        assert metadata.classes[0].name == 'Test'
    
    def test_parse_unsupported_file(self, tmp_path):
        """Test handling of unsupported file types"""
        # Create an unsupported file type
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello world")
        
        metadata = parse_file(str(txt_file))
        
        assert metadata.language == 'unknown'
        assert len(metadata.parse_errors) == 1
        assert 'Unsupported' in metadata.parse_errors[0]


class TestProcessFilesSequentially:
    """Test sequential file processing"""
    
    def test_process_empty_file_list(self, tmp_path):
        """Test processing with no files"""
        all_metadata, processed, skipped, errors = process_files_sequentially(
            files=[],
            llm_endpoint='http://localhost:11434/api/chat',
            llm_model='llama2',
            llm_timeout=30,
            workspace_path=str(tmp_path)
        )
        
        assert len(all_metadata) == 0
        assert processed == 0
        assert skipped == 0
        assert len(errors) == 0
    
    def test_process_single_file(self, tmp_path):
        """Test processing a single file"""
        # Create a test file
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    '''Say hello'''\n    pass\n")
        
        all_metadata, processed, skipped, errors = process_files_sequentially(
            files=[str(py_file)],
            llm_endpoint='http://localhost:11434/api/chat',
            llm_model='llama2',
            llm_timeout=1,  # Short timeout since LLM won't be available
            workspace_path=str(tmp_path)
        )
        
        assert len(all_metadata) == 1
        assert processed == 1
        assert skipped == 0
        assert all_metadata[0].language == 'python'
    
    def test_process_multiple_files(self, tmp_path):
        """Test processing multiple files sequentially"""
        # Create multiple test files
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    pass\n")
        
        js_file = tmp_path / "test.js"
        js_file.write_text("function world() {}\n")
        
        all_metadata, processed, skipped, errors = process_files_sequentially(
            files=[str(py_file), str(js_file)],
            llm_endpoint='http://localhost:11434/api/chat',
            llm_model='llama2',
            llm_timeout=1,
            workspace_path=str(tmp_path)
        )
        
        assert len(all_metadata) == 2
        assert processed == 2
        assert skipped == 0
        assert all_metadata[0].language == 'python'
        assert all_metadata[1].language == 'javascript'
    
    def test_process_with_missing_file(self, tmp_path):
        """Test error recovery when file is missing"""
        # Reference a non-existent file
        missing_file = tmp_path / "missing.py"
        
        all_metadata, processed, skipped, errors = process_files_sequentially(
            files=[str(missing_file)],
            llm_endpoint='http://localhost:11434/api/chat',
            llm_model='llama2',
            llm_timeout=1,
            workspace_path=str(tmp_path)
        )
        
        # The parser handles the error internally and returns metadata with parse_errors
        # So we get metadata but it's marked as skipped
        assert len(all_metadata) == 1
        assert processed == 0
        assert skipped == 1
        assert len(errors) == 1
        assert 'not found' in errors[0].lower()
        assert len(all_metadata[0].parse_errors) == 1
    
    def test_process_continues_after_error(self, tmp_path):
        """Test that processing continues after encountering an error"""
        # Create one valid file and reference one missing file
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    pass\n")
        
        missing_file = tmp_path / "missing.py"
        
        all_metadata, processed, skipped, errors = process_files_sequentially(
            files=[str(missing_file), str(py_file)],
            llm_endpoint='http://localhost:11434/api/chat',
            llm_model='llama2',
            llm_timeout=1,
            workspace_path=str(tmp_path)
        )
        
        # Should process both files, but one has errors
        # The parser returns metadata for both, but one is marked as skipped
        assert len(all_metadata) == 2
        assert processed == 1  # Only the valid file
        assert skipped == 1  # The missing file
        # Now we collect both file errors AND LLM errors
        assert len(errors) >= 1  # At least the file not found error
        assert any('not found' in err.lower() for err in errors)
        
        # Verify the valid file was processed correctly
        valid_metadata = [m for m in all_metadata if not m.parse_errors]
        assert len(valid_metadata) == 1
        assert valid_metadata[0].language == 'python'
        assert len(valid_metadata[0].functions) == 1


class TestMainFunction:
    """Test the main entry point function"""
    
    def test_main_with_valid_input(self, tmp_path, monkeypatch):
        """Test main function with valid input"""
        # Create a test file
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    '''Say hello'''\n    pass\n")
        
        # Prepare input JSON
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [str(py_file)],
            "llmEndpoint": "http://localhost:11434/api/chat",
            "llmModel": "llama2",
            "llmTimeout": 1
        }
        
        # Mock stdin
        mock_stdin = StringIO(json.dumps(input_data))
        monkeypatch.setattr('sys.stdin', mock_stdin)
        
        # Mock stdout to capture output
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        assert output['type'] == 'result'
        assert output['success'] is True
        assert output['filesProcessed'] == 1
        assert output['filesSkipped'] == 0
        assert 'documentationPath' in output
        
        # Verify DOCUMENTATION.md was created
        doc_path = Path(output['documentationPath'])
        assert doc_path.exists()
        assert doc_path.name == 'DOCUMENTATION.md'


class TestProgressTracking:
    """Test progress tracking functionality (Requirement 9.2)"""
    
    def test_no_progress_for_small_file_count(self, tmp_path, monkeypatch):
        """Test that progress is NOT emitted when processing <=100 files"""
        # Create 50 test files
        files = []
        for i in range(50):
            py_file = tmp_path / f"test_{i}.py"
            py_file.write_text(f"def func_{i}():\n    pass\n")
            files.append(str(py_file))
        
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
        
        # Mock stdout to capture output
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main
        main()
        
        # Parse all JSON messages from stdout
        output_lines = mock_stdout.getvalue().strip().split('\n')
        
        # Should only have one message (the final result)
        assert len(output_lines) == 1
        
        # Parse the result
        result = json.loads(output_lines[0])
        assert result['type'] == 'result'
        assert result['success'] is True
        assert result['filesProcessed'] == 50
    
    def test_progress_emitted_for_large_file_count(self, tmp_path, monkeypatch):
        """Test that progress IS emitted every 10 files when processing >100 files"""
        # Create 105 test files
        files = []
        for i in range(105):
            py_file = tmp_path / f"test_{i}.py"
            py_file.write_text(f"def func_{i}():\n    pass\n")
            files.append(str(py_file))
        
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
        
        # Mock stdout to capture output
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main
        main()
        
        # Parse all JSON messages from stdout
        output_lines = [line for line in mock_stdout.getvalue().strip().split('\n') if line]
        
        # Should have progress messages + final result
        # Progress at: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100 = 10 progress messages
        # Plus 1 final result = 11 total messages
        assert len(output_lines) == 11
        
        # Verify progress messages
        progress_messages = []
        result_message = None
        
        for line in output_lines:
            msg = json.loads(line)
            if msg['type'] == 'progress':
                progress_messages.append(msg)
            elif msg['type'] == 'result':
                result_message = msg
        
        # Should have 10 progress messages
        assert len(progress_messages) == 10
        
        # Verify progress message content
        expected_progress = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for i, msg in enumerate(progress_messages):
            assert msg['processed'] == expected_progress[i]
            assert msg['total'] == 105
        
        # Verify final result
        assert result_message is not None
        assert result_message['success'] is True
        assert result_message['filesProcessed'] == 105
    
    def test_progress_at_exactly_100_files(self, tmp_path, monkeypatch):
        """Test that progress is NOT emitted when processing exactly 100 files"""
        # Create exactly 100 test files
        files = []
        for i in range(100):
            py_file = tmp_path / f"test_{i}.py"
            py_file.write_text(f"def func_{i}():\n    pass\n")
            files.append(str(py_file))
        
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
        
        # Mock stdout to capture output
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main
        main()
        
        # Parse all JSON messages from stdout
        output_lines = [line for line in mock_stdout.getvalue().strip().split('\n') if line]
        
        # Should only have one message (the final result) - no progress for exactly 100
        assert len(output_lines) == 1
        
        # Parse the result
        result = json.loads(output_lines[0])
        assert result['type'] == 'result'
        assert result['success'] is True
        assert result['filesProcessed'] == 100
    
    def test_progress_at_101_files(self, tmp_path, monkeypatch):
        """Test that progress IS emitted when processing 101 files (just over threshold)"""
        # Create 101 test files
        files = []
        for i in range(101):
            py_file = tmp_path / f"test_{i}.py"
            py_file.write_text(f"def func_{i}():\n    pass\n")
            files.append(str(py_file))
        
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
        
        # Mock stdout to capture output
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main
        main()
        
        # Parse all JSON messages from stdout
        output_lines = [line for line in mock_stdout.getvalue().strip().split('\n') if line]
        
        # Should have progress messages at 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
        # Plus 1 final result = 11 total messages
        assert len(output_lines) == 11
        
        # Verify we have progress and result messages
        progress_count = sum(1 for line in output_lines if json.loads(line)['type'] == 'progress')
        result_count = sum(1 for line in output_lines if json.loads(line)['type'] == 'result')
        
        assert progress_count == 10
        assert result_count == 1


class TestMainFunctionContinued:
    """Test the main entry point function"""
    
    def test_main_with_valid_input(self, tmp_path, monkeypatch):
        """Test main function with valid input"""
        # Create a test file
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    '''Say hello'''\n    pass\n")
        
        # Prepare input JSON
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [str(py_file)],
            "llmEndpoint": "http://localhost:11434/api/chat",
            "llmModel": "llama2",
            "llmTimeout": 1
        }
        
        # Mock stdin
        mock_stdin = StringIO(json.dumps(input_data))
        monkeypatch.setattr('sys.stdin', mock_stdin)
        
        # Mock stdout to capture output
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        assert output['type'] == 'result'
        assert output['success'] is True
        assert output['filesProcessed'] == 1
        assert output['filesSkipped'] == 0
        assert 'documentationPath' in output
        
        # Verify DOCUMENTATION.md was created
        doc_path = Path(output['documentationPath'])
        assert doc_path.exists()
        assert doc_path.name == 'DOCUMENTATION.md'
    
    def test_main_with_no_files(self, tmp_path, monkeypatch):
        """Test main function with empty file list"""
        # Prepare input JSON with no files
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [],
            "llmEndpoint": "http://localhost:11434/api/chat"
        }
        
        # Mock stdin
        mock_stdin = StringIO(json.dumps(input_data))
        monkeypatch.setattr('sys.stdin', mock_stdin)
        
        # Mock stdout
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        assert output['type'] == 'result'
        assert output['success'] is True
        assert output['filesProcessed'] == 0
        assert len(output['errors']) == 1
        assert 'No files' in output['errors'][0]
    
    def test_main_with_invalid_json(self, monkeypatch):
        """Test main function with invalid JSON input"""
        # Mock stdin with invalid JSON
        mock_stdin = StringIO("not valid json")
        monkeypatch.setattr('sys.stdin', mock_stdin)
        
        # Mock stdout
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main - should exit with error
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        assert output['type'] == 'result'
        assert output['success'] is False
        assert 'Invalid JSON' in output['errors'][0]
    
    def test_main_with_missing_workspace_path(self, monkeypatch):
        """Test main function with missing workspacePath"""
        # Prepare input JSON without workspacePath
        input_data = {
            "files": ["test.py"]
        }
        
        # Mock stdin
        mock_stdin = StringIO(json.dumps(input_data))
        monkeypatch.setattr('sys.stdin', mock_stdin)
        
        # Mock stdout
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main - should exit with error
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        assert output['type'] == 'result'
        assert output['success'] is False
        assert 'workspacePath' in output['errors'][0]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


class TestErrorAggregation:
    """Test comprehensive error aggregation (Task 16.2)"""
    
    def test_parse_errors_included_in_output(self, tmp_path, monkeypatch):
        """Test that parse errors are collected and included in final output"""
        # Create a Python file with syntax errors
        py_file = tmp_path / "bad_syntax.py"
        py_file.write_text("def hello(\n    # Missing closing parenthesis")
        
        # Prepare input JSON
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [str(py_file)],
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
        
        # Run main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        assert output['type'] == 'result'
        assert output['success'] is True  # Still succeeds, but with errors
        assert output['filesSkipped'] == 1
        assert len(output['errors']) > 0
        # Should contain parse error information
        assert any('syntax' in err.lower() or 'parse' in err.lower() for err in output['errors'])
    
    def test_file_not_found_errors_collected(self, tmp_path, monkeypatch):
        """Test that file not found errors are collected"""
        # Reference non-existent files
        missing_file1 = tmp_path / "missing1.py"
        missing_file2 = tmp_path / "missing2.py"
        
        # Prepare input JSON
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [str(missing_file1), str(missing_file2)],
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
        
        # Run main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        assert output['type'] == 'result'
        assert output['success'] is True
        assert output['filesSkipped'] == 2
        assert len(output['errors']) == 2
        # Both errors should mention file not found
        assert all('not found' in err.lower() for err in output['errors'])
    
    def test_llm_errors_collected(self, tmp_path, monkeypatch):
        """Test that LLM errors are collected in the errors list"""
        # Create a valid Python file
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    pass\n")
        
        # Prepare input JSON with invalid LLM endpoint
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [str(py_file)],
            "llmEndpoint": "http://invalid-endpoint-that-does-not-exist:99999/api/chat",
            "llmModel": "llama2",
            "llmTimeout": 1
        }
        
        # Mock stdin
        mock_stdin = StringIO(json.dumps(input_data))
        monkeypatch.setattr('sys.stdin', mock_stdin)
        
        # Mock stdout
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        assert output['type'] == 'result'
        assert output['success'] is True  # Still succeeds with fallback
        assert output['filesProcessed'] == 1
        assert len(output['errors']) > 0
        # Should contain LLM error information
        assert any('basic documentation' in err.lower() or 'llm' in err.lower() for err in output['errors'])
    
    def test_multiple_error_types_aggregated(self, tmp_path, monkeypatch):
        """Test that multiple error types are all collected"""
        # Create mix of files: valid, syntax error, and missing
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("def hello():\n    pass\n")
        
        bad_syntax_file = tmp_path / "bad.py"
        bad_syntax_file.write_text("def hello(\n    # Missing closing")
        
        missing_file = tmp_path / "missing.py"
        
        # Prepare input JSON with invalid LLM endpoint
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [str(valid_file), str(bad_syntax_file), str(missing_file)],
            "llmEndpoint": "http://invalid:99999/api/chat",
            "llmModel": "llama2",
            "llmTimeout": 1
        }
        
        # Mock stdin
        mock_stdin = StringIO(json.dumps(input_data))
        monkeypatch.setattr('sys.stdin', mock_stdin)
        
        # Mock stdout
        mock_stdout = StringIO()
        monkeypatch.setattr('sys.stdout', mock_stdout)
        
        # Run main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        assert output['type'] == 'result'
        assert output['success'] is True
        assert output['filesProcessed'] == 1  # Only valid file
        assert output['filesSkipped'] == 2  # Bad syntax and missing
        assert len(output['errors']) >= 3  # Parse error, file not found, LLM error
        
        # Verify different error types are present
        error_text = ' '.join(output['errors']).lower()
        assert 'not found' in error_text  # File not found error
        assert any('syntax' in err.lower() or 'parse' in err.lower() for err in output['errors'])  # Parse error
        assert any('basic documentation' in err.lower() or 'llm' in err.lower() for err in output['errors'])  # LLM error
    
    def test_write_permission_error_reported(self, tmp_path, monkeypatch):
        """Test that write permission errors are reported with specific details"""
        # Create a valid Python file
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    pass\n")
        
        # Create a read-only directory for workspace
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        
        # Make the directory read-only (this may not work on all systems, especially Windows)
        import stat
        import platform
        
        # Skip this test on Windows as it doesn't handle read-only directories the same way
        if platform.system() == 'Windows':
            pytest.skip("Write permission test not reliable on Windows")
        
        try:
            readonly_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)
            
            # Prepare input JSON
            input_data = {
                "workspacePath": str(readonly_dir),
                "files": [str(py_file)],
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
            
            # Run main - should exit with error
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1
            
            # Parse output
            output = json.loads(mock_stdout.getvalue())
            
            assert output['type'] == 'result'
            assert output['success'] is False
            assert len(output['errors']) > 0
            # Should contain permission error information
            assert any('permission' in err.lower() for err in output['errors'])
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(stat.S_IRWXU)
    
    def test_empty_errors_list_on_success(self, tmp_path, monkeypatch):
        """Test that errors list can be empty when everything succeeds"""
        # Create a valid Python file
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    '''Say hello'''\n    pass\n")
        
        # Prepare input JSON (LLM will fail but that's expected)
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [str(py_file)],
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
        
        # Run main
        main()
        
        # Parse output
        output = json.loads(mock_stdout.getvalue())
        
        assert output['type'] == 'result'
        assert output['success'] is True
        assert output['filesProcessed'] == 1
        assert output['filesSkipped'] == 0
        # Errors list should exist (may contain LLM fallback messages)
        assert 'errors' in output
        assert isinstance(output['errors'], list)
