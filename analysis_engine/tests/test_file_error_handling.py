"""
Unit tests for file read error handling (Requirement 10.1)

Tests verify that the analysis engine handles file read errors gracefully:
- PermissionError when file cannot be read
- FileNotFoundError when file doesn't exist
- Processing continues for remaining files after errors
- Errors are logged and collected
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from io import StringIO
from unittest.mock import patch, mock_open

from analysis_engine.main import process_files_sequentially, main
from analysis_engine.parsers.python_parser import parse_python_file
from analysis_engine.parsers.javascript_parser import parse_javascript_file
from analysis_engine.parsers.java_parser import parse_java_file


class TestParserPermissionErrors:
    """Test that parsers handle PermissionError gracefully"""
    
    def test_python_parser_permission_error(self):
        """Test Python parser handles PermissionError and returns metadata with error"""
        # Use a file path that will trigger PermissionError when mocked
        test_file = "/restricted/test.py"
        
        # Mock open to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            metadata = parse_python_file(test_file)
        
        # Should return metadata with error, not raise exception
        assert metadata.file_path == test_file
        assert metadata.language == 'python'
        assert len(metadata.parse_errors) == 1
        assert 'Permission denied' in metadata.parse_errors[0]
        assert len(metadata.classes) == 0
        assert len(metadata.functions) == 0
    
    def test_javascript_parser_permission_error(self):
        """Test JavaScript parser handles PermissionError and returns metadata with error"""
        test_file = "/restricted/test.js"
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            metadata = parse_javascript_file(test_file)
        
        assert metadata.file_path == test_file
        assert metadata.language == 'javascript'
        assert len(metadata.parse_errors) == 1
        assert 'Permission denied' in metadata.parse_errors[0]
        assert len(metadata.classes) == 0
        assert len(metadata.functions) == 0
    
    def test_java_parser_permission_error(self):
        """Test Java parser handles PermissionError and returns metadata with error"""
        test_file = "/restricted/Test.java"
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            metadata = parse_java_file(test_file)
        
        assert metadata.file_path == test_file
        assert metadata.language == 'java'
        assert len(metadata.parse_errors) == 1
        assert 'Permission denied' in metadata.parse_errors[0]
        assert len(metadata.classes) == 0
        assert len(metadata.functions) == 0


class TestParserFileNotFoundErrors:
    """Test that parsers handle FileNotFoundError gracefully"""
    
    def test_python_parser_file_not_found(self):
        """Test Python parser handles FileNotFoundError"""
        test_file = "/nonexistent/test.py"
        
        metadata = parse_python_file(test_file)
        
        assert metadata.file_path == test_file
        assert metadata.language == 'python'
        assert len(metadata.parse_errors) == 1
        assert 'not found' in metadata.parse_errors[0].lower()
        assert len(metadata.classes) == 0
        assert len(metadata.functions) == 0
    
    def test_javascript_parser_file_not_found(self):
        """Test JavaScript parser handles FileNotFoundError"""
        test_file = "/nonexistent/test.js"
        
        metadata = parse_javascript_file(test_file)
        
        assert metadata.file_path == test_file
        assert metadata.language == 'javascript'
        assert len(metadata.parse_errors) == 1
        assert 'not found' in metadata.parse_errors[0].lower()
    
    def test_java_parser_file_not_found(self):
        """Test Java parser handles FileNotFoundError"""
        test_file = "/nonexistent/Test.java"
        
        metadata = parse_java_file(test_file)
        
        assert metadata.file_path == test_file
        assert metadata.language == 'java'
        assert len(metadata.parse_errors) == 1
        assert 'not found' in metadata.parse_errors[0].lower()


class TestProcessFilesWithErrors:
    """Test that process_files_sequentially handles errors and continues processing"""
    
    def test_permission_error_continues_processing(self, tmp_path):
        """Test that PermissionError on one file doesn't stop processing of other files"""
        # Create two valid files
        file1 = tmp_path / "file1.py"
        file1.write_text("def func1():\n    pass\n")
        
        file2 = tmp_path / "file2.py"
        file2.write_text("def func2():\n    pass\n")
        
        # Create a file that will trigger PermissionError
        restricted_file = tmp_path / "restricted.py"
        restricted_file.write_text("def restricted():\n    pass\n")
        
        # Make the file unreadable (Unix-like systems only)
        if sys.platform != 'win32':
            os.chmod(restricted_file, 0o000)
        
        try:
            files = [str(file1), str(restricted_file), str(file2)]
            
            all_metadata, processed, skipped, errors = process_files_sequentially(
                files=files,
                llm_endpoint='http://localhost:11434/api/chat',
                llm_model='llama2',
                llm_timeout=1,
                workspace_path=str(tmp_path)
            )
            
            # On Unix systems, should have processed 2 files and skipped 1
            # On Windows, chmod might not work, so we check more flexibly
            if sys.platform != 'win32':
                assert processed == 2, "Should process files before and after the error"
                assert skipped == 1, "Should skip the restricted file"
                assert len(errors) >= 1, "Should have at least one error"
                
                # Verify the error message mentions permission
                permission_errors = [e for e in errors if 'permission' in e.lower()]
                assert len(permission_errors) >= 1, "Should have permission error"
            
            # All files should have metadata entries (even failed ones)
            assert len(all_metadata) >= 2, "Should have metadata for successfully processed files"
            
        finally:
            # Restore permissions for cleanup
            if sys.platform != 'win32':
                try:
                    os.chmod(restricted_file, 0o644)
                except:
                    pass
    
    def test_file_not_found_continues_processing(self, tmp_path):
        """Test that FileNotFoundError on one file doesn't stop processing of other files"""
        # Create two valid files
        file1 = tmp_path / "file1.py"
        file1.write_text("def func1():\n    pass\n")
        
        file2 = tmp_path / "file2.py"
        file2.write_text("def func2():\n    pass\n")
        
        # Reference a non-existent file
        missing_file = tmp_path / "missing.py"
        
        files = [str(file1), str(missing_file), str(file2)]
        
        all_metadata, processed, skipped, errors = process_files_sequentially(
            files=files,
            llm_endpoint='http://localhost:11434/api/chat',
            llm_model='llama2',
            llm_timeout=1,
            workspace_path=str(tmp_path)
        )
        
        # Should process 2 files successfully and skip 1
        assert processed == 2, "Should process files before and after the missing file"
        assert skipped == 1, "Should skip the missing file"
        
        # Filter for file-not-found errors (ignore LLM errors during testing)
        file_not_found_errors = [e for e in errors if 'not found' in e.lower()]
        assert len(file_not_found_errors) == 1, "Should have one file-not-found error"
        assert 'not found' in file_not_found_errors[0].lower(), "Error should mention file not found"
        
        # Should have metadata for all files (including the failed one)
        assert len(all_metadata) == 3
        
        # Verify the successfully processed files have correct metadata
        successful_metadata = [m for m in all_metadata if not m.parse_errors]
        assert len(successful_metadata) == 2
        assert all(m.language == 'python' for m in successful_metadata)
    
    def test_multiple_errors_all_collected(self, tmp_path):
        """Test that multiple file errors are all collected and processing continues"""
        # Create one valid file
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("def valid_func():\n    pass\n")
        
        # Reference multiple non-existent files
        missing1 = tmp_path / "missing1.py"
        missing2 = tmp_path / "missing2.py"
        missing3 = tmp_path / "missing3.py"
        
        files = [str(missing1), str(valid_file), str(missing2), str(missing3)]
        
        all_metadata, processed, skipped, errors = process_files_sequentially(
            files=files,
            llm_endpoint='http://localhost:11434/api/chat',
            llm_model='llama2',
            llm_timeout=1,
            workspace_path=str(tmp_path)
        )
        
        # Should process 1 file and skip 3
        assert processed == 1, "Should process the one valid file"
        assert skipped == 3, "Should skip all three missing files"
        
        # Filter for file-not-found errors (ignore LLM errors during testing)
        file_not_found_errors = [e for e in errors if 'not found' in e.lower()]
        assert len(file_not_found_errors) == 3, "Should collect all three file-not-found errors"
        
        # All file-not-found errors should mention file not found
        for error in file_not_found_errors:
            assert 'not found' in error.lower()
        
        # Should have metadata for all files
        assert len(all_metadata) == 4
        
        # Verify the valid file was processed correctly
        successful_metadata = [m for m in all_metadata if not m.parse_errors]
        assert len(successful_metadata) == 1
        assert successful_metadata[0].language == 'python'
        assert len(successful_metadata[0].functions) == 1


