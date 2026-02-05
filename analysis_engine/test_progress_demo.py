"""
Demo script to test progress tracking functionality.
Creates a temporary workspace with 105 files and processes them to show progress updates.
"""
import json
import sys
import tempfile
from pathlib import Path
import subprocess

def create_test_workspace(num_files: int) -> Path:
    """Create a temporary workspace with test files"""
    temp_dir = Path(tempfile.mkdtemp())
    
    for i in range(num_files):
        py_file = temp_dir / f"test_{i}.py"
        py_file.write_text(f"""
def function_{i}():
    '''Function number {i}'''
    return {i}
""")
    
    return temp_dir

def main():
    print("Creating test workspace with 105 files...")
    workspace = create_test_workspace(105)
    
    # Get list of all files
    files = [str(f) for f in workspace.glob("*.py")]
    
    print(f"Created {len(files)} files in {workspace}")
    print("\nRunning analysis engine with progress tracking...\n")
    
    # Prepare input for the analysis engine
    input_data = {
        "workspacePath": str(workspace),
        "files": files,
        "llmEndpoint": "http://localhost:11434/api/chat",
        "llmModel": "llama2",
        "llmTimeout": 1
    }
    
    # Run the analysis engine
    process = subprocess.Popen(
        [sys.executable, "-m", "analysis_engine.main"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send input and get output
    stdout, stderr = process.communicate(input=json.dumps(input_data))
    
    # Parse and display output
    print("=" * 60)
    print("STDOUT OUTPUT:")
    print("=" * 60)
    
    for line in stdout.strip().split('\n'):
        if line:
            msg = json.loads(line)
            if msg['type'] == 'progress':
                print(f"PROGRESS: {msg['processed']}/{msg['total']} files processed")
            elif msg['type'] == 'result':
                print(f"\nFINAL RESULT:")
                print(f"  Success: {msg['success']}")
                print(f"  Files Processed: {msg['filesProcessed']}")
                print(f"  Files Skipped: {msg['filesSkipped']}")
                if msg.get('documentationPath'):
                    print(f"  Documentation: {msg['documentationPath']}")
    
    print("\n" + "=" * 60)
    print("STDERR OUTPUT (logs):")
    print("=" * 60)
    print(stderr[:500] + "..." if len(stderr) > 500 else stderr)
    
    # Cleanup
    import shutil
    shutil.rmtree(workspace)
    print(f"\nCleaned up temporary workspace: {workspace}")

if __name__ == "__main__":
    main()
