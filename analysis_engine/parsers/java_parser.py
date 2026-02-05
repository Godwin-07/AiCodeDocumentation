"""
Java regex-based parser for extracting code metadata
"""
import re
import logging
from typing import List, Optional
from ..models import FileMetadata, ClassMetadata, FunctionMetadata, Parameter

# Configure logger for this module
logger = logging.getLogger(__name__)


def _extract_comment_block(lines: List[str], line_index: int) -> Optional[str]:
    """
    Extract comment block immediately preceding a method or class.
    
    Looks for:
    - Single-line comments (//)
    - Multi-line comments (/* ... */)
    - JavaDoc comments (/** ... */)
    
    Args:
        lines: List of source code lines
        line_index: Index of the method/class definition line
        
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
                # Remove comment markers and clean up JavaDoc formatting
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
    
    Handles Java method parameters like:
    - Simple parameters: (int a, String b)
    - Generic types: (List<String> items, Map<String, Integer> map)
    - Arrays: (int[] numbers, String... args)
    - Annotations: (@NotNull String name, @Override int value)
    
    Args:
        param_string: String containing parameter list
        
    Returns:
        List of Parameter objects
    """
    if not param_string or param_string.strip() == '':
        return []
    
    parameters = []
    
    # Split by comma, but be careful with generic types and nested structures
    parts = []
    current = ''
    depth = 0
    
    for char in param_string:
        if char in '<([':
            depth += 1
            current += char
        elif char in '>)]':
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
        
        # Remove annotations (simple approach - remove @word patterns)
        part = re.sub(r'@\w+\s+', '', part)
        
        # Split into type and name
        # Java parameters are: [final] Type name
        tokens = part.strip().split()
        
        if len(tokens) >= 2:
            # Handle 'final' modifier
            if tokens[0] == 'final':
                if len(tokens) >= 3:
                    type_hint = tokens[1]
                    name = tokens[2]
                else:
                    # Malformed parameter, use the whole thing as name
                    type_hint = None
                    name = part.strip()
            else:
                # Last token is the parameter name, everything else is the type
                name = tokens[-1]
                type_hint = ' '.join(tokens[:-1])
        elif len(tokens) == 1:
            # Only one token - could be just a type or just a name
            # In Java, this is likely just a name (unusual but possible)
            name = tokens[0]
            type_hint = None
        else:
            # Empty or malformed parameter
            name = part.strip()
            type_hint = None
        
        parameters.append(Parameter(
            name=name,
            type_hint=type_hint,
            default_value=None  # Java doesn't have default parameter values
        ))
    
    return parameters


def parse_java_file(file_path: str) -> FileMetadata:
    """
    Parse a Java file using regex-based pattern matching and extract metadata.
    
    Extracts:
    - Class declarations: class ClassName
    - Method signatures with modifiers: public/private/protected static returnType methodName(params)
    - Parameters from method signatures
    - Preceding comment blocks (/** ... */)
    
    Args:
        file_path: Path to the Java file to parse
        
    Returns:
        FileMetadata object containing extracted information
        
    Requirements: 4.1, 4.3, 4.4, 4.5
    """
    classes = []
    functions = []
    parse_errors = []
    
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        lines = source_code.split('\n')
        
        # Pattern for class declarations: [modifiers] class ClassName
        # Also match interfaces: [modifiers] interface InterfaceName
        class_pattern = r'^\s*(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?(?:class|interface)\s+(\w+)'
        
        # Pattern for method signatures with modifiers
        # Captures: modifiers, return type, method name, parameters
        # Example: public static void main(String[] args)
        # Example: private int calculateSum(int a, int b)
        method_pattern = r'^\s*((?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(?:abstract)?\s*(?:synchronized)?\s*)(\w+(?:<[^>]*>)?(?:\[\])*)\s+(\w+)\s*\(([^)]*)\)'
        
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
            
            # Skip until we find the opening brace (might have extends/implements clauses)
            brace_start = -1
            i = class_start
            while i < len(source_code):
                if source_code[i] == '{':
                    brace_start = i
                    break
                i += 1
            
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
                modifiers = method_match.group(1).strip()
                return_type = method_match.group(2)
                method_name = method_match.group(3)
                method_params_str = method_match.group(4)
                
                # Skip constructors (method name same as class name)
                if method_name == class_name:
                    continue
                
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
                    return_type=return_type,
                    docstring=method_comment,
                    line_number=method_line_num
                ))
            
            classes.append(ClassMetadata(
                name=class_name,
                docstring=comment,
                methods=methods,
                line_number=line_num
            ))
        
        # Also extract standalone methods (though rare in Java, could be in interfaces or utility classes)
        # Look for methods outside of the class bodies we already processed
        for match in re.finditer(method_pattern, source_code, re.MULTILINE):
            modifiers = match.group(1).strip()
            return_type = match.group(2)
            method_name = match.group(3)
            method_params_str = match.group(4)
            
            # Find the line number
            line_num = source_code[:match.start()].count('\n') + 1
            
            # Check if this method is inside any of the classes we found
            inside_class = False
            for class_meta in classes:
                # Check if the method line number falls within the class body range
                # We need to find the class body boundaries
                class_line = class_meta.line_number
                
                # Find the class in the source code to get its body range
                class_lines = source_code.split('\n')
                class_start_line = class_line - 1  # Convert to 0-based index
                
                # Find the opening brace for this class
                brace_found = False
                class_body_start = -1
                class_body_end = -1
                
                for i in range(class_start_line, len(class_lines)):
                    line_content = class_lines[i]
                    if '{' in line_content and not brace_found:
                        # Found opening brace, now find the matching closing brace
                        brace_count = line_content.count('{') - line_content.count('}')
                        class_body_start = i + 1  # Line number (1-based)
                        
                        # Continue counting braces to find the end
                        for j in range(i + 1, len(class_lines)):
                            brace_count += class_lines[j].count('{') - class_lines[j].count('}')
                            if brace_count == 0:
                                class_body_end = j + 1  # Line number (1-based)
                                break
                        break
                
                # Check if method line is within this class body
                if class_body_start <= line_num <= class_body_end:
                    inside_class = True
                    break
            
            # If not inside a class, add as a standalone function
            if not inside_class:
                # Extract preceding comment
                comment = _extract_comment_block(lines, line_num - 1)
                
                # Parse parameters
                parameters = _parse_parameters(method_params_str)
                
                functions.append(FunctionMetadata(
                    name=method_name,
                    parameters=parameters,
                    return_type=return_type,
                    docstring=comment,
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
        language='java',
        classes=classes,
        functions=functions,
        parse_errors=parse_errors
    )