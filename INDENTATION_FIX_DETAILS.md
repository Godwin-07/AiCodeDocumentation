# Indentation Fix - Detailed Explanation

## The Problem

When adding docstrings to Python code, the indentation was completely wrong:

```python
# BEFORE (WRONG):
def add(a, b):
"""  # <-- No indentation!
Docstring text
"""
    return a + b
```

This caused Python `IndentationError` because docstrings must be indented to match the function body.

## Root Cause

The original code had two issues:

1. **Wrong insertion point**: Inserting at `line_number` (the `def` line) instead of `line_number + 1` (after the `def` line)
2. **Wrong indentation calculation**: Using the `def` line's indentation + 4 spaces, but not accounting for 0-indexed vs 1-indexed line numbers

## The Fix

### 1. Correct Line Number Handling

```python
# Parser gives 1-indexed line numbers (line 1, 2, 3...)
# Python lists are 0-indexed (index 0, 1, 2...)

def_line_idx = func.line_number - 1  # Convert to 0-indexed

# Insert AFTER the def line
insertions.append((def_line_idx + 1, formatted_docstring))
```

### 2. Correct Indentation Calculation

```python
# Get indentation of the def line
func_indent = _get_indent(lines, def_line_idx)

# Docstring should be indented one level MORE than the def
docstring_indent = func_indent + '    '  # Add 4 spaces

# Format with correct indentation
formatted_docstring = _format_docstring(
    docstrings[key], docstring_indent, metadata.language
)
```

### 3. Example

For this code:
```python
def add(a, b):
    return a + b
```

- Line 1 (index 0): `def add(a, b):`
  - Function indent: `''` (0 spaces)
  - Docstring indent: `'    '` (4 spaces)
  - Insert at index 1 (after the def line)

Result:
```python
def add(a, b):
    """
    Adds two numbers together.
    """
    return a + b
```

For this code:
```python
class Calculator:
    def multiply(self, x, y):
        return x * y
```

- Line 2 (index 1): `    def multiply(self, x, y):`
  - Method indent: `'    '` (4 spaces)
  - Docstring indent: `'        '` (8 spaces)
  - Insert at index 2 (after the def line)

Result:
```python
class Calculator:
    def multiply(self, x, y):
        """
        Multiplies two numbers together.
        """
        return x * y
```

## Testing

Run the test script to verify:
```bash
python test_indentation_fix.py
```

Expected output:
```
Function 'add' at line 1
  Function indent: '' (length: 0)
  Docstring indent: '    ' (length: 4)

Method 'multiply' at line 5
  Method indent: '    ' (length: 4)
  Docstring indent: '        ' (length: 8)
```

## Files Modified

- `analysis_engine/docstring_generator.py`
  - Fixed `_insert_docstrings()` function
  - Corrected line number indexing (1-indexed → 0-indexed)
  - Fixed insertion point (insert AFTER def line, not AT def line)
  - Fixed indentation calculation (def indent + 4 spaces)

## Try It Now

1. Press F5 to launch Extension Development Host
2. Open `test_docstring_sample.py`
3. Run: "Add AI Docstrings to Current File"
4. Verify: No indentation errors!
