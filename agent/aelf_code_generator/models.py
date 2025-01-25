"""
This module defines the data models for contract requirements.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class MethodParameter(BaseModel):
    """Parameter specification for a method."""
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type")
    description: str = Field(description="Parameter description")

class MethodReturn(BaseModel):
    """Return value specification for a method."""
    type: str = Field(description="Return type")
    description: str = Field(description="Return value description")

class Method(BaseModel):
    """Method specification."""
    name: str = Field(description="Method name")
    description: str = Field(description="Method description")
    params: List[MethodParameter] = Field(description="Method parameters", default_factory=list)
    returns: MethodReturn = Field(description="Return value specification")
    access_control: List[str] = Field(description="Access control rules", default_factory=list)
    state_changes: List[str] = Field(description="State changes made by the method", default_factory=list)
    events: List[str] = Field(description="Events emitted by the method", default_factory=list)
    validation: List[str] = Field(description="Validation rules", default_factory=list)

class StateVariable(BaseModel):
    """State variable specification."""
    name: str = Field(description="Variable name")
    type: str = Field(description="Variable type")
    description: str = Field(description="Variable description")
    is_mapping: bool = Field(description="Whether this is a mapping type", default=False)
    key_type: Optional[str] = Field(description="Key type for mapping", default=None)
    value_type: Optional[str] = Field(description="Value type for mapping", default=None)

class EventParameter(BaseModel):
    """Event parameter specification."""
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type")
    description: str = Field(description="Parameter description")
    indexed: bool = Field(description="Whether the parameter is indexed", default=False)

class Event(BaseModel):
    """Event specification."""
    name: str = Field(description="Event name")
    description: str = Field(description="Event description")
    parameters: List[EventParameter] = Field(description="Event parameters", default_factory=list)

class ContractRequirements(BaseModel):
    """Complete contract requirements specification."""
    description: str = Field(description="Contract description")
    type: str = Field(description="Contract type")
    features: List[str] = Field(description="Contract features", default_factory=list)
    methods: List[Method] = Field(description="Contract methods", default_factory=list)
    state_variables: List[StateVariable] = Field(description="State variables", default_factory=list)
    events: List[Event] = Field(description="Events", default_factory=list) 