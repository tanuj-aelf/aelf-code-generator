"""
This module defines the main agent workflow for AELF smart contract code generation.
"""

import os
import traceback
import re
import json
import glob
import hashlib
import logging
import time
import random
from typing import Dict, List, Any, Annotated, Literal, Optional, Tuple, Set
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph.message import add_messages
from langgraph.types import Command
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from aelf_code_generator.model import get_model
from aelf_code_generator.types import AgentState, ContractOutput, CodebaseInsight, get_default_state
from datetime import datetime
from pathlib import Path
import sys
import asyncio
from aelf_code_generator.prompts import (
    SYSTEM_PROMPT,
    CODE_GENERATION_PROMPT,
    CODEBASE_ANALYSIS_PROMPT,
    UI_GENERATION_PROMPT,
    TESTING_PROMPT,
    DOCUMENTATION_PROMPT,
    ANALYSIS_PROMPT,
    VALIDATION_PROMPT,
    PROTO_GENERATION_PROMPT
)
from openai import NotFoundError

# Utility function to generate request IDs for tracking
def get_request_id():
    """Generate a unique request ID for tracking RAG operations."""
    return f"req_{int(time.time())}_{random.randint(1000, 9999)}"

# RAG Configuration
RAG_CONFIG = {
    "embedding_model": "models/embedding-001",  # Google AI embedding model to use
    "samples_dir": str(Path(__file__).parent.parent.parent.parent / "aelf-samples"),  # Path to aelf-samples directory
    "vector_store_dir": str(Path(__file__).parent / "vector_store"),  # Path to store vector database
    "excluded_dirs": [".git", "bin", "obj", "node_modules", ".idea", ".vs", "packages"],  # Directories to exclude
    "chunk_size": 1000,                           # Size of code chunks for embedding
    "chunk_overlap": 200,                         # Overlap between chunks
    "retrieval_k": 5,                             # Number of samples to retrieve
    "file_extensions": [".cs", ".proto", ".csproj"] # File extensions to index
}

# Configure logging
def setup_logging():
    """Configure and initialize logging for the RAG system."""
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [RAG] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create a file handler for persistent logging
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"rag_{timestamp}.log"
    
    # Set up file handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Set up console handler for terminal output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Get the logger and add handlers
    logger = logging.getLogger('aelf_rag')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
            
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log setup info
    logger.info(f"Logging initialized to {log_file}")
    
    return logger

# Initialize logging
logging.basicConfig(level=logging.INFO)  # Basic config for other loggers
logger = setup_logging()  # Enhanced logging for RAG

# After configuration, log the RAG config
logger.info(f"RAG Config: {RAG_CONFIG}")

# Define the internal state type with annotation for multiple updates
InternalStateType = Annotated[Dict, "internal"]

# Note: When using gemini-2.0-flash, system messages are converted to human messages
# This is handled by the ChatGoogleGenerativeAI class with convert_system_message_to_human=True

# Track RAG data indexing status to avoid reindexing for each run
_RAG_INDEX_INITIALIZED = False
_RAG_VECTOR_STORE = None
_RAG_FILE_CACHE = {}

def get_embeddings() -> Embeddings:
    """Get the embeddings model for RAG."""
    import os
    
    logger.info(f"Using embedding model: {RAG_CONFIG['embedding_model']}")
    
    # Check embedding model preference (separate from main model)
    embedding_model_type = os.getenv("EMBEDDING_MODEL", os.getenv("MODEL", "")).lower()
    
    # Use Google Gemini if configured
    if embedding_model_type == "gemini" or embedding_model_type == "google_genai":
        logger.info("Using Google Gemini for embeddings")
        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found but required for Gemini embeddings")
        
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            
            logger.info("Initializing Google embedding model: models/embedding-001")
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=google_api_key
            )
            
            # Test the embeddings with a simple query
            embeddings.embed_query("test")
            logger.info("Successfully connected to Google embedding model")
            return embeddings
        except Exception as e:
            logger.error(f"Error with Google embeddings: {str(e)}")
            raise ValueError(f"Failed to initialize Google embeddings: {str(e)}")
    
    # Check if we're using Azure OpenAI
    elif embedding_model_type == "azure_openai":
        logger.info("Using Azure OpenAI for embeddings")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_ENDPOINT", "https://zhife-m5vtfkd0-westus.services.ai.azure.com")
        azure_api_version = os.getenv("AZURE_API_VERSION", "2024-02-15-preview")
        
        # List of common Azure embedding deployment names to try
        azure_deployment_names = [
            "text-embedding-ada-002",  # Most common
            "text-embedding-3-small",  # Newer model
            "ada",                     # Sometimes used
            "embedding",               # Generic name
            "ada-embedding",           # Another variant
        ]
        
        # Try to use the deployment name from env if specified
        env_deployment = os.getenv("AZURE_EMBEDDING_DEPLOYMENT")
        if env_deployment and env_deployment not in azure_deployment_names:
            azure_deployment_names.insert(0, env_deployment)
        
        if not azure_api_key:
            raise ValueError("Azure OpenAI API key not found but required for Azure embeddings")
        
        # Try multiple deployment names until one works
        for deployment in azure_deployment_names:
            try:
                logger.info(f"Trying Azure deployment: {deployment}")
                embeddings = AzureOpenAIEmbeddings(
                    azure_deployment=deployment,
                    azure_endpoint=azure_endpoint,
                    api_version=azure_api_version,
                    api_key=azure_api_key
                )
                # Test the embeddings with a simple query
                embeddings.embed_query("test")
                logger.info(f"Successfully connected to Azure embedding model: {deployment}")
                return embeddings
            except NotFoundError:
                logger.warning(f"Azure deployment '{deployment}' not found, trying next option")
                continue
            except Exception as e:
                logger.warning(f"Error with Azure deployment '{deployment}': {str(e)}")
                continue
        
        raise ValueError("All Azure deployment attempts failed")
    
    # If we get here, we don't have a valid model type
    raise ValueError(f"Unsupported model type: {embedding_model_type}. Please set MODEL environment variable to 'gemini' or 'azure_openai'")

