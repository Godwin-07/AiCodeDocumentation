"""
Main entry point for the Python analysis engine.
Reads JSON input from stdin, processes files, and outputs JSON results to stdout.

Requirements: 8.2, 8.3, 9.1
"""
import sys
import json
import os
import logging
from typing import Dict, Any, List
from pathlib import Path

# Add the parent directory to sys.path to allow imports when run as a script
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import using absolute imports
from analysis_engine.models import FileMetadata
from analysis_engine.parsers.python_parser import parse_python_file
from analysis_engine.parsers.javascript_parser import parse_javascript_file
from analysis_engine.parsers.java_parser import parse_java_file
from analysis_engine.llm_client import send_to_llm
from analysis_engine.markdown_generator import generate_markdown, write_documentation
from analysis_engine.docstring_generator import generate_docstrings_for_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Log to stderr so stdout is clean for JSON output
)
logger = logging.getLogger(__name__)


def parse_file(file_path: str) -> FileMetadata:
    """
    Dispatch file to appropriate parser based on extension.
    
    Args:
        file_path: Path to the file to parse
        
    Returns:
        FileMetadata object with extracted information
    """
    # Determine file extension
    extension = Path(file_path).suffix.lower()
    
    # Dispatch to appropriate parser
    if extension == '.py':
        return parse_python_file(file_path)
    elif extension == '.js':
        return parse_javascript_file(file_path)
    elif extension == '.java':
        return parse_java_file(file_path)
    else:
        # Unsupported file type
        logger.warning(f"Unsupported file type: {file_path}")
        return FileMetadata(
            file_path=file_path,
            language='unknown',
            classes=[],
            functions=[],
            parse_errors=[f"Unsupported file extension: {extension}"]
        )


def emit_progress(processed: int, total: int) -> None:
    """
    Emit progress update as JSON to stdout.
    
    Args:
        processed: Number of files processed so far
        total: Total number of files to process
    
    Requirements: 9.2
    """
    progress_message = {
        "type": "progress",
        "processed": processed,
        "total": total
    }
    json.dump(progress_message, sys.stdout)
    sys.stdout.write('\n')  # Add newline to separate JSON messages
    sys.stdout.flush()


def process_files_sequentially(
    files: List[str],
    llm_endpoint: str,
    llm_model: str,
    llm_timeout: int,
    workspace_path: str
) -> tuple[List[FileMetadata], int, int, List[str]]:
    """
    Process files sequentially one at a time.
    
    Args:
        files: List of file paths to process
        llm_endpoint: LLM API endpoint URL
        llm_model: LLM model name
        llm_timeout: LLM request timeout in seconds
        workspace_path: Workspace root path
        
    Returns:
        Tuple of (all_metadata, files_processed, files_skipped, errors)
    """
    all_metadata = []
    files_processed = 0
    files_skipped = 0
    errors = []
    
    total_files = len(files)
    should_emit_progress = total_files > 100  # Only emit progress for >100 files (Requirement 9.2)
    
    # Process files sequentially (Requirement 9.1)
    for idx, file_path in enumerate(files, start=1):
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Parse the file to extract metadata
            metadata = parse_file(file_path)
            
            # Check if parsing had errors
            if metadata.parse_errors:
                logger.warning(f"Parse errors in {file_path}: {metadata.parse_errors}")
                files_skipped += 1
                errors.extend(metadata.parse_errors)
                # Still add to metadata collection for documentation
                all_metadata.append(metadata)
                # Continue processing - we may have partial metadata
                continue
            
            # Call LLM client for enhancement (Requirement 8.2)
            # This will fall back to basic documentation if LLM is unavailable
            llm_response = send_to_llm(
                metadata=metadata,
                endpoint=llm_endpoint,
                model=llm_model,
                timeout=llm_timeout
            )
            
            # Collect LLM errors if any (Requirement 10.4)
            if llm_response.error:
                error_msg = f"{file_path}: {llm_response.error}"
                logger.warning(error_msg)
                errors.append(error_msg)
            
            # Store the enhanced description in the metadata
            metadata.enhanced_description = llm_response.enhanced_description
            
            # Add metadata to collection
            all_metadata.append(metadata)
            files_processed += 1
            
            logger.info(f"Successfully processed: {file_path}")
            
            # Emit progress every 10 files when processing >100 files (Requirement 9.2)
            if should_emit_progress and idx % 10 == 0:
                emit_progress(idx, total_files)
            
        except FileNotFoundError as e:
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            errors.append(error_msg)
            files_skipped += 1
            # Continue processing remaining files (Requirement 10.1)
            
        except PermissionError as e:
            error_msg = f"Permission denied reading file: {file_path}"
            logger.error(error_msg)
            errors.append(error_msg)
            files_skipped += 1
            # Continue processing remaining files (Requirement 10.1)
            
        except Exception as e:
            error_msg = f"Unexpected error processing {file_path}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            files_skipped += 1
            # Continue processing remaining files (Requirement 10.2)
    
    return all_metadata, files_processed, files_skipped, errors


