"""
This module handles conversion of plain text descriptions into structured contract requirements.
"""

from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from aelf_code_generator.models import ContractRequirements, Method, StateVariable, Event, MethodParameter, MethodReturn, EventParameter
from aelf_code_generator.model import get_model
import json
from pydantic import ValidationError

EXTRACTION_PROMPT = """You are a smart contract requirements analyzer. Your task is to analyze a plain text description 
and extract structured contract requirements. Follow these guidelines:

1. Analyze the description carefully to understand:
   - Core functionality and purpose
   - Required methods and their specifications
   - State variables needed
   - Events that should be emitted
   - Access control requirements

2. Make appropriate assumptions for any missing details while ensuring:
   - The contract remains secure and functional
   - All necessary validations are included
   - Standard patterns are followed
   - Best practices are implemented

3. Structure the output as a JSON object with these fields:
   {
     "description": "Contract description",
     "type": "Contract type/category",
     "features": ["List of main features"],
     "methods": [{
       "name": "MethodName",
       "description": "Method description",
       "params": [{"name": "param", "type": "type", "description": "desc"}],
       "returns": {"type": "type", "description": "desc"},
       "access_control": ["rules"],
       "state_changes": ["changes"],
       "events": ["events"],
       "validation": ["rules"]
     }],
     "state_variables": [{
       "name": "name",
       "type": "type",
       "description": "desc",
       "is_mapping": false,
       "key_type": null,
       "value_type": null
     }],
     "events": [{
       "name": "EventName",
       "description": "Event description",
       "parameters": [{
         "name": "param",
         "type": "type",
         "description": "desc",
         "indexed": false
       }]
     }]
   }

Input Description: {input_text}

Output MUST be a SINGLE JSON OBJECT without markdown formatting or additional text.
BAD EXAMPLE:
```json
{{"description": ...}}
```
GOOD EXAMPLE:
{{"description": ...}}

DO NOT include any explanations, markdown formatting, or additional text. ONLY output the JSON object."""

def create_default_requirements(text: str) -> ContractRequirements:
    """Create default requirements with basic structure."""
    return ContractRequirements(
        description=text,
        type="Basic Contract",
        features=["Basic Functionality"],
        methods=[
            Method(
                name="Initialize",
                description="Initialize the contract state",
                params=[],
                returns=MethodReturn(type="void", description="No return value"),
                access_control=["Owner"],
                state_changes=["Initializes contract state"],
                events=["ContractInitialized"],
                validation=["Owner only"]
            )
        ],
        state_variables=[
            StateVariable(
                name="owner",
                type="Address",
                description="Contract owner address"
            )
        ],
        events=[
            Event(
                name="ContractInitialized",
                description="Emitted when contract is initialized",
                parameters=[
                    EventParameter(
                        name="owner",
                        type="Address",
                        description="Contract owner address",
                        indexed=True
                    )
                ]
            )
        ]
    )

async def extract_requirements(text: str, state: Dict[str, Any] = None) -> ContractRequirements:
    """
    Extract structured contract requirements from plain text description.
    Uses LLM to parse and structure the requirements.
    """
    try:
        # Prepare the prompt
        messages = [
            SystemMessage(content=EXTRACTION_PROMPT.format(input_text=text)),
            HumanMessage(content="Extract the contract requirements into a JSON object. No additional text or formatting.")
        ]

        # Get model response without tools
        model = get_model(state) if state else get_model({})
        response = await model.ainvoke(messages, tools=[])  # Explicitly disable tools
        ai_message = response.content

        # Parse the response into ContractRequirements
        try:
            # Clean and extract JSON from the response
            json_str = ai_message.strip()
            # Remove any markdown formatting
            if "```" in json_str:
                json_str = "".join(line for line in json_str.split("\n") if not line.startswith("```"))
            # Remove any leading/trailing text
            json_str = json_str[json_str.find("{"):json_str.rfind("}")+1]
            
            data = json.loads(json_str)

            # Validate and convert the parsed data
            try:
                # Convert the parsed data into ContractRequirements
                methods = [
                    Method(
                        name=m["name"],
                        description=m["description"],
                        params=[MethodParameter(**p) for p in m["params"]],
                        returns=MethodReturn(**m["returns"]),
                        access_control=m["access_control"],
                        state_changes=m["state_changes"],
                        events=m["events"],
                        validation=m.get("validation", [])
                    )
                    for m in data["methods"]
                ]

                state_variables = [
                    StateVariable(**v)
                    for v in data["state_variables"]
                ]

                events = [
                    Event(
                        name=e["name"],
                        description=e["description"],
                        parameters=[EventParameter(**p) for p in e["parameters"]]
                    )
                    for e in data["events"]
                ]

                requirements = ContractRequirements(
                    description=data["description"],
                    type=data["type"],
                    features=data["features"],
                    methods=methods,
                    state_variables=state_variables,
                    events=events
                )

                return requirements

            except ValidationError as ve:
                print(f"Validation error: {ve}")
                return create_default_requirements(text)

        except json.JSONDecodeError as je:
            print(f"JSON decode error: {je}")
            return create_default_requirements(text)

    except Exception as e:
        print(f"Extraction error: {e}")
        return create_default_requirements(text) 