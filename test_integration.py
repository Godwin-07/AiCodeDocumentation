#!/usr/bin/env python3
"""
Integration test script to verify the AI Code Documentation Generator works end-to-end.
This simulates what the VS Code extension would do.
"""

import json
import sys
import os
from pathlib import Path

# Add analysis_engine to path
sys.path.insert(0, str(Path(__file__).parent / 'analysis_engine'))

from analysis_engine.main import main

def test_integration():
    """Run an integration test with the test workspace."""
    
    # Prepare test input
    test_input = {
        "workspacePath": str(Path(__file__).parent / "test_workspace"),
        "files": [
            str(Path(__file__).parent / "test_workspace" / "sample_python.py"),
            str(Path(__file__).parent / "test_workspace" / "sample_javascript.js"),
            str(Path(__file__).parent / "test_workspace" / "sample_java.java")
        ],
        "llmEndpoint": "http://localhost:11434/api/chat",
        "llmModel": "llama2:13b",
        "llmTimeout": 30
    }
    
    print("=" * 80)
    print("INTEGRATION TEST: AI Code Documentation Generator")
    print("=" * 80)
    print(f"\nTest workspace: {test_input['workspacePath']}")
    print(f"Files to process: {len(test_input['files'])}")
    for f in test_input['files']:
        print(f"  - {Path(f).name}")
    
    print("\n" + "=" * 80)
    print("Running analysis engine...")
    print("=" * 80 + "\n")
    
    # Simulate stdin input
    import io
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps(test_input))
    
    # Capture stdout
    old_stdout = sys.stdout
    output_buffer = io.StringIO()
    sys.stdout = output_buffer
    
    try:
        # Run main function
        main()
        
        # Get output
        output = output_buffer.getvalue()
        
        # Restore stdout
        sys.stdout = old_stdout
        sys.stdin = old_stdin
        
        # Parse output (skip progress messages, get final JSON)
        lines = output.strip().split('\n')
        result_line = None
        for line in reversed(lines):
            if line.strip().startswith('{'):
                result_line = line
                break
        
        if result_line:
            result = json.loads(result_line)
            
            print("\n" + "=" * 80)
            print("RESULTS")
            print("=" * 80)
            print(f"Success: {result.get('success', False)}")
            print(f"Files processed: {result.get('filesProcessed', 0)}")
            print(f"Files skipped: {result.get('filesSkipped', 0)}")
            print(f"Documentation path: {result.get('documentationPath', 'N/A')}")
            
            if result.get('errors'):
                print(f"\nErrors encountered: {len(result['errors'])}")
                for error in result['errors']:
                    print(f"  - {error}")
            else:
                print("\nNo errors encountered!")
            
            # Check if documentation file was created
            doc_path = Path(test_input['workspacePath']) / 'DOCUMENTATION.md'
            if doc_path.exists():
                print(f"\n✓ Documentation file created: {doc_path}")
                file_size = doc_path.stat().st_size
                print(f"  File size: {file_size:,} bytes")
                
                # Show first few lines
                with open(doc_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:10]
                    print(f"  First 10 lines:")
                    for line in lines:
                        print(f"    {line.rstrip()}")
                
                return True
            else:
                print(f"\n✗ Documentation file NOT created at: {doc_path}")
                return False
        else:
            print("\n✗ Could not parse output from analysis engine")
            print("Raw output:")
            print(output)
            return False
            
    except Exception as e:
        sys.stdout = old_stdout
        sys.stdin = old_stdin
        print(f"\n✗ Integration test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_integration()
    sys.exit(0 if success else 1)
