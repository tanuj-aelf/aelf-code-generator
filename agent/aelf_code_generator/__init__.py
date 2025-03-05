"""
AELF Smart Contract Code Generator.
"""

from aelf_code_generator.types import AgentState, get_default_state
from aelf_code_generator.demo import app
from aelf_code_generator.templates import (
    initialize_blank_template,
    get_contract_tree_structure
)

__all__ = [
    "AgentState", 
    "get_default_state", 
    "app",
    "initialize_blank_template",
    "get_contract_tree_structure"
] 