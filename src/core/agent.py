"""Implementação completa do agente SQL usando LangGraph."""

import re
from typing import Dict, Any, Optional, List
from langchain_ollama import OllamaLLM
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents import AgentType

from config.settings import config
from src.core.database import DatabaseManager
from src.prompts.templates import PromptManager
from src.utils.schema_documentation import schema_docs
from src.core.graph import GraphBuilder, AgentState


class SQLAgent:
    """
    Main SQL Agent that orchestrates natural language to SQL conversion using LangGraph.
    
    This agent processes user queries through a graph-based execution flow that includes:
    - Primary SQL generation using LangChain SQL agents
    - Fallback mechanisms for complex queries
    - Error handling and recovery
    - Query validation and execution tracking
    
    Attributes:
        db_manager (DatabaseManager): Handles database connections and operations
        prompt_manager (PromptManager): Manages prompt templates and formatting
        llm (OllamaLLM): Language model for SQL generation
        agent_executor: LangChain SQL agent for query processing
        graph: LangGraph execution graph for orchestrating the workflow
        debug_mode (bool): Flag to enable detailed debugging output
    """

    def __init__(self):
        """
        Initialize the SQL agent with all required components.
        
        Sets up the database manager, prompt manager, language model, and builds
        the LangGraph execution graph for processing queries.
        """
        self.db_manager = DatabaseManager()
        self.prompt_manager = PromptManager()
        self.llm = self._setup_llm()
        self.agent_executor = self._create_agent()
        self.debug_mode = True

        # Build the LangGraph execution graph with all dependencies
        graph_builder = GraphBuilder(
            agent_executor=self.agent_executor,
            prompt_manager=self.prompt_manager,
            db_manager=self.db_manager
        )
        self.graph = graph_builder.build_graph()

    def _setup_llm(self) -> OllamaLLM:
        """
        Configure and initialize the language model for SQL generation.
        
        Returns:
            OllamaLLM: Configured language model instance with settings from config
        """
        return OllamaLLM(
            model=config.model.name, 
            temperature=config.model.temperature
        )

    def _create_agent(self):
        """
        Create and configure the LangChain SQL agent.
        
        Sets up a zero-shot ReAct agent with SQL toolkit capabilities,
        including error handling and intermediate step tracking.
        
        Returns:
            Agent executor configured for SQL operations
        """
        return create_sql_agent(
            self.llm,
            db=self.db_manager.get_database(),
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=config.agent.verbose,
            return_intermediate_steps=True,
            agent_executor_kwargs={
                "handle_parsing_errors": config.agent.handle_parsing_errors
            }
        )

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query using the LangGraph execution flow.
        
        This method orchestrates the complete query processing pipeline:
        1. Initialize the agent state with the user query
        2. Execute the LangGraph workflow
        3. Handle success/error responses
        4. Return structured results with execution metadata
        
        Args:
            query (str): Natural language query from the user
            
        Returns:
            Dict[str, Any]: Processing results containing:
                - success (bool): Whether processing succeeded
                - response (str): Generated SQL result or error message
                - method (str): Processing method used (agent/fallback/error)
                - executed_queries (List[str]): SQL queries that were executed
                - query_count (int): Number of queries executed
                - error_details (str, optional): Detailed error information
        """
        # Initialize agent state with all required fields
        initial_state: AgentState = {
            "query": query,
            "enriched_query": "",
            "response": None,
            "executed_queries": [],
            "intermediate_steps": [],
            "method": None,
            "error": None,
            "is_fallback": False,
            "is_valid": True,
        }
        
        try:
            # Execute the LangGraph workflow
            final_state = self.graph.invoke(initial_state)

            # Handle error cases
            if final_state.get("error"):
                return {
                    "success": False,
                    "response": final_state["error"],
                    "method": final_state.get("method", "error"),
                    "executed_queries": final_state.get("executed_queries", [])
                }

            # Return successful processing results
            return {
                "success": True,
                "response": final_state.get("response", "No response generated."),
                "method": final_state.get("method", "unknown"),
                "executed_queries": final_state.get("executed_queries", []),
                "query_count": len(final_state.get("executed_queries", [])),
            }
            
        except Exception as e:
            # Handle critical graph execution errors
            return {
                "success": False,
                "response": f"Critical error executing graph: {str(e)}",
                "method": "graph_error",
                "executed_queries": [],
                "query_count": 0,
                "error_details": str(e)
            }

    def get_database_info(self) -> Dict[str, Any]:
        """
        Retrieve comprehensive database information and schema summary.
        
        Returns:
            Dict[str, Any]: Database metadata including tables, columns, and relationships
        """
        return self.db_manager.get_database_summary()

    def set_debug_mode(self, enabled: bool) -> None:
        """
        Enable or disable debug mode for detailed execution logging.
        
        Args:
            enabled (bool): True to enable debug mode, False to disable
        """
        self.debug_mode = enabled
