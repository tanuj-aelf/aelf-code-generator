"""
This module analyzes GitHub repositories for smart contract patterns.
"""

from typing import cast, Dict, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from aelf_code_generator.state import AgentState, STATE_KEYS
from aelf_code_generator.model import get_model
import json

class ProcessRequirementsInput:
    """Input schema for processing contract requirements."""
    def __init__(self, description: str, contract_type: str = "", features: List[str] = None):
        self.description = description
        self.contract_type = contract_type
        self.features = features or []

async def github_analyzer_node(state: AgentState, config: dict) -> AgentState:
    """
    Analyzes GitHub repositories for smart contract patterns and updates state.
    """
    try:
        # Initialize state fields if not present
        if "github_analysis" not in state:
            state["github_analysis"] = ""
        if "contract_methods" not in state:
            state["contract_methods"] = []
        if "state_variables" not in state:
            state["state_variables"] = []
        if "contract_events" not in state:
            state["contract_events"] = []
        if "contract_type" not in state:
            state["contract_type"] = ""
        if "contract_features" not in state:
            state["contract_features"] = []

        # Parse requirements into structured format
        if isinstance(state.get("user_requirements"), str):
            try:
                raw_requirements = json.loads(state["user_requirements"])
            except json.JSONDecodeError:
                raw_requirements = {"description": state["user_requirements"]}
        else:
            raw_requirements = state.get("user_requirements", {})

        # Create structured requirements object
        requirements = ProcessRequirementsInput(
            description=raw_requirements.get("description", ""),
            contract_type=raw_requirements.get("type", state.get("contract_type", "")),
            features=raw_requirements.get("features", state.get("contract_features", []))
        )

        model = get_model(state)

        # Analyze requirements and extract contract specifications
        analysis_prompt = f"""Analyze the following smart contract requirements and extract detailed specifications:

Requirements Description: {requirements.description}
Contract Type: {requirements.contract_type}
Features: {', '.join(requirements.features)}

Please extract and structure the following components as a JSON object:

1. Contract Methods (Array of objects with):
   - name: string
   - description: string
   - params: array of objects with name, type, description
   - returns: object with type and description
   - access_control: array of strings
   - state_changes: array of strings
   - events: array of strings
   - validation: array of strings

2. State Variables (Array of objects with):
   - name: string
   - type: string
   - description: string
   - is_mapping: boolean
   - key_type: string (if is_mapping is true)
   - value_type: string (if is_mapping is true)

3. Events (Array of objects with):
   - name: string
   - description: string
   - parameters: array of objects with name, type, description, indexed

Example format:
{{
    "methods": [
        {{
            "name": "CreateTask",
            "description": "Creates a new task",
            "params": [
                {{
                    "name": "title",
                    "type": "string",
                    "description": "Task title"
                }}
            ],
            "returns": {{
                "type": "void",
                "description": "No return value"
            }},
            "access_control": ["Owner"],
            "state_changes": ["Tasks mapping updated"],
            "events": ["TaskCreated"],
            "validation": ["Title not empty"]
        }}
    ],
    "state_variables": [
        {{
            "name": "Tasks",
            "type": "mapping",
            "description": "Stores all tasks",
            "is_mapping": true,
            "key_type": "long",
            "value_type": "Task"
        }}
    ],
    "events": [
        {{
            "name": "TaskCreated",
            "description": "Emitted when a new task is created",
            "parameters": [
                {{
                    "name": "taskId",
                    "type": "long",
                    "description": "ID of the created task",
                    "indexed": true
                }}
            ]
        }}
    ]
}}"""

        # Get analysis from model
        response = await model.ainvoke([HumanMessage(content=analysis_prompt)])
        ai_message = cast(AIMessage, response)

        try:
            # Parse the response as JSON
            analysis_result = json.loads(ai_message.content)
            
            # Update state with structured data
            state["contract_methods"] = analysis_result.get("methods", [])
            state["state_variables"] = analysis_result.get("state_variables", [])
            state["contract_events"] = analysis_result.get("events", [])
            state[STATE_KEYS["contract_type"]] = requirements.contract_type
            state[STATE_KEYS["contract_features"]] = requirements.features
            
            # Add analysis summary
            state["github_analysis"] = f"""Analysis completed successfully:
- Methods: {len(state['contract_methods'])} defined
- State Variables: {len(state['state_variables'])} defined
- Events: {len(state['contract_events'])} defined"""

        except json.JSONDecodeError:
            # Set default structured data for a basic contract
            state["contract_methods"] = [{
                "name": "Initialize",
                "description": "Initializes the contract state",
                "params": [],
                "returns": {"type": "void", "description": "No return value"},
                "access_control": ["Admin"],
                "state_changes": ["Initializes contract state"],
                "events": ["Initialized"],
                "validation": ["Contract not already initialized"]
            }]
            
            state["state_variables"] = [{
                "name": "State",
                "type": "ContractState",
                "description": "Main contract state container",
                "is_mapping": False
            }]
            
            state["contract_events"] = [{
                "name": "Initialized",
                "description": "Emitted when contract is initialized",
                "parameters": [{
                    "name": "initializer",
                    "type": "Address",
                    "description": "Address that initialized the contract",
                    "indexed": True
                }]
            }]
            
            state["github_analysis"] = "Basic contract structure created with default patterns."

    except Exception as e:
        # Set safe defaults if analysis fails
        state["github_analysis"] = f"Analysis error: {str(e)}. Using default patterns."
        if "contract_methods" not in state or not state["contract_methods"]:
            state["contract_methods"] = []
        if "state_variables" not in state or not state["state_variables"]:
            state["state_variables"] = []
        if "contract_events" not in state or not state["contract_events"]:
            state["contract_events"] = []

    return state 