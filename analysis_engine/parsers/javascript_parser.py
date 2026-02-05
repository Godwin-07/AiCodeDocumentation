"""
JavaScript regex-based parser for extracting code metadata
"""
import re
import logging
from typing import List, Optional
from ..models import FileMetadata, ClassMetadata, FunctionMetadata, Parameter

# Configure logger for this module
logger = logging.getLogger(__name__)


def _extract_comment_block(lines: List[str], line_index: int) -> Optional[str]:
    """
    Extract comment block immediately preceding a function or class.
    
    Looks for:
    - Single-line comments (//)
    - Multi-line comments (/* ... */)
    - JSDoc comments (/** ... */)
    
    Args:
        lines: List of source code lines
        line_index: Index of the function/class definition line
        
    Returns:
        Extracted comment text or None if no comment found
    """
    if line_index <= 0:
        return None
    
    comments = []
    i = line_index - 1
    
    # Skip empty lines
    while i >= 0 and lines[i].strip() == '':
        i -= 1
    
    if i < 0:
        return None
    
    # Check for multi-line comment ending just before the definition
    if lines[i].strip().endswith('*/'):
        # Find the start of the multi-line comment
        end_index = i
        while i >= 0:
            line = lines[i].strip()
            if line.startswith('/*') or line.startswith('/**'):
                # Extract the comment block
                comment_lines = lines[i:end_index + 1]
                comment_text = '\n'.join(comment_lines)
                # Remove comment markers
                comment_text = re.sub(r'/\*\*?', '', comment_text)
                comment_text = re.sub(r'\*/', '', comment_text)
                comment_text = re.sub(r'^\s*\*\s?', '', comment_text, flags=re.MULTILINE)
                return comment_text.strip()
            i -= 1
        return None
    
    # Check for single-line comments
    while i >= 0:
        line = lines[i].strip()
        if line.startswith('//'):
            # Remove the // prefix
            comment_line = line[2:].strip()
            comments.insert(0, comment_line)
            i -= 1
        elif line == '':
            # Skip empty lines between comments
            i -= 1
        else:
            # Stop when we hit non-comment content
            break
    
    if comments:
        return '\n'.join(comments)
    
    return None


def _parse_parameters(param_string: str) -> List[Parameter]:
    """
    Parse parameter string into Parameter objects.
    
    Handles:
    - Simple parameters: (a, b, c)
    - Default values: (a, b = 10, c = "hello")
    - Destructuring: ({x, y}, [a, b])
    - Rest parameters: (...args)
    
    Args:
        param_string: String containing parameter list
        
    Returns:
        List of Parameter objects
    """
    if not param_string or param_string.strip() == '':
        return []
    
    parameters = []
    
    # Split by comma, but be careful with nested structures
    # Simple approach: split by comma and handle each part
    parts = []
    current = ''
    depth = 0
    
    for char in param_string:
        if char in '({[':
            depth += 1
            current += char
        elif char in ')}]':
            depth -= 1
            current += char
        elif char == ',' and depth == 0:
            parts.append(current.strip())
            current = ''
        else:
            current += char
    
    if current.strip():
        parts.append(current.strip())
    
    for part in parts:
        if not part:
            continue
        
        # Check for default value
        default_value = None
        if '=' in part:
            name_part, default_part = part.split('=', 1)
            name = name_part.strip()
            default_value = default_part.strip()
        else:
            name = part.strip()
        
        # Handle rest parameters
        if name.startswith('...'):
            name = name  # Keep the ... prefix
        
        # Handle destructuring - just use the whole pattern as the name
        # (more sophisticated parsing would extract individual names)
        
        parameters.append(Parameter(
            name=name,
            type_hint=None,  # JavaScript doesn't have native type hints (unless TypeScript)
            default_value=default_value
        ))
    
    return parameters


