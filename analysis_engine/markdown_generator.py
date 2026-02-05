"""
Markdown documentation generator
"""
from typing import List
from datetime import datetime
from .models import FileMetadata, ClassMetadata, FunctionMetadata, Parameter


def generate_markdown(all_metadata: List[FileMetadata]) -> str:
    """
    Generate a complete Markdown documentation file from extracted metadata.
    
    Args:
        all_metadata: List of FileMetadata objects for all analyzed files
        
    Returns:
        Complete Markdown document as a string
    """
    sections = []
    
    # Title and timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections.append(f"# Project Documentation\n\n*Generated on: {timestamp}*\n")
    
    # Table of Contents
    sections.append(_generate_table_of_contents(all_metadata))
    
    # Overview section
    sections.append(_generate_overview(all_metadata))
    
    # Files section
    sections.append(_generate_files_section(all_metadata))
    
    return "\n".join(sections)


def _generate_table_of_contents(all_metadata: List[FileMetadata]) -> str:
    """Generate table of contents with links to major sections."""
    toc = ["## Table of Contents\n"]
    toc.append("- [Overview](#overview)")
    toc.append("- [Files](#files)")
    
    for file_meta in all_metadata:
        # Create anchor link from file path (remove special chars, convert to lowercase)
        anchor = _create_anchor(file_meta.file_path)
        toc.append(f"  - [{file_meta.file_path}](#{anchor})")
    
    toc.append("")  # Empty line after TOC
    return "\n".join(toc)


def _generate_overview(all_metadata: List[FileMetadata]) -> str:
    """Generate project overview section."""
    overview = ["## Overview\n"]
    
    # Count statistics
    total_files = len(all_metadata)
    total_classes = sum(len(fm.classes) for fm in all_metadata)
    total_functions = sum(len(fm.functions) for fm in all_metadata)
    total_methods = sum(
        len(cls.methods) for fm in all_metadata for cls in fm.classes
    )
    
    # Language breakdown
    languages = {}
    for fm in all_metadata:
        languages[fm.language] = languages.get(fm.language, 0) + 1
    
    overview.append(f"This project contains {total_files} source file(s) with:")
    overview.append(f"- {total_classes} class(es)")
    overview.append(f"- {total_functions} top-level function(s)")
    overview.append(f"- {total_methods} method(s)")
    overview.append("")
    overview.append("**Languages:**")
    for lang, count in sorted(languages.items()):
        overview.append(f"- {lang.capitalize()}: {count} file(s)")
    overview.append("")
    
    return "\n".join(overview)


def _generate_files_section(all_metadata: List[FileMetadata]) -> str:
    """Generate file-wise documentation sections."""
    sections = ["## Files\n"]
    
    for file_meta in all_metadata:
        sections.append(_generate_file_documentation(file_meta))
        sections.append("---\n")  # Separator between files
    
    return "\n".join(sections)


def _generate_file_documentation(file_meta: FileMetadata) -> str:
    """Generate documentation for a single file."""
    doc = []
    
    # File header
    anchor = _create_anchor(file_meta.file_path)
    doc.append(f"### {file_meta.file_path}\n")
    doc.append(f"**Language:** {file_meta.language.capitalize()}  ")
    doc.append(f"**Path:** `{file_meta.file_path}`\n")
    
    # Parse errors if any
    if file_meta.parse_errors:
        doc.append("**⚠️ Parse Errors:**")
        for error in file_meta.parse_errors:
            doc.append(f"- {error}")
        doc.append("")
    
    # If we have LLM-enhanced description, use it instead of the basic structure
    if file_meta.enhanced_description:
        doc.append(file_meta.enhanced_description)
        doc.append("")
        return "\n".join(doc)
    
    # Otherwise, fall back to basic documentation structure
    # Classes section
    if file_meta.classes:
        doc.append("#### Classes\n")
        for cls in file_meta.classes:
            doc.append(_generate_class_documentation(cls, file_meta.language))
    
    # Functions section
    if file_meta.functions:
        doc.append("#### Functions\n")
        for func in file_meta.functions:
            doc.append(_generate_function_documentation(func, file_meta.language))
    
    # If no classes or functions
    if not file_meta.classes and not file_meta.functions:
        doc.append("*No classes or functions found in this file.*\n")
    
    return "\n".join(doc)


def _generate_class_documentation(cls: ClassMetadata, language: str) -> str:
    """Generate documentation for a class."""
    doc = []
    
    doc.append(f"##### {cls.name}\n")
    
    # Docstring or description
    if cls.docstring:
        doc.append(cls.docstring.strip())
        doc.append("")
    else:
        doc.append(f"Class defined at line {cls.line_number}.\n")
    
    # Methods
    if cls.methods:
        doc.append("**Methods:**\n")
        for method in cls.methods:
            doc.append(_generate_method_documentation(method, language))
    else:
        doc.append("*No methods found.*\n")
    
    return "\n".join(doc)


