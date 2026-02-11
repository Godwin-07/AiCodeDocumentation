# Setup Guide - AI Code Documentation Generator

Complete step-by-step guide to set up the extension after cloning from GitHub.

---

## Prerequisites

Before you begin, ensure you have the following installed:

### 1. Install Node.js and npm
- **Download**: https://nodejs.org/ (LTS version recommended)
- **Verify installation**:
  ```bash
  node --version    # Should show v16.0.0 or higher
  npm --version     # Should show 8.0.0 or higher
  ```

### 2. Install Python
- **Download**: https://www.python.org/downloads/ (Python 3.8 or higher)
- **Important**: Check "Add Python to PATH" during installation
- **Verify installation**:
  ```bash
  python --version  # Should show Python 3.8.0 or higher
  pip --version     # Should show pip version
  ```

### 3. Install Ollama (LLM Server)
- **Download**: https://ollama.ai/
- **Install** and it will run automatically in the background
- **Verify installation**:
  ```bash
  ollama --version  # Should show ollama version
  ```

### 4. Install VS Code
- **Download**: https://code.visualstudio.com/
- Version 1.80.0 or higher required

---

## Step-by-Step Setup

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone <your-repo-url>

# Navigate to the project directory
cd AiCodeDocumentation
```

### Step 2: Install Ollama Model

```bash
# Pull the recommended model (codellama:7b - 6GB VRAM)
ollama pull codellama:7b

# OR pull llama2:7b if you prefer
ollama pull llama2:7b

# Verify the model is installed
ollama list
```

**Expected output:**
```
NAME              ID              SIZE      MODIFIED
codellama:7b      8fdf8f752f6e    3.8 GB    2 minutes ago
```

### Step 3: Install Extension Dependencies

```bash
# Navigate to extension directory
cd extension

# Install npm packages
npm install

# Compile TypeScript to JavaScript
npm run compile
```

**Expected output:**
```
> ai-code-doc-generator@0.1.0 compile
> tsc -p ./

Exit Code: 0
```

### Step 4: Install Python Dependencies

```bash
# Navigate to analysis_engine directory (from project root)
cd ../analysis_engine

# Install Python packages
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed requests-2.31.0 ...
```

### Step 5: Verify Python Installation

```bash
# Test the Python engine (from analysis_engine directory)
python main.py

# It should wait for input (press Ctrl+C to exit)
# This confirms Python can run the script
```

### Step 6: Open Project in VS Code

```bash
# From project root directory
code .
```

### Step 7: Launch Extension Development Host

1. **Open the project** in VS Code
2. **Press F5** (or Run → Start Debugging)
3. A new VS Code window will open titled **"[Extension Development Host]"**
4. This is where you'll test the extension

### Step 8: Test the Extension

#### Test 1: Workspace Documentation

1. In the Extension Development Host window, open a folder with code files
2. Press **Ctrl+Shift+P** (Cmd+Shift+P on Mac)
3. Type: **"Generate Code Documentation"**
4. Press Enter
5. Wait for processing (you'll see progress notifications)
6. Check for `DOCUMENTATION.md` in your workspace root

#### Test 2: Single File Documentation

1. Open any `.py`, `.js`, or `.java` file
2. Press **Ctrl+Shift+P**
3. Type: **"Generate Documentation for Current File"**
4. Press Enter
5. Check for `<filename>_DOCUMENTATION.md` in the same directory

#### Test 3: Add Docstrings

1. Open a Python file without docstrings
2. Press **Ctrl+Shift+P**
3. Type: **"Add AI Docstrings to Current File"**
4. Confirm the action
5. Check that docstrings were added to your functions/classes
6. A backup file (`.backup`) should be created

---

## Configuration (Optional)

### Configure LLM Settings

1. In VS Code, go to **File → Preferences → Settings** (Ctrl+,)
2. Search for: **"AI Code Doc Generator"**
3. Configure:
   - **LLM Endpoint**: `http://localhost:11434/api/chat` (default)
   - **LLM Model**: `codellama:7b` (or your preferred model)
   - **LLM Timeout**: `120` seconds (increase if you get timeouts)

### Create .docignore.txt (Optional)