class TestMainFunctionErrorHandling:
    """Test main function's error handling for file read errors"""
    
    def test_main_with_permission_error(self, tmp_path, monkeypatch):
        """Test main function continues when encountering PermissionError"""
        # Create two valid files
        file1 = tmp_path / "file1.py"
        file1.write_text("def func1():\n    pass\n")
        
        file2 = tmp_path / "file2.py"
        file2.write_text("def func2():\n    pass\n")
        
        # Create a restricted file
        restricted_file = tmp_path / "restricted.py"
        restricted_file.write_text("def restricted():\n    pass\n")
        
        # Make the file unreadable (Unix-like systems only)
        if sys.platform != 'win32':
            os.chmod(restricted_file, 0o000)
        
        try:
            # Prepare input JSON
            input_data = {
                "workspacePath": str(tmp_path),
                "files": [str(file1), str(restricted_file), str(file2)],
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
            
            # Should succeed overall despite the permission error
            assert output['type'] == 'result'
            assert output['success'] is True
            
            # On Unix systems, should have processed 2 and skipped 1
            if sys.platform != 'win32':
                assert output['filesProcessed'] == 2
                assert output['filesSkipped'] == 1
                assert len(output['errors']) >= 1
                
                # Should have permission error in errors list
                permission_errors = [e for e in output['errors'] if 'permission' in e.lower()]
                assert len(permission_errors) >= 1
            
            # Documentation should still be created
            assert 'documentationPath' in output
            doc_path = Path(output['documentationPath'])
            assert doc_path.exists()
            
        finally:
            # Restore permissions for cleanup
            if sys.platform != 'win32':
                try:
                    os.chmod(restricted_file, 0o644)
                except:
                    pass
    
    def test_main_with_missing_files(self, tmp_path, monkeypatch):
        """Test main function continues when encountering FileNotFoundError"""
        # Create one valid file
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("def valid_func():\n    pass\n")
        
        # Reference non-existent files
        missing1 = tmp_path / "missing1.py"
        missing2 = tmp_path / "missing2.py"
        
        # Prepare input JSON
        input_data = {
            "workspacePath": str(tmp_path),
            "files": [str(missing1), str(valid_file), str(missing2)],
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
        
        # Should succeed overall despite missing files
        assert output['type'] == 'result'
        assert output['success'] is True
        assert output['filesProcessed'] == 1
        assert output['filesSkipped'] == 2
        
        # Filter for file-not-found errors (ignore LLM errors during testing)
        file_not_found_errors = [e for e in output['errors'] if 'not found' in e.lower()]
        assert len(file_not_found_errors) == 2, "Should have two file-not-found errors"
        
        # Both file-not-found errors should mention file not found
        for error in file_not_found_errors:
            assert 'not found' in error.lower()
        
        # Documentation should still be created
        assert 'documentationPath' in output
        doc_path = Path(output['documentationPath'])
        assert doc_path.exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
