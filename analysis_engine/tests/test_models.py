"""
Unit tests for data models
"""
import pytest
from analysis_engine.models import Parameter, FunctionMetadata, ClassMetadata, FileMetadata


def test_parameter_creation():
    """Test creating a Parameter object"""
    param = Parameter(name="arg1", type_hint="str", default_value="'default'")
    assert param.name == "arg1"
    assert param.type_hint == "str"
    assert param.default_value == "'default'"


def test_function_metadata_creation():
    """Test creating a FunctionMetadata object"""
    params = [Parameter(name="x", type_hint="int")]
    func = FunctionMetadata(
        name="test_func",
        parameters=params,
        return_type="bool",
        docstring="Test function",
        line_number=10
    )
    assert func.name == "test_func"
    assert len(func.parameters) == 1
    assert func.return_type == "bool"
    assert func.docstring == "Test function"
    assert func.line_number == 10


def test_class_metadata_creation():
    """Test creating a ClassMetadata object"""
    method = FunctionMetadata(
        name="method1",
        parameters=[],
        return_type=None,
        docstring=None,
        line_number=5
    )
    cls = ClassMetadata(
        name="TestClass",
        docstring="A test class",
        methods=[method],
        line_number=3
    )
    assert cls.name == "TestClass"
    assert cls.docstring == "A test class"
    assert len(cls.methods) == 1
    assert cls.line_number == 3


def test_file_metadata_creation():
    """Test creating a FileMetadata object"""
    file_meta = FileMetadata(
        file_path="/path/to/file.py",
        language="python"
    )
    assert file_meta.file_path == "/path/to/file.py"
    assert file_meta.language == "python"
    assert file_meta.classes == []
    assert file_meta.functions == []
    assert file_meta.parse_errors == []