In your workspace root, create `.docignore.txt` to exclude files:

```
# Node modules
node_modules/

# Build outputs
build/
dist/
out/

# Python cache
__pycache__/
*.pyc

# Test files
*.test.js
*.test.py

# Documentation
*.md
```

---

## Troubleshooting

### Issue 1: "Python was not found"

**Solution:**
1. Install Python from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart VS Code
4. Verify: `python --version`

### Issue 2: "npm: command not found"

**Solution:**
1. Install Node.js from https://nodejs.org/
2. Restart your terminal/VS Code
3. Verify: `npm --version`

### Issue 3: "LLM timeout" errors

**Solution:**
1. Check Ollama is running: `ollama list`
2. Increase timeout in VS Code settings: `"aiCodeDocGenerator.llmTimeout": 180`
3. Use a smaller model: `"aiCodeDocGenerator.llmModel": "codellama:7b"`

### Issue 4: Extension doesn't appear in Command Palette

**Solution:**
1. Make sure you compiled TypeScript: `cd extension && npm run compile`
2. Close and reopen the Extension Development Host (press F5 again)
3. Check the Debug Console for errors

### Issue 5: "Module not found" errors in Python

**Solution:**
```bash
cd analysis_engine
pip install -r requirements.txt --force-reinstall
```

### Issue 6: Indentation errors after adding docstrings

**Solution:**
1. Check your source file has consistent indentation before running
2. Use the backup file (`.backup`) to restore if needed
3. Ensure you're using spaces (not tabs) for Python files

---

## Running Tests (Optional)

### Extension Tests

```bash
cd extension
npm test
```

### Python Tests

```bash
cd analysis_engine
pytest
```

### With Coverage

```bash
cd analysis_engine
pytest --cov=.
```

---

## Development Workflow

### Making Changes to Extension (TypeScript)

1. Edit files in `extension/src/`
2. Compile: `npm run compile`
3. Restart Extension Development Host (press F5)
4. Test your changes

### Making Changes to Python Engine

1. Edit files in `analysis_engine/`
2. No compilation needed (Python is interpreted)
3. Restart Extension Development Host (press F5)
4. Test your changes

### Watch Mode (Auto-compile on save)

```bash
cd extension
npm run watch
```

This will automatically recompile TypeScript when you save files.

---

## Quick Reference Commands

```bash
# Setup
git clone <repo-url>
cd AiCodeDocumentation
ollama pull codellama:7b
cd extension && npm install && npm run compile
cd ../analysis_engine && pip install -r requirements.txt

# Development
code .                    # Open in VS Code
# Press F5                # Launch Extension Development Host

# Testing
cd extension && npm test
cd analysis_engine && pytest

# Rebuild
cd extension && npm run compile
```

---

## System Requirements

### Minimum
- CPU: Dual-core processor
- RAM: 8GB
- Storage: 10GB free space
- GPU: Not required (CPU mode works)

### Recommended
- CPU: Quad-core (Ryzen 5 / Intel i5 or better)
- RAM: 16GB
- Storage: 20GB free space
- GPU: 6GB VRAM (for faster LLM inference)

---

## Next Steps

1. ✅ Complete all setup steps above
2. ✅ Test all three features (workspace docs, single file, add docstrings)
3. ✅ Configure settings to your preference
4. ✅ Create `.docignore.txt` for your projects
5. 🚀 Start generating documentation!

---

## Getting Help

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Check the Debug Console in VS Code (View → Debug Console)
3. Check Ollama logs: `ollama logs`
4. Open an issue on GitHub with:
   - Your OS and versions (Python, Node.js, VS Code)
   - Error messages
   - Steps to reproduce

---

## Success Checklist

- [ ] Node.js and npm installed
- [ ] Python 3.8+ installed
- [ ] Ollama installed and running
- [ ] Model downloaded (`ollama pull codellama:7b`)
- [ ] Extension dependencies installed (`npm install`)
- [ ] TypeScript compiled (`npm run compile`)
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Extension launches in Development Host (F5)
- [ ] All three commands work in Command Palette
- [ ] Documentation generated successfully

If all items are checked, you're ready to go! 🎉