def handle_workspace_mode(
    files: List[str],
    workspace_path: str,
    llm_endpoint: str,
    llm_model: str,
    llm_timeout: int
) -> None:
    """Handle workspace documentation generation mode."""
    errors = []
    
    # Process files sequentially
    all_metadata, files_processed, files_skipped, errors = process_files_sequentially(
        files=files,
        llm_endpoint=llm_endpoint,
        llm_model=llm_model,
        llm_timeout=llm_timeout,
        workspace_path=workspace_path
    )
    
    # Generate Markdown document
    logger.info("Generating Markdown documentation...")
    markdown_content = generate_markdown(all_metadata)
    
    # Write DOCUMENTATION.md to workspace root
    documentation_path = os.path.join(workspace_path, 'DOCUMENTATION.md')
    logger.info(f"Writing documentation to: {documentation_path}")
    
    try:
        write_documentation(markdown_content, documentation_path)
        logger.info("Documentation written successfully")
    except Exception as e:
        error_msg = f"Error writing documentation: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        output = {
            "type": "result",
            "success": False,
            "filesProcessed": files_processed,
            "filesSkipped": files_skipped,
            "errors": errors
        }
        json.dump(output, sys.stdout)
        sys.stdout.flush()
        sys.exit(1)
    
    # Output results
    output = {
        "type": "result",
        "success": True,
        "documentationPath": documentation_path,
        "filesProcessed": files_processed,
        "filesSkipped": files_skipped,
        "errors": errors
    }
    json.dump(output, sys.stdout)
    sys.stdout.flush()


def handle_single_file_mode(
    file_path: str,
    workspace_path: str,
    llm_endpoint: str,
    llm_model: str,
    llm_timeout: int,
    output_file_name: str
) -> None:
    """Handle single file documentation generation mode."""
    errors = []
    
    try:
        # Parse the file
        logger.info(f"Parsing file: {file_path}")
        metadata = parse_file(file_path)
        
        if metadata.parse_errors:
            logger.warning(f"Parse errors: {metadata.parse_errors}")
            errors.extend(metadata.parse_errors)
        
        # Enhance with LLM
        logger.info("Enhancing with LLM...")
        llm_response = send_to_llm(
            metadata=metadata,
            endpoint=llm_endpoint,
            model=llm_model,
            timeout=llm_timeout
        )
        
        if llm_response.error:
            logger.warning(f"LLM error: {llm_response.error}")
            errors.append(llm_response.error)
        
        # Store enhanced description
        metadata.enhanced_description = llm_response.enhanced_description
        
        # Generate Markdown for single file
        markdown_content = generate_markdown([metadata])
        
        # Write to custom filename
        documentation_path = os.path.join(workspace_path, output_file_name)
        logger.info(f"Writing documentation to: {documentation_path}")
        
        write_documentation(markdown_content, documentation_path)
        
        # Output results
        output = {
            "type": "result",
            "success": True,
            "documentationPath": documentation_path,
            "filesProcessed": 1,
            "filesSkipped": 0,
            "errors": errors
        }
        json.dump(output, sys.stdout)
        sys.stdout.flush()
        
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        output = {
            "type": "result",
            "success": False,
            "filesProcessed": 0,
            "filesSkipped": 1,
            "errors": errors
        }
        json.dump(output, sys.stdout)
        sys.stdout.flush()
        sys.exit(1)


