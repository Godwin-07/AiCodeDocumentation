"""
Docstring generator for adding AI-enhanced docstrings to source code files.
"""
import re
import logging
from typing import List, Dict, Any
from .models import FileMetadata, ClassMetadata, FunctionMetadata
from .llm_client import send_to_llm

logger = logging.getLogger(__name__)


def generate_docstrings_for_file(
    file_path: str,
    metadata: FileMetadata,
    llm_endpoint: str,
    llm_model: str,
    llm_timeout: int
) -> str:
    """
    Generate enhanced source code with AI-generated docstrings.
    
    Args:
        file_path: Path to the source file
        metadata: Extracted metadata from the file
        llm_endpoint: LLM API endpoint
        llm_model: LLM model name
        llm_timeout: Request timeout in seconds
        
    Returns:
        Modified source code with added docstrings
    """
    # Read the original file
    with open(file_path, 'r', encoding='utf-8') as f:
        original_code = f.read()
    
    # Generate docstrings using LLM
    docstrings = _generate_docstrings_with_llm(
        metadata, llm_endpoint, llm_model, llm_timeout
    )
    
    # Insert docstrings into the code
    modified_code = _insert_docstrings(original_code, metadata, docstrings)
    
    return modified_code


def _generate_docstrings_with_llm(
    metadata: FileMetadata,
    llm_endpoint: str,
    llm_model: str,
    llm_timeout: int
) -> Dict[str, str]:
    """
    Use LLM to generate docstrings for all functions and classes.
    
    Returns:
        Dictionary mapping function/class names to their docstrings
    """
    import requests
    import json
    
    docstrings = {}
    
    # Prepare metadata for LLM
    items_to_document = []
    
    # Add classes
    for cls in metadata.classes:
        items_to_document.append({
            'type': 'class',
            'name': cls.name,
            'line': cls.line_number,
            'existing_docstring': cls.docstring,
            'methods': [
                {
                    'name': m.name,
                    'parameters': [{'name': p.name, 'type': p.type_hint, 'default': p.default_value} for p in m.parameters],
                    'return_type': m.return_type
                }
                for m in cls.methods
            ]
        })
        
        # Add methods
        for method in cls.methods:
            items_to_document.append({
                'type': 'method',
                'class': cls.name,
                'name': method.name,
                'line': method.line_number,
                'parameters': [{'name': p.name, 'type': p.type_hint, 'default': p.default_value} for p in method.parameters],
                'return_type': method.return_type,
                'existing_docstring': method.docstring
            })
    
    # Add functions
    for func in metadata.functions:
        items_to_document.append({
            'type': 'function',
            'name': func.name,
            'line': func.line_number,
            'parameters': [{'name': p.name, 'type': p.type_hint, 'default': p.default_value} for p in func.parameters],
            'return_type': func.return_type,
            'existing_docstring': func.docstring
        })
    
    # Generate docstrings for each item
    for item in items_to_document:
        try:
            docstring = _generate_single_docstring(
                item, metadata.language, llm_endpoint, llm_model, llm_timeout
            )
            
            # Create a unique key for this item
            if item['type'] == 'method':
                key = f"{item['class']}.{item['name']}"
            else:
                key = item['name']
            
            docstrings[key] = docstring
            
        except Exception as e:
            logger.warning(f"Failed to generate docstring for {item['name']}: {e}")
            # Use existing docstring or create a basic one
            if item.get('existing_docstring'):
                docstrings[key] = item['existing_docstring']
    
    return docstrings


