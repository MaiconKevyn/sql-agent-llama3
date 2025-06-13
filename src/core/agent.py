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
    Agente SQL principal que agora usa LangGraph para orquestrar o fluxo de processamento.
    """

    def __init__(self):
        """Inicializa o agente SQL e constrói o grafo de execução."""
        self.db_manager = DatabaseManager()
        self.prompt_manager = PromptManager()
        self.llm = self._setup_llm()
        self.agent_executor = self._create_agent()
        self.debug_mode = True

        # ATUALIZADO: Passa as dependências necessárias para o GraphBuilder
        graph_builder = GraphBuilder(
            agent_executor=self.agent_executor,
            prompt_manager=self.prompt_manager,
            db_manager=self.db_manager
        )
        self.graph = graph_builder.build_graph()

    def _setup_llm(self) -> OllamaLLM:
        # (código omitido para brevidade, permanece o mesmo)
        return OllamaLLM(model=config.model.name, temperature=config.model.temperature)

    def _create_agent(self):
        # (código omitido para brevidade, permanece o mesmo)
        return create_sql_agent(
            self.llm,
            db=self.db_manager.get_database(),
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=config.agent.verbose,
            return_intermediate_steps=True,
            agent_executor_kwargs={"handle_parsing_errors": config.agent.handle_parsing_errors}
        )

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Processa uma consulta em linguagem natural usando o grafo LangGraph.
        """
        initial_state: AgentState = {
            "query": query, "response": None, "executed_queries": [],
            "intermediate_steps": [], "method": None, "error": None, "is_fallback": False,
        }
        try:
            final_state = self.graph.invoke(initial_state)

            if final_state.get("error"):
                return {"success": False, "response": final_state["error"], "method": final_state.get("method", "error"),"executed_queries": final_state.get("executed_queries", [])}

            return {
                "success": True, "response": final_state.get("response", "Nenhuma resposta gerada."),
                "method": final_state.get("method", "unknown"), "executed_queries": final_state.get("executed_queries", []),
                "query_count": len(final_state.get("executed_queries", [])),
            }
        except Exception as e:
            return {"success": False, "response": f"Erro crítico ao executar o grafo: {str(e)}", "method": "graph_error","executed_queries": [], "query_count": 0, "error_details": str(e)}

    def get_database_info(self) -> Dict[str, Any]:
        return self.db_manager.get_database_summary()

    def set_debug_mode(self, enabled: bool) -> None:
        self.debug_mode = enabled
