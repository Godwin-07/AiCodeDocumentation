"""
Documentation templates for different output styles.
"""
from typing import List
from datetime import datetime
from .models import FileMetadata, ClassMetadata, FunctionMetadata, Parameter


class DocumentationTemplate:
    """Base class for documentation templates."""
    
    def generate(self, all_metadata: List[FileMetadata]) -> str:
        """Generate documentation using this template."""
        raise NotImplementedError


class StandardTemplate(DocumentationTemplate):
    """Standard comprehensive documentation template (default)."""
    
    def generate(self, all_metadata: List[FileMetadata]) -> str:
        """Generate standard comprehensive documentation."""
        from .markdown_generator import generate_markdown
        return generate_markdown(all_metadata)


class MinimalTemplate(DocumentationTemplate):
    """Minimal documentation template - brief overview only."""
    
    def generate(self, all_metadata: List[FileMetadata]) -> str:
        """Generate minimal documentation."""
        sections = []
        
        # Title
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sections.append(f"# Project Documentation (Minimal)\n\n*Generated on: {timestamp}*\n")
        
        # Quick stats
        total_files = len(all_metadata)
        total_classes = sum(len(fm.classes) for fm in all_metadata)
        total_functions = sum(len(fm.functions) for fm in all_metadata)
        
        sections.append("## Overview\n")
        sections.append(f"- **Files:** {total_files}")
        sections.append(f"- **Classes:** {total_classes}")
        sections.append(f"- **Functions:** {total_functions}\n")
        
        # File list with brief info
        sections.append("## Files\n")
        for file_meta in all_metadata:
            sections.append(f"### {file_meta.file_path}")
            sections.append(f"*{file_meta.language.capitalize()}*\n")
            
            if file_meta.enhanced_description:
                # Use first sentence only
                first_sentence = file_meta.enhanced_description.split('.')[0] + '.'
                sections.append(first_sentence + "\n")
            else:
                sections.append(f"Contains {len(file_meta.classes)} class(es) and {len(file_meta.functions)} function(s).\n")
        
        return "\n".join(sections)


class APIReferenceTemplate(DocumentationTemplate):
    """API Reference template - focused on signatures and parameters."""
    
    def generate(self, all_metadata: List[FileMetadata]) -> str:
        """Generate API reference documentation."""
        sections = []
        
        # Title
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sections.append(f"# API Reference\n\n*Generated on: {timestamp}*\n")
        
        # Table of contents
        sections.append("## Table of Contents\n")
        for file_meta in all_metadata:
            sections.append(f"- [{file_meta.file_path}](#{self._create_anchor(file_meta.file_path)})")
        sections.append("")
        
        # API documentation
        for file_meta in all_metadata:
            sections.append(f"## {file_meta.file_path}\n")
            sections.append(f"**Language:** {file_meta.language.capitalize()}\n")
            
            # Classes
            for cls in file_meta.classes:
                sections.append(f"### class `{cls.name}`\n")
                if cls.docstring:
                    sections.append(cls.docstring.strip() + "\n")
                
                # Methods
                for method in cls.methods:
                    sections.append(self._format_function_api(method, file_meta.language, is_method=True))
            
            # Functions
            for func in file_meta.functions:
                sections.append(self._format_function_api(func, file_meta.language))
            
            sections.append("---\n")
        
        return "\n".join(sections)
    
    def _format_function_api(self, func: FunctionMetadata, language: str, is_method: bool = False) -> str:
        """Format function/method for API reference."""
        doc = []
        
        # Signature
        params_str = ", ".join([
            f"{p.name}: {p.type_hint}" if p.type_hint else p.name
            for p in func.parameters
        ])
        
        prefix = "  " if is_method else ""
        doc.append(f"{prefix}#### `{func.name}({params_str})`\n")
        
        # Parameters table
        if func.parameters:
            doc.append(f"{prefix}| Parameter | Type | Default | Description |")
            doc.append(f"{prefix}|-----------|------|---------|-------------|")
            for param in func.parameters:
                param_type = param.type_hint or "any"
                param_default = param.default_value or "-"
                doc.append(f"{prefix}| `{param.name}` | `{param_type}` | `{param_default}` | - |")
            doc.append("")
        
        # Return type
        if func.return_type:
            doc.append(f"{prefix}**Returns:** `{func.return_type}`\n")
        
        return "\n".join(doc)
    
    def _create_anchor(self, text: str) -> str:
        """Create markdown anchor."""
        return text.lower().replace("/", "").replace("\\", "").replace(".", "").replace(" ", "-")


class TutorialTemplate(DocumentationTemplate):
    """Tutorial template - explanatory with examples."""
    
    def generate(self, all_metadata: List[FileMetadata]) -> str:
        """Generate tutorial-style documentation."""
        sections = []
        
        # Title
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sections.append(f"# Project Tutorial\n\n*Generated on: {timestamp}*\n")
        
        # Introduction
        sections.append("## Introduction\n")
        sections.append("This tutorial will guide you through the codebase.\n")
        
        # Language breakdown
        languages = {}
        for fm in all_metadata:
            languages[fm.language] = languages.get(fm.language, 0) + 1
        
        sections.append("### Technologies Used\n")
        for lang, count in sorted(languages.items()):
            sections.append(f"- **{lang.capitalize()}**: {count} file(s)")
        sections.append("")
        
        # Files with explanations
        sections.append("## Code Structure\n")
        for file_meta in all_metadata:
            sections.append(f"### {file_meta.file_path}\n")
            
            # Use enhanced description if available
            if file_meta.enhanced_description:
                sections.append(file_meta.enhanced_description + "\n")
            else:
                sections.append(f"This {file_meta.language} file contains:\n")
                if file_meta.classes:
                    sections.append(f"- {len(file_meta.classes)} class(es)")
                if file_meta.functions:
                    sections.append(f"- {len(file_meta.functions)} function(s)")
                sections.append("")
            
            # Key components
            if file_meta.classes:
                sections.append("#### Key Classes\n")
                for cls in file_meta.classes:
                    sections.append(f"**{cls.name}**")
                    if cls.docstring:
                        sections.append(cls.docstring.strip())
                    else:
                        sections.append(f"A class with {len(cls.methods)} method(s).")
                    sections.append("")
            
            if file_meta.functions:
                sections.append("#### Key Functions\n")
                for func in file_meta.functions:
                    sections.append(f"**{func.name}()**")
                    if func.docstring:
                        sections.append(func.docstring.strip())
                    else:
                        sections.append(f"A function that takes {len(func.parameters)} parameter(s).")
                    sections.append("")
            
            sections.append("---\n")
        
        # Getting started section
        sections.append("## Getting Started\n")
        sections.append("To use this codebase:\n")
        sections.append("1. Review the code structure above")
        sections.append("2. Start with the main entry points")
        sections.append("3. Explore individual modules as needed\n")
        
        return "\n".join(sections)


# Template registry
TEMPLATES = {
    'standard': StandardTemplate(),
    'minimal': MinimalTemplate(),
    'api': APIReferenceTemplate(),
    'tutorial': TutorialTemplate()
}


def get_template(template_name: str) -> DocumentationTemplate:
    """
    Get a documentation template by name.
    
    Args:
        template_name: Name of the template ('standard', 'minimal', 'api', 'tutorial')
        
    Returns:
        DocumentationTemplate instance
        
    Raises:
        ValueError: If template name is not recognized
    """
    template = TEMPLATES.get(template_name.lower())
    if not template:
        raise ValueError(f"Unknown template: {template_name}. Available: {', '.join(TEMPLATES.keys())}")
    return template
