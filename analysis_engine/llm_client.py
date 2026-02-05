"""
LLM API client for enhancing documentation with AI-generated descriptions
"""
import json
import requests
import logging
from typing import Dict, Any
from .models import LLMResponse, FileMetadata, ClassMetadata, FunctionMetadata

# Configure logger for this module
logger = logging.getLogger(__name__)


def send_to_llm(
    metadata: FileMetadata,
    endpoint: str,
    model: str,
    timeout: int
) -> LLMResponse:
    """
    Send metadata to LLM and get enhanced documentation.
    Falls back to basic documentation if LLM is unavailable.
    
    Args:
        metadata: Extracted file metadata
        endpoint: LLM API endpoint URL
        model: LLM model name
        timeout: Request timeout in seconds
        
    Returns:
        LLMResponse with enhanced description or basic fallback documentation
    """
    try:
        # Apply code safety check to ensure only metadata is sent (Requirement 5.6)
        # This strips any executable code from docstrings before sending to LLM
        safe_metadata = _apply_code_safety_check(metadata)
        
        # Format metadata as JSON for LLM prompt
        metadata_json = _format_metadata_as_json(safe_metadata)
        
        # Construct prompt requesting Markdown documentation
        prompt = _construct_prompt(metadata_json, metadata.language)
        
        # Prepare request payload
        request_payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a technical documentation assistant. Generate clear, concise Markdown documentation based on the provided code metadata. Focus on explaining the purpose and functionality of classes, functions, and methods. Use proper Markdown formatting with headers, lists, and code blocks."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        }
        
        # Make HTTP POST request with 30-second timeout
        response = requests.post(
            endpoint,
            json=request_payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse LLM response and extract Markdown content
        response_data = response.json()
        
        if "message" in response_data and "content" in response_data["message"]:
            enhanced_description = response_data["message"]["content"]
            return LLMResponse(
                enhanced_description=enhanced_description,
                success=True
            )
        else:
            # Invalid response format - fall back to basic documentation
            logger.warning(f"Invalid LLM response format for {metadata.file_path}, using basic documentation")
            basic_docs = generate_basic_documentation(metadata)
            return LLMResponse(
                enhanced_description=basic_docs,
                success=True,  # Still successful, just using fallback
                error="Used basic documentation due to invalid LLM response format"
            )
            
    except requests.exceptions.Timeout:
        logger.warning(f"LLM request timed out for {metadata.file_path}, using basic documentation")
        basic_docs = generate_basic_documentation(metadata)
        return LLMResponse(
            enhanced_description=basic_docs,
            success=True,  # Still successful, just using fallback
            error="Used basic documentation due to LLM timeout"
        )
    except requests.exceptions.ConnectionError:
        logger.warning(f"Could not connect to LLM for {metadata.file_path}, using basic documentation")
        basic_docs = generate_basic_documentation(metadata)
        return LLMResponse(
            enhanced_description=basic_docs,
            success=True,  # Still successful, just using fallback
            error="Used basic documentation due to LLM connection error"
        )
    except requests.exceptions.HTTPError as e:
        status_code = getattr(e.response, 'status_code', 'unknown') if e.response else 'unknown'
        logger.warning(f"HTTP error {status_code} for {metadata.file_path}, using basic documentation")
        basic_docs = generate_basic_documentation(metadata)
        return LLMResponse(
            enhanced_description=basic_docs,
            success=True,  # Still successful, just using fallback
            error=f"Used basic documentation due to HTTP error: {status_code}"
        )
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON response from LLM for {metadata.file_path}, using basic documentation")
        basic_docs = generate_basic_documentation(metadata)
        return LLMResponse(
            enhanced_description=basic_docs,
            success=True,  # Still successful, just using fallback
            error="Used basic documentation due to invalid JSON response"
        )
    except Exception as e:
        logger.warning(f"Unexpected error with LLM for {metadata.file_path}: {str(e)}, using basic documentation")
        basic_docs = generate_basic_documentation(metadata)
        return LLMResponse(
            enhanced_description=basic_docs,
            success=True,  # Still successful, just using fallback
            error=f"Used basic documentation due to unexpected error: {str(e)}"
        )


def _apply_code_safety_check(metadata: FileMetadata) -> FileMetadata:
    """
    Apply code safety check to ensure only metadata is sent to LLM, not executable code.
    Strips any code content that might have been accidentally included.
    
    Args:
        metadata: FileMetadata object to sanitize
        
    Returns:
        Sanitized FileMetadata with only structural metadata
    """
    # Create a new FileMetadata object with sanitized content
    safe_classes = []
    for cls in metadata.classes:
        # Sanitize docstring to remove any code blocks
        safe_docstring = _sanitize_docstring(cls.docstring) if cls.docstring else None
        
        # Sanitize methods
        safe_methods = []
        for method in cls.methods:
            safe_method_docstring = _sanitize_docstring(method.docstring) if method.docstring else None
            safe_methods.append(FunctionMetadata(
                name=method.name,
                parameters=method.parameters,  # Parameters are already safe (just names and types)
                return_type=method.return_type,
                docstring=safe_method_docstring,
                line_number=method.line_number
            ))
        
        safe_classes.append(ClassMetadata(
            name=cls.name,
            docstring=safe_docstring,
            methods=safe_methods,
            line_number=cls.line_number
        ))
    
    # Sanitize functions
    safe_functions = []
    for func in metadata.functions:
        safe_func_docstring = _sanitize_docstring(func.docstring) if func.docstring else None
        safe_functions.append(FunctionMetadata(
            name=func.name,
            parameters=func.parameters,  # Parameters are already safe
            return_type=func.return_type,
            docstring=safe_func_docstring,
            line_number=func.line_number
        ))
    
    return FileMetadata(
        file_path=metadata.file_path,
        language=metadata.language,
        classes=safe_classes,
        functions=safe_functions,
        parse_errors=metadata.parse_errors
    )


def _sanitize_docstring(docstring: str) -> str:
    """
    Sanitize docstring to remove any executable code content.
    Keeps only descriptive text and removes code examples.
    
    Args:
        docstring: Original docstring text
        
    Returns:
        Sanitized docstring with code content removed
    """
    if not docstring:
        return ""
    
    lines = docstring.split('\n')
    sanitized_lines = []
    in_code_block = False
    
    for line in lines:
        # Detect code block markers (```, >>>, etc.)
        stripped = line.strip()
        
        # Check for code block delimiters
        if stripped.startswith('```') or stripped.startswith('~~~'):
            in_code_block = not in_code_block
            continue  # Skip the delimiter line
        
        # Skip lines that look like code (Python interactive prompt)
        if stripped.startswith('>>>') or stripped.startswith('...'):
            continue
        
        # Skip lines inside code blocks
        if in_code_block:
            continue
        
        # For lines outside code blocks, check if they look like code
        # Only filter if it's clearly a code statement
        if stripped and _looks_like_code(stripped):
            continue
        
        # Keep the line (it's natural language or acceptable content)
        sanitized_lines.append(line)
    
    return '\n'.join(sanitized_lines)


def _looks_like_code(line: str) -> bool:
    """
    Heuristic to detect if a line looks like executable code.
    
    Args:
        line: Line of text to check
        
    Returns:
        True if line appears to be code, False otherwise
    """
    stripped = line.strip()
    
    # Empty lines are not code
    if not stripped:
        return False
    
    # Lines starting with common code patterns (must be at start of line)
    code_start_patterns = [
        'def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ',
        'try:', 'except:', 'finally:', 'with ', 'async ', 'await ',
        'function ', 'const ', 'let ', 'var ', 'public ', 'private ', 'protected ',
        'static ', 'void ', 'int ', 'String ', 'boolean ', 'new ',
        'return ', 'yield ', 'pass', 'break', 'continue'
    ]
    
    for pattern in code_start_patterns:
        if stripped.startswith(pattern):
            return True
    
    # Lines that are exactly certain keywords
    if stripped in ['pass', 'break', 'continue', 'return', 'yield']:
        return True
    
    # Lines with specific code patterns anywhere in the line
    code_anywhere_patterns = [
        '=>', '};', '});', ');'
    ]
    
    for pattern in code_anywhere_patterns:
        if pattern in stripped:
            return True
    
    # Check for lines that are just braces (common in code)
    if stripped in ['{', '}', '};', ');', '});']:
        return True
    
    # Lines with assignment operators (but not in natural language context)
    # Only flag as code if it looks like a statement, not a description
    if '=' in stripped:
        # Check if it's likely an assignment statement
        # Exclude natural language patterns like "equals", "is equal to"
        if not any(word in stripped.lower() for word in ['equals', 'equal to', 'is equal', 'are equal']):
            # Check if it's not a list item or markdown
            if not stripped.startswith('-') and not stripped.startswith('*'):
                # Check if it has typical code patterns (variable = value)
                parts = stripped.split('=')
                if len(parts) == 2:
                    left = parts[0].strip()
                    # If left side is a single word or simple expression, likely code
                    if left and not ' ' in left.strip() or '.' in left or '[' in left:
                        return True
    
    return False


def _format_metadata_as_json(metadata: FileMetadata) -> str:
    """
    Format FileMetadata as JSON string for LLM prompt.
    
    Args:
        metadata: FileMetadata object to format
        
    Returns:
        JSON string representation of metadata
    """
    # Convert metadata to dictionary format
    metadata_dict = {
        "file_path": metadata.file_path,
        "language": metadata.language,
        "classes": [],
        "functions": []
    }
    
    # Add class information
    for cls in metadata.classes:
        class_dict = {
            "name": cls.name,
            "docstring": cls.docstring,
            "line_number": cls.line_number,
            "methods": []
        }
        
        # Add method information
        for method in cls.methods:
            method_dict = {
                "name": method.name,
                "parameters": [
                    {
                        "name": param.name,
                        "type_hint": param.type_hint,
                        "default_value": param.default_value
                    }
                    for param in method.parameters
                ],
                "return_type": method.return_type,
                "docstring": method.docstring,
                "line_number": method.line_number
            }
            class_dict["methods"].append(method_dict)
        
        metadata_dict["classes"].append(class_dict)
    
    # Add function information
    for func in metadata.functions:
        func_dict = {
            "name": func.name,
            "parameters": [
                {
                    "name": param.name,
                    "type_hint": param.type_hint,
                    "default_value": param.default_value
                }
                for param in func.parameters
            ],
            "return_type": func.return_type,
            "docstring": func.docstring,
            "line_number": func.line_number
        }
        metadata_dict["functions"].append(func_dict)
    
    return json.dumps(metadata_dict, indent=2)


def _construct_prompt(metadata_json: str, language: str) -> str:
    """
    Construct prompt requesting Markdown documentation.
    
    Args:
        metadata_json: JSON string of file metadata
        language: Programming language of the file
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""Please generate comprehensive Markdown documentation for the following {language} code metadata:

{metadata_json}

Requirements:
1. Generate documentation in valid Markdown format
2. Create clear, concise descriptions for each class and function
3. Explain the purpose and functionality of each component
4. For functions and methods, describe what they do and their parameters
5. Use proper Markdown formatting with headers, lists, and code blocks
6. Focus on clarity and readability for developers
7. If existing docstrings are present, enhance and expand them
8. Structure the documentation logically with appropriate headings

Please provide only the Markdown documentation content, without any additional explanations or comments."""
    
    return prompt


def generate_basic_documentation(metadata: FileMetadata) -> str:
    """
    Generate basic documentation from metadata only (fallback when LLM is unavailable).
    
    Args:
        metadata: FileMetadata object containing extracted code structure
        
    Returns:
        Basic Markdown documentation string
    """
    lines = []
    
    # File header
    lines.append(f"## {metadata.file_path}")
    lines.append("")
    lines.append(f"**Language:** {metadata.language.title()}")
    lines.append("")
    
    # Add parse errors if any
    if metadata.parse_errors:
        lines.append("**Parse Errors:**")
        for error in metadata.parse_errors:
            lines.append(f"- {error}")
        lines.append("")
    
    # Document classes
    if metadata.classes:
        lines.append("### Classes")
        lines.append("")
        
        for cls in metadata.classes:
            lines.append(f"#### {cls.name}")
            lines.append("")
            
            if cls.docstring:
                lines.append(cls.docstring)
                lines.append("")
            else:
                lines.append(f"Class defined at line {cls.line_number}")
                lines.append("")
            
            # Document methods
            if cls.methods:
                lines.append("**Methods:**")
                lines.append("")
                
                for method in cls.methods:
                    # Method signature
                    params = ", ".join([
                        f"{p.name}" + (f": {p.type_hint}" if p.type_hint else "") + 
                        (f" = {p.default_value}" if p.default_value else "")
                        for p in method.parameters
                    ])
                    signature = f"{method.name}({params})"
                    if method.return_type:
                        signature += f" -> {method.return_type}"
                    
                    lines.append(f"##### {signature}")
                    lines.append("")
                    
                    if method.docstring:
                        lines.append(method.docstring)
                    else:
                        lines.append(f"Method defined at line {method.line_number}")
                        
                        # List parameters if any
                        if method.parameters:
                            lines.append("")
                            lines.append("**Parameters:**")
                            for param in method.parameters:
                                param_desc = f"- `{param.name}`"
                                if param.type_hint:
                                    param_desc += f" ({param.type_hint})"
                                if param.default_value:
                                    param_desc += f" - Default: {param.default_value}"
                                lines.append(param_desc)
                    
                    lines.append("")
            
            lines.append("---")
            lines.append("")
    
    # Document functions
    if metadata.functions:
        lines.append("### Functions")
        lines.append("")
        
        for func in metadata.functions:
            # Function signature
            params = ", ".join([
                f"{p.name}" + (f": {p.type_hint}" if p.type_hint else "") + 
                (f" = {p.default_value}" if p.default_value else "")
                for p in func.parameters
            ])
            signature = f"{func.name}({params})"
            if func.return_type:
                signature += f" -> {func.return_type}"
            
            lines.append(f"#### {signature}")
            lines.append("")
            
            if func.docstring:
                lines.append(func.docstring)
            else:
                lines.append(f"Function defined at line {func.line_number}")
                
                # List parameters if any
                if func.parameters:
                    lines.append("")
                    lines.append("**Parameters:**")
                    for param in func.parameters:
                        param_desc = f"- `{param.name}`"
                        if param.type_hint:
                            param_desc += f" ({param.type_hint})"
                        if param.default_value:
                            param_desc += f" - Default: {param.default_value}"
                        lines.append(param_desc)
            
            lines.append("")
            lines.append("---")
            lines.append("")
    
    # If no classes or functions found
    if not metadata.classes and not metadata.functions:
        lines.append("*No classes or functions found in this file.*")
        lines.append("")
    
    return "\n".join(lines)