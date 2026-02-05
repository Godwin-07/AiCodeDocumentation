"""
Python AST-based parser for extracting code metadata
"""
import ast
import logging
from typing import List, Optional
from ..models import FileMetadata, ClassMetadata, FunctionMetadata, Parameter

# Configure logger for this module
logger = logging.getLogger(__name__)


def _extract_parameters(args: ast.arguments) -> List[Parameter]:
    """
    Extract parameters and default values from ast.arguments.
    
    Args:
        args: ast.arguments object from a function definition
        
    Returns:
        List of Parameter objects
    """
    parameters = []
    
    # Get all arguments (positional and keyword)
    all_args = args.args + args.posonlyargs + args.kwonlyargs
    
    # Calculate how many args have defaults
    # Defaults are aligned to the right of the args list
    num_defaults = len(args.defaults)
    num_args = len(args.args)
    
    # Process regular args
    for i, arg in enumerate(args.args):
        default_value = None
        # Check if this arg has a default (defaults are right-aligned)
        default_index = i - (num_args - num_defaults)
        if default_index >= 0:
            default_node = args.defaults[default_index]
            default_value = ast.unparse(default_node) if default_node else None
        
        type_hint = ast.unparse(arg.annotation) if arg.annotation else None
        parameters.append(Parameter(
            name=arg.arg,
            type_hint=type_hint,
            default_value=default_value
        ))
    
    # Process positional-only args
    for i, arg in enumerate(args.posonlyargs):
        default_value = None
        # posonlyargs can also have defaults
        if i < len(args.defaults):
            default_node = args.defaults[i]
            default_value = ast.unparse(default_node) if default_node else None
        
        type_hint = ast.unparse(arg.annotation) if arg.annotation else None
        parameters.append(Parameter(
            name=arg.arg,
            type_hint=type_hint,
            default_value=default_value
        ))
    
    # Process keyword-only args
    for i, arg in enumerate(args.kwonlyargs):
        default_value = None
        if i < len(args.kw_defaults) and args.kw_defaults[i]:
            default_value = ast.unparse(args.kw_defaults[i])
        
        type_hint = ast.unparse(arg.annotation) if arg.annotation else None
        parameters.append(Parameter(
            name=arg.arg,
            type_hint=type_hint,
            default_value=default_value
        ))
    
    # Process *args
    if args.vararg:
        type_hint = ast.unparse(args.vararg.annotation) if args.vararg.annotation else None
        parameters.append(Parameter(
            name=f"*{args.vararg.arg}",
            type_hint=type_hint,
            default_value=None
        ))
    
    # Process **kwargs
    if args.kwarg:
        type_hint = ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None
        parameters.append(Parameter(
            name=f"**{args.kwarg.arg}",
            type_hint=type_hint,
            default_value=None
        ))
    
    return parameters


def _extract_function_metadata(node: ast.FunctionDef) -> FunctionMetadata:
    """
    Extract metadata from a function definition node.
    
    Args:
        node: ast.FunctionDef or ast.AsyncFunctionDef node
        
    Returns:
        FunctionMetadata object
    """
    parameters = _extract_parameters(node.args)
    docstring = ast.get_docstring(node)
    return_type = ast.unparse(node.returns) if node.returns else None
    
    return FunctionMetadata(
        name=node.name,
        parameters=parameters,
        return_type=return_type,
        docstring=docstring,
        line_number=node.lineno
    )


def _extract_class_metadata(node: ast.ClassDef) -> ClassMetadata:
    """
    Extract metadata from a class definition node.
    
    Args:
        node: ast.ClassDef node
        
    Returns:
        ClassMetadata object
    """
    docstring = ast.get_docstring(node)
    methods = []
    
    # Extract all methods from the class
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_extract_function_metadata(item))
    
    return ClassMetadata(
        name=node.name,
        docstring=docstring,
        methods=methods,
        line_number=node.lineno
    )


def parse_python_file(file_path: str) -> FileMetadata:
    """
    Parse a Python file using the ast module and extract metadata.
    
    Extracts:
    - Class definitions with ast.ClassDef
    - Function definitions with ast.FunctionDef
    - Parameters and default values from ast.arguments
    - Docstrings using ast.get_docstring()
    
    Args:
        file_path: Path to the Python file to parse
        
    Returns:
        FileMetadata object containing extracted information
        
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
    """
    classes = []
    functions = []
    parse_errors = []
    
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse the source code into an AST
        tree = ast.parse(source_code, filename=file_path)
        
        # Extract module-level classes and functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # Extract class definitions
                classes.append(_extract_class_metadata(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Extract module-level function definitions
                functions.append(_extract_function_metadata(node))
    
    except SyntaxError as e:
        # Handle syntax errors gracefully (Requirement 3.6)
        error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
        parse_errors.append(error_msg)
        logger.error(f"Failed to parse {file_path}: {error_msg}")
    
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
        language='python',
        classes=classes,
        functions=functions,
        parse_errors=parse_errors
    )
