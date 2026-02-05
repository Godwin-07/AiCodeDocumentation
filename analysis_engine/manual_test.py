"""
Manual test script for main.py
"""
import json
import sys
from io import StringIO

# Test input
test_input = {
    "workspacePath": ".",
    "files": [
        "models.py",
        "llm_client.py"
    ],
    "llmEndpoint": "http://localhost:11434/api/chat",
    "llmModel": "llama2",
    "llmTimeout": 2
}

# Mock stdin with test input
sys.stdin = StringIO(json.dumps(test_input))

# Import and run main
from analysis_engine.main import main

print("Running main.py with test input...")
print("=" * 60)

try:
    main()
    print("\n" + "=" * 60)
    print("SUCCESS: main.py executed without errors")
except SystemExit as e:
    if e.code == 0:
        print("\n" + "=" * 60)
        print("SUCCESS: main.py completed successfully")
    else:
        print("\n" + "=" * 60)
        print(f"ERROR: main.py exited with code {e.code}")
except Exception as e:
    print("\n" + "=" * 60)
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