def handle_add_docstrings_mode(
    file_path: str,
    llm_endpoint: str,
    llm_model: str,
    llm_timeout: int
) -> None:
    """Handle add docstrings mode."""
    errors = []
    
    try:
        # Parse the file
        logger.info(f"Parsing file: {file_path}")
        metadata = parse_file(file_path)
        
        if metadata.parse_errors:
            logger.warning(f"Parse errors: {metadata.parse_errors}")
            errors.extend(metadata.parse_errors)
        
        # Generate docstrings
        logger.info("Generating docstrings with LLM...")
        modified_code = generate_docstrings_for_file(
            file_path=file_path,
            metadata=metadata,
            llm_endpoint=llm_endpoint,
            llm_model=llm_model,
            llm_timeout=llm_timeout
        )
        
        # Write modified code back to file
        logger.info(f"Writing modified code to: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_code)
        
        logger.info("Docstrings added successfully")
        
        # Output results
        output = {
            "type": "result",
            "success": True,
            "documentationPath": file_path,
            "filesProcessed": 1,
            "filesSkipped": 0,
            "errors": errors
        }
        json.dump(output, sys.stdout)
        sys.stdout.flush()
        
    except Exception as e:
        error_msg = f"Error adding docstrings: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        output = {
            "type": "result",
            "success": False,
            "filesProcessed": 0,
            "filesSkipped": 1,
            "errors": errors
        }
        json.dump(output, sys.stdout)
        sys.stdout.flush()
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the analysis engine.
    
    Reads JSON from stdin with:
    - workspacePath: Root path of the workspace
    - files: List of file paths to analyze
    - llmEndpoint: LLM API endpoint URL
    - llmModel: LLM model name (optional, defaults to "llama2")
    - llmTimeout: LLM timeout in seconds (optional, defaults to 30)
    
    Outputs JSON to stdout with:
    - success: Boolean indicating overall success
    - documentationPath: Path to generated DOCUMENTATION.md (if successful)
    - filesProcessed: Number of files successfully processed
    - filesSkipped: Number of files skipped due to errors
    - errors: List of error messages
    
    Requirements: 8.2, 8.3, 9.1
    """
    try:
        # Read input from stdin (Requirement 8.2)
        logger.info("Reading input from stdin...")
        input_data = json.load(sys.stdin)
        
        # Extract input parameters
        workspace_path = input_data.get('workspacePath', '')
        files = input_data.get('files', [])
        llm_endpoint = input_data.get('llmEndpoint', 'https://localhosted:11434/api/chat')
        llm_model = input_data.get('llmModel', 'llama2')
        llm_timeout = input_data.get('llmTimeout', 30)
        mode = input_data.get('mode', 'workspace')  # New: mode parameter
        output_file_name = input_data.get('outputFileName', 'DOCUMENTATION.md')  # New: custom output name
        
        # Validate input
        if not workspace_path:
            raise ValueError("workspacePath is required")
        
        if not files:
            logger.warning("No files provided for processing")
            output = {
                "type": "result",
                "success": True,
                "filesProcessed": 0,
                "filesSkipped": 0,
                "errors": ["No files provided for processing"]
            }
            json.dump(output, sys.stdout)
            sys.stdout.flush()
            return
        
        logger.info(f"Processing {len(files)} file(s) from workspace: {workspace_path}")
        logger.info(f"Mode: {mode}, LLM endpoint: {llm_endpoint}, model: {llm_model}, timeout: {llm_timeout}s")
        
        # Handle different modes
        if mode == 'add-docstrings':
            # Mode: Add docstrings to source file
            handle_add_docstrings_mode(
                files[0], llm_endpoint, llm_model, llm_timeout
            )
        elif mode == 'single-file':
            # Mode: Generate documentation for single file
            handle_single_file_mode(
                files[0], workspace_path, llm_endpoint, llm_model, llm_timeout, output_file_name
            )
        else:
            # Default mode: Generate documentation for entire workspace
            handle_workspace_mode(
                files, workspace_path, llm_endpoint, llm_model, llm_timeout
            )
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON input: {str(e)}"
        logger.error(error_msg)
        error_output = {
            "type": "result",
            "success": False,
            "filesProcessed": 0,
            "filesSkipped": 0,
            "errors": [error_msg]
        }
        json.dump(error_output, sys.stdout)
        sys.stdout.flush()
        sys.exit(1)
        
    except ValueError as e:
        error_msg = f"Invalid input: {str(e)}"
        logger.error(error_msg)
        error_output = {
            "type": "result",
            "success": False,
            "filesProcessed": 0,
            "filesSkipped": 0,
            "errors": [error_msg]
        }
        json.dump(error_output, sys.stdout)
        sys.stdout.flush()
        sys.exit(1)
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        error_output = {
            "type": "result",
            "success": False,
            "filesProcessed": 0,
            "filesSkipped": 0,
            "errors": [error_msg]
        }
        json.dump(error_output, sys.stdout)
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
