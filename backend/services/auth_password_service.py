"""
Password Authentication Service
Handles password hashing, verification, and strength validation for hybrid auth (P2).
"""

from passlib.context import CryptContext
from typing import Tuple

# P2: Initialize password context with bcrypt (rounds >= 12 for security)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configure bcrypt rounds (minimum 12 for security, default is 12)
# Higher rounds = more secure but slower (12 is good balance)
pwd_context.bcrypt_rounds = 12


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password (must be a string, max 72 bytes)
        
    Returns:
        Hashed password string (bcrypt)
    
    Raises:
        ValueError: If password is not a string or exceeds 72 bytes
    """
    # P0: Ensure password is a string (not an object)
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
    
    # P0: Validate password length (bcrypt max 72 bytes)
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password cannot exceed 72 bytes (bcrypt limitation)")
    
    # Hash only the string password
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Invalid hash format or other error
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 digit
    
    Args:
        password: Plain text password to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message is empty string
    """
    if len(password) < 8:
        return False, "Minimum 8 caractères requis"
    
    if not any(c.isupper() for c in password):
        return False, "Au moins 1 majuscule requise"
    
    if not any(c.isdigit() for c in password):
        return False, "Au moins 1 chiffre requis"
    
    # Optional: Check for special characters (not required but recommended)
    # if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
    #     return False, "Au moins 1 caractère spécial requis"
    
    return True, ""