def _generate_method_documentation(method: FunctionMetadata, language: str) -> str:
    """Generate documentation for a method."""
    doc = []
    
    # Method signature
    params_str = _format_parameters_inline(method.parameters)
    doc.append(f"###### {method.name}({params_str})\n")
    
    # Docstring
    if method.docstring:
        doc.append(method.docstring.strip())
        doc.append("")
    
    # Parameters list
    if method.parameters:
        doc.append("**Parameters:**")
        for param in method.parameters:
            param_doc = f"- `{param.name}`"
            if param.type_hint:
                param_doc += f" ({param.type_hint})"
            if param.default_value:
                param_doc += f" - Default: `{param.default_value}`"
            if method.docstring and param.name in method.docstring:
                # Try to extract parameter description from docstring
                param_doc += " - " + _extract_param_description(method.docstring, param.name)
            doc.append(param_doc)
        doc.append("")
    
    # Return type
    if method.return_type:
        doc.append(f"**Returns:** {method.return_type}\n")
    
    # Code signature with language tag
    signature = _generate_code_signature(method, language)
    doc.append(f"```{language}")
    doc.append(signature)
    doc.append("```\n")
    
    return "\n".join(doc)


def _generate_function_documentation(func: FunctionMetadata, language: str) -> str:
    """Generate documentation for a function."""
    doc = []
    
    # Function signature
    params_str = _format_parameters_inline(func.parameters)
    doc.append(f"##### {func.name}({params_str})\n")
    
    # Docstring
    if func.docstring:
        doc.append(func.docstring.strip())
        doc.append("")
    else:
        doc.append(f"Function defined at line {func.line_number}.\n")
    
    # Parameters list
    if func.parameters:
        doc.append("**Parameters:**")
        for param in func.parameters:
            param_doc = f"- `{param.name}`"
            if param.type_hint:
                param_doc += f" ({param.type_hint})"
            if param.default_value:
                param_doc += f" - Default: `{param.default_value}`"
            doc.append(param_doc)
        doc.append("")
    
    # Return type
    if func.return_type:
        doc.append(f"**Returns:** {func.return_type}\n")
    
    # Code signature with language tag
    signature = _generate_code_signature(func, language)
    doc.append(f"```{language}")
    doc.append(signature)
    doc.append("```\n")
    
    return "\n".join(doc)


def _format_parameters_inline(parameters: List[Parameter]) -> str:
    """Format parameters for inline display in heading."""
    if not parameters:
        return ""
    
    param_strs = []
    for param in parameters:
        param_str = param.name
        if param.type_hint:
            param_str += f": {param.type_hint}"
        if param.default_value:
            param_str += f"={param.default_value}"
        param_strs.append(param_str)
    
    return ", ".join(param_strs)


def _generate_code_signature(func: FunctionMetadata, language: str) -> str:
    """Generate code signature for a function/method."""
    params_str = _format_parameters_inline(func.parameters)
    
    if language == "python":
        signature = f"def {func.name}({params_str})"
        if func.return_type:
            signature += f" -> {func.return_type}"
        signature += ":"
    elif language == "javascript":
        signature = f"function {func.name}({params_str})"
        if func.return_type:
            signature += f" // returns {func.return_type}"
    elif language == "java":
        return_type = func.return_type or "void"
        signature = f"public {return_type} {func.name}({params_str})"
    else:
        signature = f"{func.name}({params_str})"
    
    return signature


def _create_anchor(text: str) -> str:
    """Create a markdown anchor link from text."""
    # Convert to lowercase, replace special chars with hyphens
    anchor = text.lower()
    anchor = anchor.replace("/", "").replace("\\", "")
    anchor = anchor.replace(".", "").replace("_", "")
    anchor = anchor.replace(" ", "-")
    # Remove any remaining special characters
    anchor = "".join(c for c in anchor if c.isalnum() or c == "-")
    return anchor


def _extract_param_description(docstring: str, param_name: str) -> str:
    """Try to extract parameter description from docstring."""
    # Simple heuristic: look for lines containing the parameter name
    lines = docstring.split("\n")
    for line in lines:
        if param_name in line and (":" in line or "-" in line):
            # Extract description after : or -
            parts = line.split(":", 1) if ":" in line else line.split("-", 1)
            if len(parts) > 1:
                return parts[1].strip()
    return ""


def write_documentation(content: str, output_path: str) -> None:
    """
    Write documentation content to a file.
    
    Args:
        content: Markdown content to write
        output_path: Path to output file (DOCUMENTATION.md)
        
    Raises:
        PermissionError: If write permission is denied
        OSError: If other file system errors occur
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except PermissionError as e:
        raise PermissionError(f"Permission denied writing to {output_path}: {e}")
    except OSError as e:
        raise OSError(f"Error writing documentation to {output_path}: {e}")
