"""
Data models for the analysis engine
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Parameter:
    """Represents a function or method parameter"""
    name: str
    type_hint: Optional[str] = None
    default_value: Optional[str] = None


@dataclass
class FunctionMetadata:
    """Metadata extracted from a function or method"""
    name: str
    parameters: List[Parameter]
    return_type: Optional[str]
    docstring: Optional[str]
    line_number: int


@dataclass
class ClassMetadata:
    """Metadata extracted from a class"""
    name: str
    docstring: Optional[str]
    methods: List[FunctionMetadata]
    line_number: int


@dataclass
class FileMetadata:
    """Metadata extracted from a source file"""
    file_path: str
    language: str  # 'python', 'javascript', 'java'
    classes: List[ClassMetadata] = field(default_factory=list)
    functions: List[FunctionMetadata] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)
    enhanced_description: Optional[str] = None  # LLM-generated documentation


@dataclass
class LLMRequest:
    """Request to send to LLM"""
    metadata: Dict[str, Any]
    prompt_template: str


@dataclass
class LLMResponse:
    """Response from LLM"""
    enhanced_description: str
    success: bool
    error: Optional[str] = None