async def initialize_rag_index(force_rebuild: bool = False) -> VectorStore:
    """
    Initialize the RAG index for AELF samples
    """
    logger.info("Initializing RAG index")
    start_time = time.time()
    
    try:
        # Get embeddings model based on configuration
        embed_model = get_embeddings()
        logger.info(f"Using embedding model: {RAG_CONFIG['embedding_model']}")
        
        # Get path to aelf-samples
        samples_dir = Path(RAG_CONFIG["samples_dir"])
        vector_store_dir = Path(RAG_CONFIG["vector_store_dir"])
        
        # Create vector store directory if it doesn't exist
        vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Path to FAISS index
        index_path = vector_store_dir / "faiss_index"
        
        # Check if index already exists
        if index_path.exists() and not force_rebuild:
            try:
                logger.info(f"Loading existing vector store from {index_path}")
                # Load existing FAISS index
                vectorstore = FAISS.load_local(
                    str(index_path),
                    embed_model,
                    allow_dangerous_deserialization=True
                )
                
                # Check if index is valid by running a test query
                test_result = vectorstore.similarity_search("test", k=1)
                logger.info(f"Vector store loaded successfully, contains {len(vectorstore.index_to_docstore_id)} documents")
                return vectorstore
            except Exception as e:
                logger.warning(f"Error loading existing vector store: {str(e)}")
                logger.info("Will rebuild vector store")
                # Continue to rebuild index
                pass
                
        # If we get here, we need to create a new index
        logger.info(f"Building new vector store from {samples_dir}")
        
        # Check if samples directory exists
        if not samples_dir.exists():
            logger.error(f"Samples directory not found: {samples_dir}")
            raise FileNotFoundError(f"Samples directory not found: {samples_dir}")
            
        # Count total files to index
        logger.info("Scanning aelf-samples directory for files to index")
        total_files = 0
        for ext in RAG_CONFIG["file_extensions"]:
            pattern = str(samples_dir / "**" / f"*{ext}")
            found_files = glob.glob(pattern, recursive=True)
            total_files += len(found_files)
        
        logger.info(f"Found {total_files} total files with extensions {RAG_CONFIG['file_extensions']}")
        
        # Create a list of all files to index
        files_to_index = []
        for ext in RAG_CONFIG["file_extensions"]:
            pattern = str(samples_dir / "**" / f"*{ext}")
            found_files = glob.glob(pattern, recursive=True)
            
            for file in found_files:
                skip = False
                for excluded in RAG_CONFIG["excluded_dirs"]:
                    if f"/{excluded}/" in file or file.endswith(f"/{excluded}"):
                        skip = True
                        break
                
                if not skip:
                    files_to_index.append(file)
        
        logger.info(f"Indexing {len(files_to_index)} files after excluding directories {RAG_CONFIG['excluded_dirs']}")
        
        # Load documents
        documents = []
        indexed_files = 0
        
        for file_path in files_to_index:
            try:
                # Read file content
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Skip empty files
                if not content.strip():
                    continue
                    
                # Get relative path for better identification
                rel_path = os.path.relpath(file_path, str(samples_dir))
                
                # Determine project from path
                project = rel_path.split("/")[0] if "/" in rel_path else "root"
                
                # Get file extension for type identification
                _, ext = os.path.splitext(file_path)
                
                # Create metadata
                metadata = {
                    "source": rel_path,
                    "project": project,
                    "file_type": ext[1:] if ext.startswith(".") else ext  # Remove leading dot
                }
                
                # Add to documents
                documents.append(Document(page_content=content, metadata=metadata))
                indexed_files += 1
                
                # Log progress periodically
                if indexed_files % 50 == 0:
                    logger.info(f"Indexed {indexed_files}/{len(files_to_index)} files...")
                
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {str(e)}")
                continue
                
        if not documents:
            logger.error("No documents found to index")
            raise ValueError("No documents found to index")
            
        logger.info(f"Successfully loaded {len(documents)} documents")
        
        # Create text splitter for code
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=RAG_CONFIG["chunk_size"],
            chunk_overlap=RAG_CONFIG["chunk_overlap"],
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Split documents into chunks
        logger.info(f"Splitting documents into chunks (size={RAG_CONFIG['chunk_size']}, overlap={RAG_CONFIG['chunk_overlap']})")
        splits = text_splitter.split_documents(documents)
        logger.info(f"Created {len(splits)} chunks from {len(documents)} documents")
        
        # Create FAISS index
        logger.info("Creating FAISS index from chunks")
        vectorstore = FAISS.from_documents(splits, embed_model)
        
        # Save index
        logger.info(f"Saving vector store to {index_path}")
        vectorstore.save_local(str(index_path))
        
        total_time = time.time() - start_time
        logger.info(f"RAG index initialization completed in {total_time:.2f} seconds")
        
        return vectorstore
        
    except Exception as e:
        logger.error(f"Error initializing RAG index: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def retrieve_relevant_samples(query: str, 
                                   contract_type: Optional[str] = None, 
                                   k: int = RAG_CONFIG["retrieval_k"]) -> List[Dict]:
    """
    Retrieve relevant code samples from the vector store
    """
    if k is None:
        k = RAG_CONFIG["retrieval_k"]
        
    try:
        logger.info(f"Retrieving samples for query: '{query}' (contract_type={contract_type}, k={k})")
        start_time = time.time()
        
        # Initialize vector store
        vectorstore = await initialize_rag_index()
        
        # Create a composite query by combining the query with contract type
        search_query = query
        if contract_type:
            search_query = f"{contract_type}: {query}"
            
        logger.info(f"Using search query: '{search_query}'")
        
        # Search for relevant documents
        docs = vectorstore.similarity_search(search_query, k=k)
        
        # Format results as samples
        samples = []
        for doc in docs:
            metadata = doc.metadata
            samples.append({
                "content": doc.page_content,
                "source": metadata.get("source", "unknown"),
                "project": metadata.get("project", "unknown"),
                "file_type": metadata.get("file_type", "unknown")
            })
            
        retrieval_time = time.time() - start_time
        logger.info(f"Retrieved {len(samples)} samples in {retrieval_time:.2f} seconds")
        
        # Log some details about the retrieved samples
        if samples:
            sample_info = "\n".join([f"- {s['source']} ({s['project']})" for s in samples[:3]])
            logger.info(f"Top sample sources:\n{sample_info}")
        
        return samples
        
    except Exception as e:
        logger.error(f"Error retrieving samples: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def format_code_samples_for_prompt(samples: List[Dict]) -> str:
    """
    Format code samples for inclusion in a prompt.
    
    Args:
        samples: List of sample dictionaries returned by retrieve_relevant_samples
        
    Returns:
        Formatted string with code samples for prompt inclusion
    """
    if not samples:
        logger.info("No samples to format")
        return "No relevant code samples found."
        
    logger.info(f"Formatting {len(samples)} code samples for prompt")
    
    # Group samples by project
    samples_by_project = {}
    for sample in samples:
        project = sample.get("project", "unknown")
        if project not in samples_by_project:
            samples_by_project[project] = []
        samples_by_project[project].append(sample)
        
    # Format samples
    formatted_samples = []
    
    for project, project_samples in samples_by_project.items():
        # Add project header
        formatted_samples.append(f"## Project: {project}")
        
        # Add samples from this project
        for i, sample in enumerate(project_samples):
            source = sample.get("source", "unknown")
            file_type = sample.get("file_type", "unknown")
            content = sample.get("content", "")
            
            # Truncate content if too long (limit to ~3000 chars)
            if len(content) > 3000:
                content = content[:3000] + "\n...(truncated)..."
                
            # Format sample
            formatted_sample = f"### Sample {i+1}: {source}\nType: {file_type}\n```\n{content}\n```\n"
            formatted_samples.append(formatted_sample)
            
    # Join all formatted samples
    result = "\n".join(formatted_samples)
    
    # Log stats about the formatted output
    logger.info(f"Formatted {len(samples)} samples from {len(samples_by_project)} projects, total length: {len(result)} chars")
    
    return result

async def generate_proto_file_content(model, proto_file_path: str) -> str:
    """Generate content for an AELF-specific proto file using the LLM."""
    try:
        # Generate proto file content using the LLM
        messages = [
            SystemMessage(content=PROTO_GENERATION_PROMPT.format(proto_file_path=proto_file_path)),
            HumanMessage(content=f"Please generate the content for the AELF proto file: {proto_file_path}")
        ]
        
        # Use a shorter timeout for proto generation - these are smaller files
        response = await model.ainvoke(messages, timeout=60)
        content = response.content.strip()
        
        if not content or "```" in content:
            # If the model returned markdown or empty content, clean it up
            content = content.replace("```protobuf", "").replace("```proto", "").replace("```", "").strip()
            
        if not content:
            print(f"Warning: LLM generated empty content for {proto_file_path}")
            # Generate minimal valid proto file with correct package name
            package_name = proto_file_path.split("/")[-1].replace(".proto", "")
            if "aelf/" in proto_file_path:
                package_name = "aelf"
            elif "acs" in proto_file_path:
                package_name = proto_file_path.split("/")[-1].replace(".proto", "")
            
            return f"""syntax = "proto3";

// This is a minimal placeholder generated for {proto_file_path}
// The LLM was unable to generate proper content
package {package_name};

// Please review and complete this proto file manually
"""
            
        return content
    except Exception as e:
        print(f"Error generating proto content for {proto_file_path}: {str(e)}")
        # Generate minimal valid proto file with package name derived from path
        package_name = proto_file_path.split("/")[-1].replace(".proto", "")
        if "aelf/" in proto_file_path:
            package_name = "aelf"
        elif "acs" in proto_file_path:
            package_name = proto_file_path.split("/")[-1].replace(".proto", "")
        
        return f"""syntax = "proto3";

// This is a minimal placeholder generated for {proto_file_path}
// Error during generation: {str(e)}
package {package_name};

// Please review and complete this proto file manually
"""

async def analyze_requirements(state: AgentState) -> Command[Literal["analyze_codebase", "__end__"]]:
    """Analyze the dApp description and provide detailed requirements analysis."""
    try:
        # Initialize internal state if not present
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
            
        # Get model with state
        model = get_model(state)
        
        # Generate analysis
        messages = [
            SystemMessage(content=ANALYSIS_PROMPT),
            HumanMessage(content=state["input"])
        ]
        
        response = await model.ainvoke(messages)
        analysis = response.content.strip()
        
        if not analysis:
            raise ValueError("Analysis generation failed - empty response")
            
        # Create internal state with analysis
        internal_state = state["generate"]["_internal"]
        internal_state["analysis"] = analysis
        internal_state["output"] = {
            **internal_state.get("output", {}),
            "analysis": analysis
        }
        
        # Return command to move to next state
        return Command(
            goto="analyze_codebase",
            update={
                "generate": {
                    "_internal": internal_state
                }
            }
        )
        
    except Exception as e:
        print(f"Error in analyze_requirements: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        
        # Initialize internal state if it doesn't exist
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
        
        # Create error state
        error_state = state["generate"]["_internal"]
        error_state["analysis"] = f"Error analyzing requirements: {str(e)}"
        error_state["output"] = {
            **error_state.get("output", {}),
            "analysis": f"Error analyzing requirements: {str(e)}"
        }
        
        # Return error state
        return Command(
            goto="__end__",
            update={
                "generate": {
                    "_internal": error_state
                }
            }
        )

async def analyze_codebase(state: AgentState) -> Command[Literal["generate_code", "__end__"]]:
    """Analyze AELF sample codebases to gather implementation insights."""
    try:
        # Initialize internal state if not present
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
            
        # Get analysis from internal state
        internal_state = state["generate"]["_internal"]
        analysis = internal_state.get("analysis", "")
        
        logger.info("Starting codebase analysis with RAG")
        request_id = get_request_id()
        logger.info(f"Request ID: {request_id}")
        
        if not analysis:
            logger.warning("No analysis provided, using generic implementation")
            analysis = "No analysis provided. Proceeding with generic AELF contract implementation."
            internal_state["analysis"] = analysis
        
        # Extract contract type from analysis for better targeting
        contract_types = []
        contract_type = None
        
        # Log a summary of the analysis for debugging
        analysis_summary = analysis[:200] + "..." if len(analysis) > 200 else analysis
        logger.info(f"Analysis summary: {analysis_summary}")
        
        # Look for contract type mentions in the analysis
        contract_type_keywords = {
            "lottery": "lottery game",
            "voting": "voting contract",
            "dao": "dao contract",
            "token": "token contract",
            "nft": "nft contract",
            "staking": "staking contract",
            "game": "game contract",
            "expense": "expense tracker",
            "auction": "auction contract",
            "allowance": "allowance contract"
        }
        
        analysis_lower = analysis.lower()
        for keyword, type_name in contract_type_keywords.items():
            if keyword in analysis_lower:
                contract_types.append(type_name)
        
        if contract_types:
            # Use the first identified contract type for retrieval
            contract_type = contract_types[0]
            logger.info(f"[{request_id}] Identified contract type: {contract_type}")
        else:
            logger.info(f"[{request_id}] No specific contract type identified")
        
        # Generate queries based on analysis
        queries = []
        
        # Create targeted queries based on analysis keywords and content
        if "state" in analysis_lower and "variable" in analysis_lower:
            queries.append("state variables and storage")
            
        if "method" in analysis_lower or "function" in analysis_lower:
            queries.append("contract methods and functions")
            
        if "event" in analysis_lower:
            queries.append("contract events")
            
        if "access" in analysis_lower or "owner" in analysis_lower or "permission" in analysis_lower:
            queries.append("access control and permissions")
        
        # Add a general query based on contract type
        if contract_type:
            queries.append(f"{contract_type} implementation")
        else:
            # If no specific type was identified, use a generic query
            queries.append("AELF smart contract implementation")
            
        # Create a targeted query from the first paragraph of analysis
        first_paragraph = analysis.split("\n\n")[0] if "\n\n" in analysis else analysis.split("\n")[0]
        if len(first_paragraph) > 30:  # Ensure it's substantial enough
            queries.append(first_paragraph[:200])  # Limit length
            
        logger.info(f"[{request_id}] Generated {len(queries)} queries for RAG retrieval: {queries}")
        
        # Get model to analyze requirements
        model = get_model(state)
        
        # Retrieve relevant code samples from aelf-samples
        all_samples = []
        logger.info(f"[{request_id}] Starting sample retrieval process")
        start_time = time.time()
        
        for i, query in enumerate(queries):
            try:
                logger.info(f"[{request_id}] Processing query {i+1}/{len(queries)}: '{query}'")
                samples = await retrieve_relevant_samples(query, contract_type)
                
                # Only add new samples that aren't duplicates
                seen_sources = {s["source"] for s in all_samples}
                new_samples = 0
                
                for sample in samples:
                    if sample["source"] not in seen_sources:
                        all_samples.append(sample)
                        seen_sources.add(sample["source"])
                        new_samples += 1
                
                logger.info(f"[{request_id}] Added {new_samples} new samples from query {i+1}")
                
                # Limit total samples to prevent token overflow
                if len(all_samples) >= RAG_CONFIG["retrieval_k"] * 2:
                    logger.info(f"[{request_id}] Reached sample limit ({len(all_samples)}), stopping retrieval")
                    break
            except Exception as e:
                logger.error(f"[{request_id}] Error retrieving samples for query '{query}': {str(e)}")
                # Continue with other queries even if one fails
                continue
                
        retrieval_time = time.time() - start_time
        logger.info(f"[{request_id}] Retrieved {len(all_samples)} total samples in {retrieval_time:.2f} seconds")
        
        # Log sample sources for debugging
        sample_sources = [f"{s['source']} ({s['project']})" for s in all_samples[:5]]
        logger.info(f"[{request_id}] Top samples: {sample_sources}")
                
        # Format samples for prompt inclusion
        formatted_samples = format_code_samples_for_prompt(all_samples)
        
        # Store retrieved samples in internal state
        logger.info(f"[{request_id}] Storing {len(all_samples)} samples in internal state")
        internal_state["retrieved_samples"] = [{
            "source": sample["source"],
            "project": sample["project"],
            "file_type": sample["file_type"]
        } for sample in all_samples]
        
        # Generate codebase insights with improved prompt
        logger.info(f"[{request_id}] Generating codebase insights with LLM")
        messages = [
            SystemMessage(content=CODEBASE_ANALYSIS_PROMPT),
            HumanMessage(content=f"""
Based on the following contract requirements and the provided code samples from the aelf-samples repository, provide implementation insights and patterns for an AELF smart contract.

Contract Requirements:
{analysis}

Retrieved Code Samples:
{formatted_samples}

Please provide structured insights focusing on:

1. Project Structure and Organization
   - Required contract files and their purpose
   - State variables and their types
   - Events and their parameters
   - Contract references needed

2. Smart Contract Patterns
   - State management patterns
   - Access control patterns needed
   - Event handling patterns
   - Common utility functions
   - Error handling strategies

3. Implementation Guidelines
   - Best practices for AELF contracts
   - Security considerations
   - Performance optimizations
   - Testing approaches

4. Code Examples
   - Key methods to implement
   - Common features needed
   - Pitfalls to avoid

Your insights will guide the code generation process.""")
        ]
        
        try:
            logger.info(f"[{request_id}] Invoking LLM for codebase analysis")
            start_time = time.time()
            
            response = await model.ainvoke(messages, timeout=150)
            insights = response.content.strip()
            
            analysis_time = time.time() - start_time
            logger.info(f"[{request_id}] LLM analysis completed in {analysis_time:.2f} seconds")
            
            if not insights:
                logger.error(f"[{request_id}] Codebase analysis failed - empty response")
                raise ValueError("Codebase analysis failed - empty response")
                
            # Log a summary of the insights
            insights_summary = insights[:200] + "..." if len(insights) > 200 else insights
            logger.info(f"[{request_id}] Insights summary: {insights_summary}")
                
            # Split insights into sections
            sections = insights.split("\n\n")
            
            # Extract sections based on headers
            project_structure = ""
            coding_patterns = ""
            implementation_guidelines = insights  # Keep full response as guidelines
            
            for i, section in enumerate(sections):
                section_lower = section.lower()
                if any(header in section_lower for header in ["project structure", "file structure", "organization"]):
                    project_structure = section
                    # Look ahead for subsections
                    for next_section in sections[i+1:]:
                        if not any(header in next_section.lower() for header in ["pattern", "guideline", "implementation"]):
                            project_structure += "\n\n" + next_section
                        else:
                            break
                elif any(header in section_lower for header in ["pattern", "practice", "common"]):
                    coding_patterns = section
                    # Look ahead for subsections
                    for next_section in sections[i+1:]:
                        if not any(header in next_section.lower() for header in ["guideline", "implementation", "structure"]):
                            coding_patterns += "\n\n" + next_section
                        else:
                            break
            
            # Ensure we have content for each section
            if not project_structure:
                logger.warning(f"[{request_id}] No project structure section found, using default")
                project_structure = """Standard AELF project structure:
1. Main Contract Implementation (ContractName.cs)
   - Inherits from ContractBase
   - Contains contract logic
   - Uses state management
   - Includes documentation

2. Contract State (ContractState.cs)
   - Defines state variables
   - Uses proper AELF types
   - Includes documentation

3. Protobuf Definitions (Protobuf/)
   - contract/ - Interface
   - message/ - Messages
   - reference/ - References

4. Contract References (ContractReferences.cs)
   - Reference declarations
   - Helper methods"""

            if not coding_patterns:
                logger.warning(f"[{request_id}] No coding patterns section found, using default")
                coding_patterns = """Common AELF patterns:
1. State Management
   - MapState for collections
   - SingletonState for values
   - State initialization
   - Access patterns

2. Access Control
   - Context.Sender checks
   - Ownership patterns
   - Authorization
   - Least privilege

3. Event Handling
   - Event definitions
   - State change events
   - Event parameters
   - Documentation

4. Input Validation
   - Parameter validation
   - State validation
   - Error messages
   - Fail-fast approach

5. Error Handling
   - Exception types
   - Error messages
   - Edge cases
   - AELF patterns"""
                
            # Create insights dictionary with extracted sections
            insights_dict = {
                "project_structure": project_structure,
                "coding_patterns": coding_patterns,
                "implementation_guidelines": implementation_guidelines
            }
            
            # Store sample insights in the dictionary
            if all_samples:
                sample_insights = "\n\n".join([
                    f"- {sample['source']} (from {sample['project']} project)" 
                    for sample in all_samples[:5]  # Limit to top 5 samples
                ])
                insights_dict["sample_references"] = f"""Referenced Samples:
{sample_insights}"""
                logger.info(f"[{request_id}] Added {len(all_samples[:5])} sample references to insights")
            
            # Update internal state with insights
            internal_state["codebase_insights"] = insights_dict
            
            logger.info(f"[{request_id}] Codebase analysis with RAG completed successfully")
            
            # Return command to move to next state
            return Command(
                goto="generate_code",
                update={
                    "generate": {
                        "_internal": internal_state
                    }
                }
            )
                
        except Exception as e:
            logger.error(f"[{request_id}] Error analyzing codebase insights: {str(e)}")
            logger.error(f"[{request_id}] Error traceback: {traceback.format_exc()}")
            raise
            
    except Exception as e:
        logger.error(f"Error in analyze_codebase: {str(e)}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        
        # Initialize internal state if it doesn't exist
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
        
        # Create error state with default insights
        error_state = state["generate"]["_internal"]
        error_msg = f"Error analyzing codebase: {str(e)}"
        
        error_state["codebase_insights"] = {
            "project_structure": """Standard AELF project structure:
1. Contract class inheriting from AElfContract
2. State class for data storage
3. Proto files for interface definition
4. Project configuration in .csproj""",
            "coding_patterns": """Common AELF patterns:
1. State management using MapState/SingletonState
2. Event emission for status changes
3. Authorization checks using Context.Sender
4. Input validation with proper error handling""",
            "implementation_guidelines": """Follow AELF best practices:
1. Use proper base classes and inheritance
2. Implement robust state management
3. Add proper access control checks
4. Include comprehensive input validation
5. Emit events for important state changes
6. Follow proper error handling patterns
7. Add XML documentation for all public members"""
        }
        
        logger.info("Using fallback insights due to error")
        
        # Return command to continue to generate even if codebase analysis fails
        return Command(
            goto="generate_code",
            update={
                "generate": {
                    "_internal": error_state
                }
            }
        )

async def generate_contract(state: AgentState) -> Command[Literal["validate"]]:
    """Generate smart contract code based on analysis and codebase insights."""
    try:
        # Initialize internal state if not present
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
            
        # Get analysis and insights from internal state
        internal_state = state["generate"]["_internal"]
        analysis = internal_state.get("analysis", "")
        insights = internal_state.get("codebase_insights", {})
        fixes = internal_state.get("fixes", "")
        validation_count = internal_state.get("validation_count", 0)
        
        if not analysis:
            analysis = "No analysis provided. Proceeding with generic AELF contract implementation."
            internal_state["analysis"] = analysis
            
        if not insights:
            insights = {
                "project_structure": "Standard AELF project structure",
                "coding_patterns": "Common AELF patterns",
                "implementation_guidelines": "Follow AELF best practices",
                "sample_references": ""
            }
            internal_state["codebase_insights"] = insights
        
        # Get model with state
        model = get_model(state)
        
        # Prepare RAG context from codebase insights
        rag_context = f"""
# AELF Project Structure
{insights.get("project_structure", "")}

# AELF Coding Patterns
{insights.get("coding_patterns", "")}

# AELF Implementation Guidelines
{insights.get("implementation_guidelines", "")}

# AELF Code Sample References
{insights.get("sample_references", "")}

# Previous Validation Issues and Fixes
{fixes}
"""
        
        # Generate code based on analysis and insights with RAG context
        messages = [
            SystemMessage(content=CODE_GENERATION_PROMPT.format(
                implementation_guidelines=insights.get("implementation_guidelines", ""),
                coding_patterns=insights.get("coding_patterns", ""),
                project_structure=insights.get("project_structure", ""),
                sample_references=insights.get("sample_references", "")
            )),
            HumanMessage(content=f"""
Analysis:
{analysis}

RAG Context:
{rag_context}

Please generate the complete smart contract implementation following AELF's project structure.
{f"This is iteration {validation_count + 1} of the code generation. Please incorporate the fixes suggested in the previous validation." if validation_count > 0 else ""}
""")
        ]
        
        try:
            # Set a longer timeout for code generation
            response = await model.ainvoke(messages, timeout=180)  # 3 minutes timeout
            content = response.content
            
            if not content:
                raise ValueError("Code generation failed - empty response")
        except TimeoutError:
            print("DEBUG - Code generation timed out, using partial response if available")
            content = getattr(response, 'content', '') or ""
            if not content:
                raise ValueError("Code generation timed out and no partial response available")
                
        # Initialize components with empty CodeFile structures
        empty_code_file = {"content": "", "file_type": "", "path": ""}
        components = {
            "contract": dict(empty_code_file),
            "state": dict(empty_code_file),
            "proto": dict(empty_code_file),
            "reference": dict(empty_code_file),
            "project": dict(empty_code_file)
        }
        
        additional_files = []  # List to store additional files
        
        # Extract contract name from file paths or content
        contract_name = None
        lines = content.split("\n")
        
        # First try to find contract name from class definition
        for line in lines:
            if "public class" in line and "Contract" in line and ":" in line:
                parts = line.split("public class")[1].strip().split(":")
                potential_name = parts[0].strip().replace("Contract", "")
                if potential_name and not any(x in potential_name.lower() for x in ["state", "reference", "test"]):
                    contract_name = potential_name
                    break
        
        # If not found, try file paths
        if not contract_name:
            for line in lines:
                if line.strip().startswith("//") and ".cs" in line and not any(x in line.lower() for x in ["state", "reference", "test"]):
                    file_path = line.replace("// ", "").strip()
                    if "/" in file_path:
                        potential_name = file_path.split("/")[-1].replace(".cs", "")
                        if potential_name and not any(x in potential_name.lower() for x in ["state", "reference", "test"]):
                            contract_name = potential_name
                            break
        
        # If still not found, use a default name
        if not contract_name:
            contract_name = "AELFContract"
            
        # Store contract name in components for consistent usage
        for component in components.values():
            component["contract_name"] = contract_name
            
        # Function to update paths and content with contract name
        def update_contract_name_references(content, path):
            """Helper function to consistently update contract name references."""
            if content:
                content = content.replace("ContractName", contract_name)
                content = content.replace("contractname", contract_name.lower())
                content = content.replace("namespace ContractName", f"namespace {contract_name}")
                
            if path:
                # Special handling for project file to ensure it's always named correctly
                if path.endswith(".csproj"):
                    path = f"src/{contract_name}.csproj"
                else:
                    path = path.replace("ContractName", contract_name)
                    path = path.replace("contractname", contract_name.lower())
                    
            return content, path

        # Initialize all file paths with correct names
        components["project"]["path"] = f"src/{contract_name}.csproj"
        components["contract"]["path"] = f"src/{contract_name}Contract.cs"
        components["state"]["path"] = f"src/{contract_name}State.cs"
        components["proto"]["path"] = f"src/Protobuf/contract/{contract_name.lower()}.proto"
        components["reference"]["path"] = "src/ContractReference.cs"

        # Parse code blocks
        current_component = None
        current_content = []
        in_code_block = False
        current_file_type = ""
        found_components = set()  # Track which components we've already found
        contract_files = []  # Store all contract files (for multiple contract files)
        
        for i, line in enumerate(content.split("\n")):
            # Handle code block markers
            if "```" in line:
                if not in_code_block:
                    # Start of code block - detect language and file path
                    current_file_type = ""
                    if "csharp" in line.lower():
                        current_file_type = "csharp"
                    elif "protobuf" in line.lower() or "proto" in line.lower():
                        current_file_type = "proto"
                    elif "xml" in line.lower():
                        current_file_type = "xml"
                    
                    # Look for file path in next line
                    if i + 1 < len(content.split("\n")):
                        next_line = content.split("\n")[i + 1].strip()
                        if next_line.startswith("//") or next_line.startswith("<!--"):
                            file_path = (
                                next_line.replace("// ", "")
                                .replace("<!-- ", "")
                                .replace(" -->", "")
                                .strip()
                            )
                            
                            # Map file path to component type
                            if "State.cs" in file_path:
                                current_component = "state"
                            elif ".csproj" in file_path:
                                current_component = "project"
                            elif file_path.endswith(".cs") and "Reference" in file_path:
                                current_component = "reference"
                            elif ".proto" in file_path:
                                current_component = "proto"
                            elif file_path.endswith(".cs"):
                                # Check if we've already found a contract component
                                if "contract" in found_components:
                                    # This is an additional contract file
                                    current_component = f"additional_contract_{len(contract_files)}"
                                    contract_files.append({
                                        "content": "",
                                        "file_type": current_file_type,
                                        "path": file_path
                                    })
                                else:
                                    current_component = "contract"
                                    found_components.add("contract")
                            
                            if current_component:
                                if current_component.startswith("additional_contract_"):
                                    # For additional contract files, store the file path directly
                                    idx = int(current_component.split("_")[-1])
                                    contract_files[idx]["path"] = file_path
                                else:
                                    components[current_component]["file_type"] = current_file_type
                else:
                    # End of code block
                    if current_component and current_content:
                        code_content = "\n".join(current_content).strip()
                        if current_component.startswith("additional_contract_"):
                            # Store content for additional contract file
                            idx = int(current_component.split("_")[-1])
                            contract_files[idx]["content"] = code_content
                        elif current_component in components:
                            # Update content with contract name
                            code_content, _ = update_contract_name_references(code_content, "")
                            components[current_component]["content"] = code_content
                    current_content = []
                    current_component = None
                in_code_block = not in_code_block
                continue
            
            # Collect content if in a code block
            if in_code_block and current_component:
                # Skip the first line if it's a comment with the file path
                if len(current_content) == 0 and (line.startswith("// ") or line.startswith("<!-- ")):
                    if ("src/" in line or line.endswith(".cs") or line.endswith(".proto") or line.endswith(".csproj")):
                        continue
                current_content.append(line)

        # Add all additional contract files to metadata
        for contract_file in contract_files:
            content, path = update_contract_name_references(contract_file["content"], contract_file["path"])
            additional_files.append({
                "content": content,
                "file_type": contract_file["file_type"],
                "path": path
            })

        # Check the proto file for AELF-specific imports and generate additional proto files
        proto_content = components["proto"].get("content", "")
        if proto_content:
            # Parse the proto file for imports
            aelf_imports = []
            import_re = r'import\s+"([^"]+)";'
            imports = re.findall(import_re, proto_content)
            
            for import_path in imports:
                # Check if this is an AELF-specific import
                if import_path.startswith("aelf/"):
                    aelf_imports.append(import_path)
            
            # Generate content for AELF-specific imports
            for aelf_import in aelf_imports:
                import_path = f"src/Protobuf/reference/{aelf_import}"
                
                # Generate content using LLM instead of hardcoded templates
                import_content = await generate_proto_file_content(model, aelf_import)
                
                # Add to additional files if we have content
                if import_content:
                    additional_files.append({
                        "content": import_content,
                        "file_type": "proto",
                        "path": import_path
                    })
            
            # Check for ACS imports
            acs_imports = []
            for import_path in imports:
                if "acs" in import_path.lower():
                    acs_imports.append(import_path)
            
            # Generate content for ACS imports
            for acs_import in acs_imports:
                import_path = f"src/Protobuf/reference/{acs_import}"
                
                # Generate content using LLM instead of hardcoded templates
                import_content = await generate_proto_file_content(model, acs_import)
                
                # Add to additional files if we have content
                if import_content:
                    additional_files.append({
                        "content": import_content,
                        "file_type": "proto",
                        "path": import_path
                    })

        # Create the output structure with metadata containing additional files
        output = {
            "contract": components["contract"],
            "state": components["state"],
            "proto": components["proto"],
            "reference": components["reference"],
            "project": components["project"],
            "metadata": additional_files,
            "analysis": analysis  # Preserve analysis in output
        }
        
        # Remove commented filenames from the beginning of the content
        for component_key in ["contract", "state", "proto", "reference", "project"]:
            component = output[component_key]
            content = component["content"]
            
            # If content starts with a commented filename, remove it
            if content:
                lines = content.split("\n")
                if lines and (
                    (lines[0].startswith("// src/") or lines[0].startswith("// Src/")) or
                    (lines[0].startswith("<!-- src/") or lines[0].startswith("<!-- Src/"))
                ):
                    component["content"] = "\n".join(lines[1:])
        
        # Remove contract_name fields from components in the output
        for component_key in ["contract", "state", "proto", "reference", "project"]:
            if "contract_name" in output[component_key]:
                del output[component_key]["contract_name"]
        
        # Update internal state with output
        internal_state["output"] = output
        
        # Return command to move to validation
        return Command(
            goto="validate",
            update={
                "generate": {
                    "_internal": internal_state
                }
            }
        )
        
    except Exception as e:
        print(f"Error in generate_contract: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        
        # Initialize internal state if it doesn't exist
        if "generate" not in state or "_internal" not in state["generate"]:
            state["generate"] = {"_internal": get_default_state()["generate"]["_internal"]}
        
        # Create error state
        error_state = state["generate"]["_internal"]
        error_msg = f"Error generating contract: {str(e)}"
        
        # Create empty code file
        empty_code_file = {"content": "", "file_type": "", "path": ""}
        
        # Update output with error
        error_state["output"] = {
            "contract": empty_code_file,
            "state": empty_code_file,
            "proto": empty_code_file,
            "reference": empty_code_file,
            "project": empty_code_file,
            "metadata": [],
            "analysis": error_msg
        }
        
        # Return command to continue to next state
        return Command(
            goto="__end__",
            update={
                "generate": {
                    "_internal": error_state
                }
            }
        )

async def validate_contract(state: AgentState) -> Dict:
    """Validate the generated contract code and provide suggestions using LLM."""
    try:
        # Initialize internal state if not present
        if "generate" not in state:
            state["generate"] = {}
        if "_internal" not in state["generate"]:
            state["generate"]["_internal"] = get_default_state()["generate"]["_internal"]
        
        internal_state = state["generate"]["_internal"]
        current_count = internal_state.get("validation_count", 0)
        
        # Get the generated code from the state
        output = internal_state.get("output", {})
        
        contract_code = output.get("contract", {}).get("content", "")
        state_code = output.get("state", {}).get("content", "")
        proto_code = output.get("proto", {}).get("content", "")
        reference_code = output.get("reference", {}).get("content", "")
        project_code = output.get("project", {}).get("content", "")
        
        # Create a combined code representation for validation
        code_to_validate = f"""Main Contract File:
```csharp
{contract_code}
```

State Class File:
```csharp
{state_code}
```

Proto File:
```protobuf
{proto_code}
```

Reference Contract File:
```csharp
{reference_code}
```

Project File:
```xml
{project_code}
```"""

        # Get model with state
        model = get_model(state)
        
        # Generate validation using the LLM
        messages = [
            SystemMessage(content=VALIDATION_PROMPT),
            HumanMessage(content=f"""
Please validate the following smart contract code generated for AELF and provide a detailed analysis with specific issues and fixes:

{code_to_validate}

Categorize your findings into:
1. Critical issues (must be fixed)
2. Improvements (recommended but not critical)
3. Best practices

For each issue found, provide specific suggestions on how to fix it. If no issues are found in a category, explicitly state "No issues found in this category."
""")
        ]
        
        try:
            # Set timeout for validation
            validation_response = await model.ainvoke(messages, timeout=120)
            validation_feedback = validation_response.content.strip()
            
            if not validation_feedback:
                raise ValueError("Validation failed - empty response")
                
            # Basic parsing to extract issues and suggestions
            validation_results = []
            suggestions = []
            
            # Simple parsing logic - extract issues and suggestions
            lines = validation_feedback.split('\n')
            for i, line in enumerate(lines):
                if "issue" in line.lower() or "error" in line.lower() or "problem" in line.lower() or "missing" in line.lower():
                    validation_results.append(line.strip())
                    # Look for suggestion in the next few lines
                    for j in range(i+1, min(i+5, len(lines))):
                        if "fix" in lines[j].lower() or "suggestion" in lines[j].lower() or "should" in lines[j].lower() or "add" in lines[j].lower() or "change" in lines[j].lower():
                            suggestions.append(lines[j].strip())
                            break
            
            # If no explicit issues found but validation contains critical keywords
            if not validation_results:
                for critical_keyword in ["error", "missing", "invalid", "incorrect", "problem", "issue"]:
                    if critical_keyword in validation_feedback.lower():
                        validation_results.append(f"Potential issue detected: review '{critical_keyword}' mentions in validation")
                        break
            
            # Create validation summary
            validation_summary = {
                "passed": len(validation_results) == 0 or "no issues found" in validation_feedback.lower(),
                "issues": validation_results[:5],  # Limit to top 5 issues
                "suggestions": suggestions[:5]     # Limit to top 5 suggestions
            }
            
            # Update internal state with validation results and full feedback
            updated_internal = {
                **internal_state,
                "validation_count": current_count + 1,
                "validation_complete": True,
                "validation_result": validation_summary,
                "validation_status": "success" if validation_summary["passed"] else "needs_improvement",
                "output": output,  # Preserve the output structure
                "fixes": validation_feedback  # Store full validation feedback for next iteration
            }
            
            # Return state in the format expected by UI
            return {
                "generate": {
                    "_internal": updated_internal
                }
            }
                
        except Exception as e:
            print(f"Error during LLM validation: {str(e)}")
            print(f"Error traceback: {traceback.format_exc()}")
            raise
            
    except Exception as e:
        print(f"Error in validate_contract: {str(e)}")
        print(f"Error traceback: {traceback.format_exc()}")
        
        # Make sure we have internal_state defined even in case of error
        if not 'internal_state' in locals():
            internal_state = state.get("generate", {}).get("_internal", {})
            if not internal_state:
                internal_state = get_default_state()["generate"]["_internal"]
        
        # Preserve any existing output
        output = internal_state.get("output", {})
        
        # Create a default validation result
        validation_summary = {
            "passed": False,
            "issues": [f"Error during validation: {str(e)}"],
            "suggestions": ["Fix the validation errors and try again"]
        }
        
        # Return state in the format expected by UI
        return {
            "generate": {
                "_internal": {
                    **internal_state,
                    "validation_count": current_count + 1 if 'current_count' in locals() else 1,
                    "validation_complete": True,
                    "validation_result": validation_summary,
                    "validation_status": "error",
                    "output": output,  # Preserve the output structure
                    "fixes": f"Error during validation: {str(e)}\nPlease review the generated code and fix any apparent issues."
                }
            }
        }

async def test_contract(state: AgentState) -> Dict:
    """
    Test the generated contract by sending it to the AELF playground API.
    Handles build testing and code fixes internally for up to 2 iterations.
    
    This function:
    1. Creates a zip file from the generated contract files
    2. Sends the zip to the AELF playground API for build testing
    3. If build fails, passes errors to LLM to generate fixes
    4. Repeats the process up to 2 times if needed
    
    Args:
        state: The current state of the agent workflow
        
    Returns:
        A dictionary containing test results and any identified issues
    """
    import os
    import zipfile
    import json
    import tempfile
    import subprocess
    import base64
    
    # Initialize internal state if not present
    if "generate" not in state:
        state["generate"] = {}
    if "_internal" not in state["generate"]:
        state["generate"]["_internal"] = {}
    
    internal_state = state["generate"]["_internal"]
    
    # Get or initialize the test cycle count
    test_cycle_count = internal_state.get("test_cycle_count", 0)
    max_cycles = 2
    
    while test_cycle_count < max_cycles:
        internal_state["test_cycle_count"] = test_cycle_count + 1
        
        # Initialize test results for this iteration
        test_results = {
            "passed": False,
            "build_output": "",
            "errors": [],
            "warnings": [],
            "dll_output": "",
            "test_cycle": test_cycle_count + 1
        }
        
        try:
            # Get the output from the state
            output = internal_state.get("output", {})
            
            # Create a temporary directory to store the files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create src directory
                src_dir = os.path.join(temp_dir, "src")
                os.makedirs(src_dir, exist_ok=True)
                
                # Extract contract, state and proto files from output
                files_to_write = []
                
                if "contract" in output and "content" in output["contract"]:
                    files_to_write.append({
                        "path": os.path.join(src_dir, os.path.basename(output["contract"].get("path", "Contract.cs"))),
                        "content": output["contract"]["content"]
                    })
                
                if "state" in output and "content" in output["state"]:
                    files_to_write.append({
                        "path": os.path.join(src_dir, os.path.basename(output["state"].get("path", "ContractState.cs"))),
                        "content": output["state"]["content"]
                    })
                
                if "proto" in output and "content" in output["proto"]:
                    # Create protobuf directory if it exists in the path
                    proto_path = output["proto"].get("path", "Protobuf/contract.proto")
                    proto_dir = os.path.dirname(proto_path)
                    if proto_dir:
                        os.makedirs(os.path.join(src_dir, proto_dir), exist_ok=True)
                    
                    files_to_write.append({
                        "path": os.path.join(src_dir, proto_path),
                        "content": output["proto"]["content"]
                    })
                
                # Add any additional files from output
                for key, value in output.items():
                    if key not in ["contract", "state", "proto"] and isinstance(value, dict) and "content" in value and "path" in value:
                        # Create directory if needed
                        file_dir = os.path.dirname(value["path"])
                        if file_dir:
                            os.makedirs(os.path.join(src_dir, file_dir), exist_ok=True)
                        
                        files_to_write.append({
                            "path": os.path.join(src_dir, value["path"]),
                            "content": value["content"]
                        })
                
                # Add metadata files (like aelf/options.proto and aelf/core.proto)
                metadata_files = output.get("metadata", [])
                for meta_file in metadata_files:
                    if isinstance(meta_file, dict) and "path" in meta_file and "content" in meta_file:
                        # Create directory if needed
                        file_dir = os.path.dirname(meta_file["path"])
                        if file_dir:
                            os.makedirs(os.path.join(src_dir, file_dir), exist_ok=True)
                        
                        files_to_write.append({
                            "path": os.path.join(src_dir, meta_file["path"]),
                            "content": meta_file["content"]
                        })
                
                # Write all files
                for file_info in files_to_write:
                    with open(file_info["path"], "w") as f:
                        f.write(file_info["content"])
                
                # Create the zip file
                zip_path = os.path.join(temp_dir, "src.zip")
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for root, _, files in os.walk(src_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                
                # Send the zip file to the AELF playground API
                curl_cmd = [
                    "curl", "--location", "https://playground.aelf.com/playground/build",
                    "--form", f'contractFiles=@"{zip_path}"'
                ]
                
                # Execute the curl command
                process = subprocess.run(curl_cmd, capture_output=True, text=True)
                
                # Process the API response
                if process.returncode == 0:
                    response_text = process.stdout
                    
                    # Check if the response indicates build success (contains base64 DLL)
                    if not response_text.strip().startswith("TV") and "error" in response_text.lower():
                        # Build failed - extract error messages
                        test_results["passed"] = False
                        test_results["build_output"] = response_text
                        
                        # Parse error messages
                        error_lines = [line for line in response_text.split('\n') if "error" in line.lower()]
                        test_results["errors"] = error_lines
                        
                        # Parse warning messages
                        warning_lines = [line for line in response_text.split('\n') if "warning" in line.lower()]
                        test_results["warnings"] = warning_lines
                        
                        # If we have errors and haven't reached max cycles, try to fix them
                        if test_cycle_count < max_cycles:
                            # Prepare prompt for generating fixes
                            error_list = "\n".join(error_lines[:10])  # Limit to first 10 errors
                            
                            # Create a map of file extensions to their descriptions
                            file_type_descriptions = {
                                ".cs": "C# source code file",
                                ".csproj": "C# project file",
                                ".proto": "Protocol Buffer definition file"
                            }
                            
                            # Collect all files content for context
                            files_context = []
                            processed_files = set()  # Track already processed files
                            
                            # First add regular files from files_to_write
                            for file_info in files_to_write:
                                file_path = os.path.basename(file_info["path"])
                                if file_path in processed_files:
                                    continue  # Skip if already processed
                                
                                processed_files.add(file_path)
                                file_ext = os.path.splitext(file_info["path"])[1]
                                file_type = file_type_descriptions.get(file_ext, "source file")
                                files_context.append(f"""
                                File: {file_path} ({file_type})
                                Content:
                                {file_info["content"]}
                                """)
                            
                            # Then add metadata files, but only if not already processed
                            metadata_files = output.get("metadata", [])
                            for meta_file in metadata_files:
                                if isinstance(meta_file, dict) and "path" in meta_file and "content" in meta_file:
                                    filename = os.path.basename(meta_file["path"])
                                    if filename in processed_files:
                                        continue  # Skip if already processed
                                    
                                    processed_files.add(filename)
                                    file_ext = os.path.splitext(meta_file["path"])[1]
                                    file_type = file_type_descriptions.get(file_ext, "source file")
                                    files_context.append(f"""
                                    File: {filename} ({file_type})
                                    Content:
                                    {meta_file["content"]}
                                    """)
                            
                            files_content = "\n---\n".join(files_context)
                            
                            # Prepare the current output structure for the LLM
                            output_description = {
                                "contract": {
                                    "path": output.get("contract", {}).get("path", ""),
                                    "file_type": output.get("contract", {}).get("file_type", "")
                                },
                                "state": {
                                    "path": output.get("state", {}).get("path", ""),
                                    "file_type": output.get("state", {}).get("file_type", "")
                                },
                                "proto": {
                                    "path": output.get("proto", {}).get("path", ""),
                                    "file_type": output.get("proto", {}).get("file_type", "")
                                },
                                "reference": {
                                    "path": output.get("reference", {}).get("path", ""),
                                    "file_type": output.get("reference", {}).get("file_type", "")
                                },
                                "project": {
                                    "path": output.get("project", {}).get("path", ""),
                                    "file_type": output.get("project", {}).get("file_type", "")
                                },
                                "metadata_paths": [meta.get("path", "") for meta in output.get("metadata", []) if isinstance(meta, dict)]
                            }
                            
                            prompt = f"""
                            You are an expert AELF smart contract developer. The contract build has failed with the following errors:
                            
                            {error_list}
                            
                            Here are all the current contract files:
                            
                            {files_content}
                            
                            Please analyze these errors and generate fixes for the code. Focus on:
                            1. Missing or incorrect imports/using statements
                            2. Class inheritance and type issues
                            3. Static vs instance member declarations
                            4. Project file configuration issues
                            5. Proto file syntax and compatibility
                            6. Any syntax or compiler errors
                            
                            The current output structure is:
                            ```json
                            {json.dumps(output_description, indent=2)}
                            ```
                            
                            Instead of describing the changes, I want you to provide the complete updated output object 
                            that incorporates all necessary fixes. Return your response in the following format:
                            
                            <UPDATED_OUTPUT>
                            {{
                              "contract": {{
                                "content": "... complete updated content ...",
                                "path": "...",
                                "file_type": "..."
                              }},
                              "state": {{
                                "content": "... complete updated content ...",
                                "path": "...",
                                "file_type": "..."
                              }},
                              "proto": {{
                                "content": "... complete updated content ...",
                                "path": "...",
                                "file_type": "..."
                              }},
                              "reference": {{
                                "content": "... complete updated content ...",
                                "path": "...",
                                "file_type": "..."
                              }},
                              "project": {{
                                "content": "... complete updated content ...",
                                "path": "...",
                                "file_type": "..."
                              }},
                              "metadata": [
                                {{
                                  "content": "... complete updated content ...",
                                  "path": "...",
                                  "file_type": "..."
                                }},
                                ...
                              ]
                            }}
                            </UPDATED_OUTPUT>
                            
                            IMPORTANT: 
                            1. Include the COMPLETE content for each file, not just the changes.
                            2. Keep the same file paths and structure, just update the content to fix the build errors.
                            3. Ensure your response is valid JSON when extracted from the <UPDATED_OUTPUT> tags.
                            4. Make only the necessary changes to fix the build errors.
                            """
                            
                            # Call the model to generate fixes
                            model = get_model(state)
                            messages = [
                                SystemMessage(content="You are an expert AELF smart contract developer."),
                                HumanMessage(content=prompt)
                            ]
                            ai_response = await model.ainvoke(messages)
                            
                            # Store the suggested fixes
                            internal_state["suggested_fixes"] = ai_response.content
                            
                            # Parse the response to extract the updated output object
                            response_text = ai_response.content
                            debug_info = []  # Store debug info about the parsing process
                            
                            # Extract the updated output object
                            updated_output = None
                            match = re.search(r'<UPDATED_OUTPUT>(.*?)</UPDATED_OUTPUT>', response_text, re.DOTALL)
                            
                            if match:
                                try:
                                    # Extract and parse the JSON
                                    updated_output_str = match.group(1).strip()
                                    
                                    # Try to parse as JSON
                                    updated_output = json.loads(updated_output_str)
                                    
                                    # Validate the structure
                                    required_keys = ["contract", "state", "proto", "reference", "project", "metadata"]
                                    missing_keys = [key for key in required_keys if key not in updated_output]
                                    
                                    if missing_keys:
                                        # Try to keep the existing keys that are missing
                                        for key in missing_keys:
                                            if key in output:
                                                updated_output[key] = output[key]
                                    
                                    # Update the output with the LLM-generated complete object
                                    output = updated_output
                                    
                                except json.JSONDecodeError as e:
                                    # Try basic validation and sanitizing
                                    try:
                                        # Replace any problematic characters and try again
                                        sanitized_str = updated_output_str.replace('\t', '    ').replace('\\n', '\\\\n')
                                        updated_output = json.loads(sanitized_str)
                                        output = updated_output
                                    except:
                                        pass
                            
                            # Store debug info in internal state for troubleshooting if needed
                            internal_state["debug_info"] = debug_info
                            
                            # Update the state with fixed files
                            internal_state["output"] = output
                            
                            # Continue to next iteration
                            test_cycle_count += 1
                            continue
                            
                    else:
                        # Build successful
                        test_results["passed"] = True
                        test_results["build_output"] = "Build succeeded"
                        test_results["dll_output"] = response_text[:100] + "..." if len(response_text) > 100 else response_text
                        break  # Exit the loop on success
                else:
                    # API call failed
                    test_results["passed"] = False
                    test_results["build_output"] = f"API call failed: {process.stderr}"
                    test_results["errors"] = [process.stderr]
                    break  # Exit the loop on API failure
            
        except Exception as e:
            print(f"Error in test_contract: {str(e)}")
            print(f"Error traceback: {traceback.format_exc()}")
            
            # Update test results with error information
            test_results["passed"] = False
            test_results["build_output"] = f"Error during testing: {str(e)}"
            test_results["errors"] = [str(e)]
            break  # Exit the loop on exception
        
        test_cycle_count += 1
    
    # Store final test results in the state
    internal_state["test_results"] = test_results
    
    # Return the final state
    return {
        "generate": {
            "_internal": {
                "output": internal_state.get("output", {}),  # Keep only the essential output
                "analysis": internal_state.get("analysis", ""),  # Keep analysis for reference
                "fixes": internal_state.get("fixes", ""),  # Keep fixes information
                "codebase_insights": internal_state.get("codebase_insights", {}),  # Keep codebase insights
                "test_results": internal_state.get("test_results", {}),  # Keep test results
                "validation_results": internal_state.get("validation_result", {})  # Keep validation results
            }
        }
    }

def validation_router(state: AgentState) -> str:
    """
    Route to the appropriate next step based on validation results.
    Allows only one validation cycle before ending.
    """
    if "generate" not in state:
        state["generate"] = {}
    if "_internal" not in state["generate"]:
        state["generate"]["_internal"] = {}
            
    internal_state = state["generate"]["_internal"]
    current_count = internal_state.get("validation_count", 0)
    
    # Ensure required fields exist
    if "output" not in internal_state:
        internal_state["output"] = {}
    if "validation_result" not in internal_state:
        internal_state["validation_result"] = {
            "passed": True,
            "issues": [],
            "suggestions": []
        }
    if "validation_status" not in internal_state:
        internal_state["validation_status"] = "success"
    if "fixes" not in internal_state:
        internal_state["fixes"] = ""
    
    # Route to test_contract after successful validation
    # Store the current validation count for tracking retries
    internal_state["validation_count"] = current_count + 1
    
    if current_count < 2:
        # If we haven't reached the second validation yet, go back to generate_code
        return "generate_code"
    else:
        # After reaching validation_count of 2, proceed to test_contract
        # regardless of validation status
        return "test_contract"

def test_router(state: AgentState) -> str:
    """
    Route to end after test_contract completes.
    The test_contract function handles all iterations internally.
    """
    return "__end__"

def create_agent() -> StateGraph:
    """Create the agent workflow with a linear flow."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_requirements)
    workflow.add_node("analyze_codebase", analyze_codebase)
    workflow.add_node("generate_code", generate_contract)
    workflow.add_node("validate", validate_contract)
    workflow.add_node("test_contract", test_contract)
    
    # Set the entry point
    workflow.set_entry_point("analyze")

    # Define the linear flow
    workflow.add_edge("analyze", "analyze_codebase")
    workflow.add_edge("analyze_codebase", "generate_code")
    workflow.add_edge("generate_code", "validate")
    workflow.add_edge("generate_code", END)  # Add direct edge to END
    
    # Add conditional edges from validate
    workflow.add_conditional_edges(
        "validate",
        validation_router,
        {
            "generate_code": "generate_code",
            "test_contract": "test_contract",
            "__end__": END
        }
    )
    
    # Add edge from test_contract to END
    workflow.add_edge("test_contract", END)
    
    return workflow.compile()

# Create the graph instance
graph = create_agent()

# Export
__all__ = ["graph", "get_default_state"] 