"""
Sample Python module for testing the AI Code Documentation Generator.

This module demonstrates various Python code patterns including classes,
methods, functions, and different parameter styles.
"""

class UserManager:
    """
    Manages user accounts and authentication.
    
    This class provides methods for creating, updating, and authenticating users.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize the UserManager with a database connection.
        
        Args:
            database_url: The URL of the database to connect to
        """
        self.database_url = database_url
        self.users = {}
    
    def create_user(self, username: str, email: str, password: str) -> dict:
        """
        Create a new user account.
        
        Args:
            username: The unique username for the account
            email: The user's email address
            password: The user's password (will be hashed)
        
        Returns:
            A dictionary containing the created user's information
        """
        user_id = len(self.users) + 1
        user = {
            'id': user_id,
            'username': username,
            'email': email,
            'password': self._hash_password(password)
        }
        self.users[user_id] = user
        return user
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate a user with username and password.
        
        Args:
            username: The username to authenticate
            password: The password to verify
        
        Returns:
            True if authentication succeeds, False otherwise
        """
        for user in self.users.values():
            if user['username'] == username:
                return user['password'] == self._hash_password(password)
        return False
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password for secure storage.
        
        Args:
            password: The plain text password
        
        Returns:
            The hashed password
        """
        # Simple hash for demonstration purposes
        return f"hashed_{password}"


def calculate_discount(price: float, discount_percent: float = 10.0) -> float:
    """
    Calculate the discounted price.
    
    Args:
        price: The original price
        discount_percent: The discount percentage (default: 10.0)
    
    Returns:
        The price after applying the discount
    """
    discount_amount = price * (discount_percent / 100)
    return price - discount_amount


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format a monetary amount with currency symbol.
    
    Args:
        amount: The monetary amount
        currency: The currency code (default: "USD")
    
    Returns:
        Formatted currency string
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    symbol = symbols.get(currency, "$")
    return f"{symbol}{amount:.2f}"


class DataProcessor:
    """Process and transform data collections."""
    
    def filter_data(self, data: list, condition) -> list:
        """
        Filter data based on a condition function.
        
        Args:
            data: The list of items to filter
            condition: A function that returns True for items to keep
        
        Returns:
            A new list containing only items that match the condition
        """
        return [item for item in data if condition(item)]
    
    def transform_data(self, data: list, transformer) -> list:
        """
        Transform each item in the data collection.
        
        Args:
            data: The list of items to transform
            transformer: A function to apply to each item
        
        Returns:
            A new list with transformed items
        """
        return [transformer(item) for item in data]
