"""
Utility helper functions for the test workspace.

This module provides common utility functions used across the application.
"""

def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email: The email address to validate
    
    Returns:
        True if the email format is valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_input(text: str, max_length: int = 255) -> str:
    """
    Sanitize user input by removing dangerous characters and limiting length.
    
    Args:
        text: The input text to sanitize
        max_length: Maximum allowed length (default: 255)
    
    Returns:
        The sanitized text
    """
    # Remove potentially dangerous characters
    sanitized = text.replace('<', '').replace('>', '').replace('&', '')
    # Trim to max length
    return sanitized[:max_length]


class Logger:
    """Simple logging utility for the application."""
    
    def __init__(self, name: str):
        """
        Initialize the logger with a name.
        
        Args:
            name: The name of the logger
        """
        self.name = name
        self.logs = []
    
    def info(self, message: str) -> None:
        """
        Log an informational message.
        
        Args:
            message: The message to log
        """
        self.logs.append(f"[INFO] {self.name}: {message}")
    
    def error(self, message: str) -> None:
        """
        Log an error message.
        
        Args:
            message: The error message to log
        """
        self.logs.append(f"[ERROR] {self.name}: {message}")
    
    def get_logs(self) -> list:
        """
        Get all logged messages.
        
        Returns:
            A list of all log messages
        """
        return self.logs.copy()
