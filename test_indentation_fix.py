"""
Test script to verify docstring indentation fix
"""

# Simulate the fixed logic
def test_indentation():
    original_code = """def add(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y"""
    
    lines = original_code.split('\n')
    
    # Test function at line 1 (0-indexed: line 0)
    def_line_idx = 0  # "def add(a, b):"
    func_indent = lines[def_line_idx][:len(lines[def_line_idx]) - len(lines[def_line_idx].lstrip())]
    docstring_indent = func_indent + '    '
    
    print(f"Function 'add' at line {def_line_idx + 1}")
    print(f"  Function indent: '{func_indent}' (length: {len(func_indent)})")
    print(f"  Docstring indent: '{docstring_indent}' (length: {len(docstring_indent)})")
    print()
    
    # Test class at line 3 (0-indexed: line 2)
    def_line_idx = 3  # "class Calculator:"
    class_indent = lines[def_line_idx][:len(lines[def_line_idx]) - len(lines[def_line_idx].lstrip())]
    docstring_indent = class_indent + '    '
    
    print(f"Class 'Calculator' at line {def_line_idx + 1}")
    print(f"  Class indent: '{class_indent}' (length: {len(class_indent)})")
    print(f"  Docstring indent: '{docstring_indent}' (length: {len(docstring_indent)})")
    print()
    
    # Test method at line 5 (0-indexed: line 4)
    def_line_idx = 4  # "    def multiply(self, x, y):"
    method_indent = lines[def_line_idx][:len(lines[def_line_idx]) - len(lines[def_line_idx].lstrip())]
    docstring_indent = method_indent + '    '
    
    print(f"Method 'multiply' at line {def_line_idx + 1}")
    print(f"  Method indent: '{method_indent}' (length: {len(method_indent)})")
    print(f"  Docstring indent: '{docstring_indent}' (length: {len(docstring_indent)})")
    print()
    
    # Show expected output
    print("Expected docstring format for function 'add':")
    print('    """')
    print('    This is a docstring')
    print('    """')
    print()
    
    print("Expected docstring format for method 'multiply':")
    print('        """')
    print('        This is a docstring')
    print('        """')

if __name__ == "__main__":
    test_indentation()
