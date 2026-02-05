"""
Sample Python file for testing the parser
"""


def module_function(x: int, y: int = 10) -> int:
    """
    A module-level function that adds two numbers.
    
    Args:
        x: First number
        y: Second number (default: 10)
    
    Returns:
        Sum of x and y
    """
    return x + y


class Calculator:
    """A simple calculator class for basic arithmetic operations"""
    
    def __init__(self, initial_value: float = 0.0):
        """
        Initialize the calculator with an initial value.
        
        Args:
            initial_value: Starting value (default: 0.0)
        """
        self.value = initial_value
    
    def add(self, amount: float) -> float:
        """Add an amount to the current value"""
        self.value += amount
        return self.value
    
    def subtract(self, amount: float) -> float:
        """Subtract an amount from the current value"""
        self.value -= amount
        return self.value
    
    def reset(self):
        """Reset the calculator to zero"""
        self.value = 0.0


async def async_fetch(url: str, timeout: int = 30) -> dict:
    """
    Asynchronously fetch data from a URL.
    
    Args:
        url: The URL to fetch from
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary containing the response data
    """
    pass


def flexible_function(*args, **kwargs):
    """A function that accepts any arguments"""
    pass
