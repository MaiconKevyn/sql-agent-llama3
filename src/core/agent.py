"""Implementação do agente SQL principal."""

from typing import Dict, Any, Optional
from langchain_ollama import OllamaLLM
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents import AgentType

from config.settings import config
from src.core.database import DatabaseManager
from src.prompts.templates import PromptManager


class SQLAgent:
    """Agente SQL principal para processamento de consultas em linguagem natural."""

    def __init__(self):
        """Inicializa o agente SQL."""
        self.db_manager = DatabaseManager()
        self.prompt_manager = PromptManager()
        self.llm = self._setup_llm()
        self.agent_executor = self._create_agent()

    def _setup_llm(self) -> OllamaLLM:
        """Configura o modelo de linguagem."""
        return OllamaLLM(
            model=config.model.name,
            temperature=config.model.temperature,
            top_p=config.model.top_p,
            num_predict=config.model.num_predict
        )

    def _create_agent(self):
        """Cria o agente SQL com configurações personalizadas."""
        return create_sql_agent(
            self.llm,
            db=self.db_manager.get_database(),
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=config.agent.verbose,
            handle_parsing_errors=config.agent.handle_parsing_errors,
            max_iterations=config.agent.max_iterations,
            return_intermediate_steps=True,
            agent_executor_kwargs={
                "handle_parsing_errors": config.agent.handle_parsing_errors,
            }
        )

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Processa uma consulta em linguagem natural.

        Args:
            query: Pergunta em linguagem natural

        Returns:
            Dict com resultado da consulta e metadados
        """
        # Adicionar contexto em português
        contextualized_query = self.prompt_manager.create_contextualized_query(query)

        try:
            # Tentar com o agente
            result = self.agent_executor.invoke({"input": contextualized_query})

            if 'output' in result and result['output'] != 'Agent stopped due to iteration limit or time limit.':
                return {
                    "success": True,
                    "response": result['output'],
                    "method": "agent"
                }

            # Fallback para consultas diretas
            fallback_result = self._try_fallback_query(query)
            if fallback_result:
                return fallback_result

            return {
                "success": False,
                "response": "Não foi possível processar a consulta.",
                "method": "failed"
            }

        except Exception as e:
            # Tentar fallback em caso de erro
            fallback_result = self._try_fallback_query(query)
            if fallback_result:
                return fallback_result

            return {
                "success": False,
                "response": f"Erro ao processar consulta: {str(e)}",
                "method": "error"
            }

    def _try_fallback_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Tenta processar consulta com fallbacks específicos."""
        query_lower = query.lower()

        try:
            # Fallback para contagem de colunas
            if "quantas colunas" in query_lower or "colunas tem" in query_lower:
                result = self.db_manager.execute_query(
                    "SELECT COUNT(*) FROM pragma_table_info('dados_sus3');"
                )
                count = result[0][0] if result else "N/A"
                return {
                    "success": True,
                    "response": f"A tabela dados_sus3 tem {count} colunas.",
                    "method": "fallback_columns"
                }

            # Fallback para contagem de registros
            elif "quantos registros" in query_lower or "quantas linhas" in query_lower:
                result = self.db_manager.execute_query("SELECT COUNT(*) FROM dados_sus3;")
                count = result[0][0] if result else "N/A"
                return {
                    "success": True,
                    "response": f"A tabela dados_sus3 tem {count:,} registros.",
                    "method": "fallback_records"
                }

            # Fallback para estados
            elif "quantos estados" in query_lower or "estados diferentes" in query_lower:
                result = self.db_manager.execute_query(
                    "SELECT COUNT(DISTINCT UF_RESIDENCIA_PACIENTE) FROM dados_sus3;"
                )
                count = result[0][0] if result else "N/A"
                return {
                    "success": True,
                    "response": f"Existem {count} estados diferentes nos dados.",
                    "method": "fallback_states"
                }

            # Fallback para cidades
            elif "quantas cidades" in query_lower or "cidades diferentes" in query_lower:
                result = self.db_manager.execute_query(
                    "SELECT COUNT(DISTINCT CIDADE_RESIDENCIA_PACIENTE) FROM dados_sus3;"
                )
                count = result[0][0] if result else "N/A"
                return {
                    "success": True,
                    "response": f"Existem {count} cidades diferentes nos dados.",
                    "method": "fallback_cities"
                }

            # Fallback para idade média
            elif "idade média" in query_lower or "media idade" in query_lower:
                result = self.db_manager.execute_query("SELECT AVG(IDADE) FROM dados_sus3;")
                avg_age = result[0][0] if result else None
                if avg_age:
                    self.age_ = {
                        "success": True,
                        "response": f"A idade média dos pacientes é {avg_age:.1f} anos.",
                        "method": "fallback_age"
                    }
                    return self.age_

            # Fallback para estrutura
            elif "estrutura" in query_lower or "schema" in query_lower:
                schema = self.db_manager.get_schema_info()
                return {
                    "success": True,
                    "response": f"Estrutura da tabela dados_sus3:\n{schema}",
                    "method": "fallback_schema"
                }

        except Exception as e:
            return {
                "success": False,
                "response": f"Erro no fallback: {str(e)}",
                "method": "fallback_error"
            }

        return None

    def get_database_info(self) -> Dict[str, Any]:
        """Retorna informações do banco de dados."""
        return self.db_manager.get_database_summary()