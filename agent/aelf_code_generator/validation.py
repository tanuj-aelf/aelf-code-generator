"""
This module handles input validation for the agent.
"""

from typing import Any
from pydantic import BaseModel, ValidationError

class TextInputValidator(BaseModel):
    """Validator for text input."""
    content: str

def validate_input(input_data: Any) -> str:
    """
    Validate and clean input data.
    Returns cleaned text input or raises ValueError.
    """
    try:
        if isinstance(input_data, dict):
            validated = TextInputValidator(**input_data)
            return validated.content.strip()
        elif isinstance(input_data, str):
            return input_data.strip()
        raise ValueError()
    except (ValidationError, ValueError):
        raise ValueError("Please provide a text description. Example: 'I need a DeFi lending platform'") 