def _generate_single_docstring(
    item: Dict[str, Any],
    language: str,
    llm_endpoint: str,
    llm_model: str,
    llm_timeout: int
) -> str:
    """Generate a single docstring using LLM."""
    import requests
    import json
    
    # Construct prompt
    prompt = f"""Generate a clear, concise docstring for this {language} {item['type']}:

Name: {item['name']}
Parameters: {json.dumps(item.get('parameters', []), indent=2)}
Return Type: {item.get('return_type', 'None')}

Requirements:
1. Follow {language} docstring conventions
2. Explain what the {item['type']} does
3. Document each parameter clearly
4. Document the return value if applicable
5. Keep it concise and professional (2-4 sentences maximum)
6. Do NOT include code examples
7. Do NOT include markdown formatting or code blocks
8. Output ONLY plain text, no quotes, delimiters, or special formatting

Generate the docstring:"""
    
    # Make LLM request
    payload = {
        "model": llm_model,
        "messages": [
            {
                "role": "system",
                "content": f"You are a technical documentation expert. Generate clear, concise docstrings for {language} code. Output only plain text without any markdown formatting."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }
    
    response = requests.post(
        llm_endpoint,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=llm_timeout
    )
    
    response.raise_for_status()
    response_data = response.json()
    
    if "message" in response_data and "content" in response_data["message"]:
        docstring = response_data["message"]["content"].strip()
        
        # Clean up the docstring - remove any markdown artifacts
        docstring = _clean_llm_output(docstring)
        
        return docstring
    
    raise ValueError("Invalid LLM response format")


def _insert_docstrings(
    original_code: str,
    metadata: FileMetadata,
    docstrings: Dict[str, str]
) -> str:
    """
    Insert generated docstrings into the original code.
    
    Args:
        original_code: Original source code
        metadata: File metadata with line numbers
        docstrings: Generated docstrings mapped by name
        
    Returns:
        Modified code with docstrings inserted
    """
    lines = original_code.split('\n')
    
    # Collect all insertion points (line number, docstring)
    insertions = []
    
    # Process classes
    for cls in metadata.classes:
        key = cls.name
        if key in docstrings and not cls.docstring:
            # Insert after the class definition line (line_number is 0-indexed in our list)
            # The parser gives us 1-indexed line numbers, so we need to adjust
            def_line_idx = cls.line_number - 1
            
            # Get the indentation of the class definition
            class_indent = _get_indent(lines, def_line_idx)
            
            # Docstring should be indented one level more than the class
            docstring_indent = class_indent + '    '
            
            formatted_docstring = _format_docstring(
                docstrings[key], docstring_indent, metadata.language
            )
            
            # Insert after the class definition line
            insertions.append((def_line_idx + 1, formatted_docstring))
        
        # Process methods
        for method in cls.methods:
            key = f"{cls.name}.{method.name}"
            if key in docstrings and not method.docstring:
                # Insert after the method definition line
                def_line_idx = method.line_number - 1
                
                # Get the indentation of the method definition
                method_indent = _get_indent(lines, def_line_idx)
                
                # Docstring should be indented one level more than the method
                docstring_indent = method_indent + '    '
                
                formatted_docstring = _format_docstring(
                    docstrings[key], docstring_indent, metadata.language
                )
                
                # Insert after the method definition line
                insertions.append((def_line_idx + 1, formatted_docstring))
    
    # Process functions
    for func in metadata.functions:
        key = func.name
        if key in docstrings and not func.docstring:
            # Insert after the function definition line
            def_line_idx = func.line_number - 1
            
            # Get the indentation of the function definition
            func_indent = _get_indent(lines, def_line_idx)
            
            # Docstring should be indented one level more than the function
            docstring_indent = func_indent + '    '
            
            formatted_docstring = _format_docstring(
                docstrings[key], docstring_indent, metadata.language
            )
            
            # Insert after the function definition line
            insertions.append((def_line_idx + 1, formatted_docstring))
    
    # Sort insertions by line number (reverse order to maintain line numbers)
    insertions.sort(key=lambda x: x[0], reverse=True)
    
    # Insert docstrings
    for line_idx, docstring in insertions:
        if 0 <= line_idx <= len(lines):
            lines.insert(line_idx, docstring)
    
    return '\n'.join(lines)


def _get_indent(lines: List[str], line_num: int) -> str:
    """Get the indentation of a specific line."""
    if line_num < len(lines):
        line = lines[line_num]
        return line[:len(line) - len(line.lstrip())]
    return ''


def _clean_llm_output(text: str) -> str:
    """
    Clean LLM output to remove markdown artifacts and formatting issues.
    
    Args:
        text: Raw LLM output
        
    Returns:
        Cleaned text suitable for docstrings
    """
    # Remove markdown code blocks
    text = re.sub(r'```[\w]*\n?', '', text)
    text = re.sub(r'```', '', text)
    
    # Remove leading/trailing quotes that LLM might add
    text = text.strip('"\'`')
    
    # Remove docstring delimiters if LLM included them
    text = re.sub(r'^"""\s*', '', text)
    text = re.sub(r'\s*"""$', '', text)
    text = re.sub(r'^/\*\*\s*', '', text)
    text = re.sub(r'\s*\*/$', '', text)
    
    # Clean up excessive whitespace
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove leading * from javadoc-style comments if present
        line = re.sub(r'^\s*\*\s?', '', line)
        cleaned_lines.append(line.rstrip())
    
    # Remove empty lines at start and end
    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    return '\n'.join(cleaned_lines)


def _format_docstring(docstring: str, indent: str, language: str) -> str:
    """
    Format docstring with proper delimiters and indentation.
    
    Args:
        docstring: Raw docstring text
        indent: Indentation string
        language: Programming language
        
    Returns:
        Formatted docstring with delimiters
    """
    # Split into lines and clean
    lines = docstring.split('\n')
    
    if language == 'python':
        # Python uses triple quotes
        formatted_lines = [f'{indent}"""']
        
        for line in lines:
            # Each line should have the same indentation as the opening quotes
            if line.strip():  # Only add indent to non-empty lines
                formatted_lines.append(f'{indent}{line}')
            else:
                formatted_lines.append('')  # Keep empty lines empty
        
        formatted_lines.append(f'{indent}"""')
        return '\n'.join(formatted_lines)
    
    elif language == 'javascript' or language == 'java':
        # JavaScript and Java use /** */ style
        formatted_lines = [f'{indent}/**']
        
        for line in lines:
            # Each line should have proper indentation and * prefix
            if line.strip():
                formatted_lines.append(f'{indent} * {line}')
            else:
                formatted_lines.append(f'{indent} *')  # Keep * on empty lines
        
        formatted_lines.append(f'{indent} */')
        return '\n'.join(formatted_lines)
    
    return docstring