def parse_javascript_file(file_path: str) -> FileMetadata:
    """
    Parse a JavaScript file using regex-based pattern matching and extract metadata.
    
    Extracts:
    - Function declarations: function name(params) { }
    - Arrow functions: const name = (params) => { }
    - Class definitions: class Name { }
    - Method definitions within classes
    - Preceding comment blocks
    
    Args:
        file_path: Path to the JavaScript file to parse
        
    Returns:
        FileMetadata object containing extracted information
        
    Requirements: 4.1, 4.2, 4.4, 4.5
    """
    classes = []
    functions = []
    parse_errors = []
    
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        lines = source_code.split('\n')
        
        # Pattern for function declarations: function name(params)
        function_pattern = r'function\s+(\w+)\s*\(([^)]*)\)'
        
        # Pattern for arrow functions: const name = (params) =>
        # Also handle: const name = params => (single param without parens)
        # Also handle async: const name = async (params) =>
        arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\(([^)]*)\)|(\w+))\s*=>'
        
        # Pattern for class definitions: class Name
        # Use word boundary and ensure it's at the start of a line (after optional whitespace)
        class_pattern = r'^\s*class\s+(\w+)'
        
        # Pattern for method definitions: methodName(params) {
        # This is used inside classes
        method_pattern = r'^\s*(\w+)\s*\(([^)]*)\)\s*\{'
        
        # Track line numbers for each match
        line_to_content = {i: line for i, line in enumerate(lines)}
        
        # Extract function declarations
        for match in re.finditer(function_pattern, source_code, re.MULTILINE):
            func_name = match.group(1)
            params_str = match.group(2)
            
            # Find the line number
            line_num = source_code[:match.start()].count('\n') + 1
            
            # Extract preceding comment
            comment = _extract_comment_block(lines, line_num - 1)
            
            # Parse parameters
            parameters = _parse_parameters(params_str)
            
            functions.append(FunctionMetadata(
                name=func_name,
                parameters=parameters,
                return_type=None,  # JavaScript doesn't have return type annotations
                docstring=comment,
                line_number=line_num
            ))
        
        # Extract arrow functions
        for match in re.finditer(arrow_pattern, source_code, re.MULTILINE):
            func_name = match.group(1)
            # Arrow functions can have params in group 2 (with parens) or group 3 (single param)
            params_str = match.group(2) if match.group(2) is not None else match.group(3)
            if params_str is None:
                params_str = ''
            
            # Find the line number
            line_num = source_code[:match.start()].count('\n') + 1
            
            # Extract preceding comment
            comment = _extract_comment_block(lines, line_num - 1)
            
            # Parse parameters
            parameters = _parse_parameters(params_str)
            
            functions.append(FunctionMetadata(
                name=func_name,
                parameters=parameters,
                return_type=None,
                docstring=comment,
                line_number=line_num
            ))
        
        # Extract class definitions
        for match in re.finditer(class_pattern, source_code, re.MULTILINE):
            class_name = match.group(1)
            
            # Find the line number
            line_num = source_code[:match.start()].count('\n') + 1
            
            # Extract preceding comment
            comment = _extract_comment_block(lines, line_num - 1)
            
            # Find the class body to extract methods
            # Look for the opening brace after the class declaration
            class_start = match.end()
            brace_start = source_code.find('{', class_start)
            
            if brace_start == -1:
                # No class body found, skip
                continue
            
            # Find the matching closing brace
            brace_count = 1
            i = brace_start + 1
            brace_end = -1
            
            while i < len(source_code) and brace_count > 0:
                if source_code[i] == '{':
                    brace_count += 1
                elif source_code[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        brace_end = i
                        break
                i += 1
            
            if brace_end == -1:
                # Couldn't find matching brace
                continue
            
            # Extract class body
            class_body = source_code[brace_start:brace_end + 1]
            class_body_lines = class_body.split('\n')
            
            # Extract methods from class body
            methods = []
            for method_match in re.finditer(method_pattern, class_body, re.MULTILINE):
                method_name = method_match.group(1)
                method_params_str = method_match.group(2)
                
                # Find line number within the class body
                method_line_offset = class_body[:method_match.start()].count('\n')
                method_line_num = line_num + method_line_offset
                
                # Extract preceding comment within class body
                method_comment = _extract_comment_block(class_body_lines, method_line_offset)
                
                # Parse parameters
                method_parameters = _parse_parameters(method_params_str)
                
                methods.append(FunctionMetadata(
                    name=method_name,
                    parameters=method_parameters,
                    return_type=None,
                    docstring=method_comment,
                    line_number=method_line_num
                ))
            
            classes.append(ClassMetadata(
                name=class_name,
                docstring=comment,
                methods=methods,
                line_number=line_num
            ))
    
    except FileNotFoundError as e:
        # Handle file not found errors
        error_msg = f"File not found: {file_path}"
        parse_errors.append(error_msg)
        logger.error(error_msg)
    
    except PermissionError as e:
        # Handle permission errors
        error_msg = f"Permission denied reading file: {file_path}"
        parse_errors.append(error_msg)
        logger.error(error_msg)
    
    except Exception as e:
        # Handle any other unexpected errors
        error_msg = f"Unexpected error parsing {file_path}: {str(e)}"
        parse_errors.append(error_msg)
        logger.error(error_msg)
    
    return FileMetadata(
        file_path=file_path,
        language='javascript',
        classes=classes,
        functions=functions,
        parse_errors=parse_errors
    )
