"""
This module provides model configuration for the AELF smart contract code generator.
"""

import os
from typing import cast, Any
from langchain_core.language_models.chat_models import BaseChatModel
from aelf_code_generator.types import AgentState

def get_model(state: AgentState) -> BaseChatModel:
    """
    Get a model based on the environment variable or state configuration.
    """
    state_model = state.get("model")
    model = os.getenv("MODEL", state_model)

    print(f"Using model: {model}")

    if model == "azure_openai":
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_deployment="dapp-factory-gpt-4o",
            azure_endpoint="https://zhife-m5vtfkd0-westus.services.ai.azure.com/",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview",
            temperature=0.7
        )
    if model == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(temperature=0, model="gpt-4")
    if model == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            temperature=0,
            model_name="claude-3-sonnet-20240229",
            timeout=None,
            stop=None
        )
    if model == "google_genai":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            temperature=0,
            model="gemini-1.5-flash",
            api_key=cast(Any, os.getenv("GOOGLE_API_KEY")) or None,
            convert_system_message_to_human=True
        )

    raise ValueError("Invalid model specified") 