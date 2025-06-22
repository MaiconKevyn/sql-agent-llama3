"""
Implementação do fluxo do agente usando LangGraph.
Este módulo define o estado, os nós e as arestas do grafo que orquestra a lógica de consulta.
"""

from typing import List, TypedDict, Optional, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.pregel import Pregel

# Importações necessárias para a lógica dos nós
from src.core.database import DatabaseManager
from src.prompts.templates import PromptManager
from src.utils.cid_lookup import CIDLookup # Importa a nova ferramenta de busca
import re

class AgentState(TypedDict):
    """
    Representa o estado do agente durante o processamento de uma consulta.
    """
    query: str
    enriched_query: str
    response: Optional[str]
    executed_queries: List[str]
    intermediate_steps: List[Any]
    method: Optional[str]
    error: Optional[str]
    is_fallback: bool
    is_valid: Optional[bool]


class GraphBuilder:
    """
    Constrói e contém os nós e as lógicas de aresta para o grafo do LangGraph.
    """
    def __init__(self, agent_executor: Any, prompt_manager: PromptManager, db_manager: DatabaseManager):
        self.agent_executor = agent_executor
        self.prompt_manager = prompt_manager
        self.db_manager = db_manager
        # Inicializa a ferramenta de busca CID
        self.cid_lookup = CIDLookup()

    # ATUALIZADO: Lógica de tradução mais robusta
    def semantic_translation_node(self, state: AgentState) -> dict:
        """
        Nó que enriquece a consulta do usuário usando a ferramenta CIDLookup
        para traduzir termos de doenças em condições SQL explícitas.
        """
        print("--- Verificando necessidade de tradução semântica ---")
        query = state['query']
        # CORREÇÃO 1: Limpa a query de pontuação final para uma regex mais confiável
        clean_query = re.sub(r'[.?]$', '', query.lower()).strip()
        enriched_query = query

        # CORREÇÃO 2: Regex aprimorado para capturar frases com 'com', 'de', 'por', etc.
        match = re.search(r'(casos|internações|mortes|doenças?) (?:com |de |do |da |pelo |pela |por )([\w\s]+)', clean_query)

        if match:
            # O termo da doença é o segundo grupo capturado pela regex
            term = match.group(2).strip()
            print(f"--- Termo encontrado para tradução: '{term}' ---")
            cid_range = self.cid_lookup.find_cid_range(term)

            # CORREÇÃO 3: Lógica de fallback para a busca do termo
            if not cid_range and ' ' in term:
                simpler_term = term.split()[-1]
                print(f"--- Termo não encontrado. Tentando termo mais simples: '{simpler_term}' ---")
                cid_range = self.cid_lookup.find_cid_range(simpler_term)

            if cid_range:
                start_cat, end_cat = cid_range
                print(f"--- Categorias CID encontradas: {start_cat}-{end_cat} ---")

                sql_condition = f"(DIAG_PRINC >= '{start_cat}' AND DIAG_PRINC <= '{end_cat}')"

                # CORREÇÃO 4: Constrói uma nova query do zero para ser clara e inequívoca
                base_intent = match.group(1)
                if base_intent.startswith("doença"):
                    base_intent = "casos" # Trata "doenças de X" como "casos de X"

                question = f"Qual o número total de {base_intent}"
                enriched_query = f"{question} que satisfazem a seguinte condição SQL: {sql_condition}"
                print(f"--- Query reescrita e enriquecida: {enriched_query} ---")

        return {"enriched_query": enriched_query}


    def route_query(self, state: AgentState) -> dict:
        """
        Este é um nó que simplesmente passa o estado adiante.
        """
        print("--- Decidindo rota para a consulta ---")
        return {}

    def should_use_fallback(self, state: AgentState) -> Literal["fallback", "agent"]:
        """
        Determina se a consulta do usuário deve ser tratada por uma lógica de fallback.
        """
        query = state['enriched_query']
        query_lower = query.lower()

        # Se a query foi enriquecida com uma condição SQL, ela deve ir para o agente.
        if "condição sql" in query_lower:
            return "agent"

        fallback_triggers = [
            ("quantas colunas", "tem"), ("colunas tem", "tabela"),
            ("número de colunas", ""), ("numero de colunas", ""),
            ("quantos registros", ""), ("quantas linhas", ""),
            ("quantas mortes", ""), ("quantos morreram", ""),
            ("quantos estados", ""), ("quantas cidades", "")
        ]

        for trigger1, trigger2 in fallback_triggers:
            if trigger1 in query_lower and (not trigger2 or trigger2 in query_lower):
                if "para" in query_lower or "em" in query_lower or "com" in query_lower or "de" in query_lower:
                    if trigger1 not in ["quantas colunas", "quantos registros"]:
                         return "agent"
                return "fallback"

        return "agent"

    def run_fallback(self, state: AgentState) -> dict:
        """
        Executa uma consulta usando a lógica de fallback codificada.
        """
        query = state['enriched_query']
        query_lower = query.lower()
        executed_query = None
        response_data = {}

        try:
            if any(phrase in query_lower for phrase in ["quantas colunas", "colunas tem"]):
                executed_query = "SELECT COUNT(*) FROM pragma_table_info('dados_sus3');"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                response_data = {"response": f"A tabela dados_sus3 tem {count} colunas.","method": "fallback_columns"}
            elif any(phrase in query_lower for phrase in ["quantos registros", "quantas linhas"]):
                executed_query = "SELECT COUNT(*) FROM dados_sus3;"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                response_data = {"response": f"A tabela dados_sus3 tem {count:,} registros.","method": "fallback_records"}
            elif any(phrase in query_lower for phrase in ["quantas mortes", "quantos morreram"]):
                executed_query = "SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1;"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                response_data = {"response": f"Houve {count:,} mortes registradas nos dados.", "method": "fallback_deaths"}
            elif "quantos estados" in query_lower or "estados diferentes" in query_lower:
                executed_query = "SELECT COUNT(DISTINCT UF_RESIDENCIA_PACIENTE) FROM dados_sus3;"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                response_data = {"response": f"Existem {count} estados diferentes nos dados.", "method": "fallback_states"}
            elif "quantas cidades" in query_lower or "cidades diferentes" in query_lower:
                executed_query = "SELECT COUNT(DISTINCT CIDADE_RESIDENCIA_PACIENTE) FROM dados_sus3;"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                response_data = {"response": f"Existem {count} cidades diferentes nos dados.", "method": "fallback_cities"}

            if executed_query:
                response_data['executed_queries'] = [executed_query]
                response_data['is_fallback'] = True
                return response_data
        except Exception as e:
            return {"error": f"Erro no fallback: {str(e)}", "is_fallback": True}
        return {"error": "Nenhum gatilho de fallback encontrado para esta consulta.", "is_fallback": True}


    def run_agent(self, state: AgentState) -> dict:
        """
        Executa o agente SQL principal com a consulta do usuário.
        """
        query = state['enriched_query']
        contextualized_query = self.prompt_manager.create_contextualized_query_with_schema(query)

        try:
            result = self.agent_executor.invoke({"input": contextualized_query})
            executed_queries = self._extract_sql_queries(result.get('intermediate_steps', []))
            return {
                "response": result.get('output'),
                "intermediate_steps": result.get('intermediate_steps', []),
                "executed_queries": executed_queries,
                "method": "agent",
                "is_fallback": False
            }
        except Exception as e:
            return {"error": f"Erro ao executar o agente LLM: {str(e)}", "is_fallback": False}

    def validation_node(self, state: AgentState) -> dict:
        """
        Valida a resposta do agente LLM para detectar erros comuns.
        """
        print("--- Validando resposta do agente ---")
        query = state['enriched_query']
        agent_output = state.get('response', '')
        query_lower = query.lower()

        if any(word in query_lower for word in ["quantas colunas", "colunas tem"]):
            numbers = re.findall(r'\d+', agent_output.replace(',', '').replace('.', ''))
            if numbers and int(numbers[0]) > 100:
                print("--- Validação Falhou: Agente provavelmente confundiu colunas com registros. ---")
                return {"is_valid": False}

        elif any(word in query_lower for word in ["quantos registros", "quantas linhas"]):
            numbers = re.findall(r'\d+', agent_output.replace(',', '').replace('.', ''))
            if numbers and int(numbers[0]) < 100:
                print("--- Validação Falhou: Agente provavelmente confundiu registros com colunas. ---")
                return {"is_valid": False}

        print("--- Validação OK ---")
        return {"is_valid": True}

    def decide_after_validation(self, state: AgentState) -> Literal["fallback", "end"]:
        """
        Decide o que fazer após a validação da resposta do agente.
        """
        if state.get("is_valid") is False:
            print("--- Roteando para fallback após validação falhar. ---")
            return "fallback"
        else:
            print("--- Finalizando o fluxo. ---")
            return "end"

    @staticmethod
    def _extract_sql_queries(intermediate_steps: List) -> List[str]:
        queries = []
        for step in intermediate_steps:
            if len(step) >= 2:
                action, _ = step
                if hasattr(action, 'tool') and 'sql' in action.tool.lower():
                    if hasattr(action, 'tool_input'):
                        query = action.tool_input
                        if isinstance(query, str) and query.strip() and query not in queries:
                            queries.append(query)
        return queries

    @staticmethod
    def _safe_extract_count(result) -> int:
        try:
            if not result: return 0
            if isinstance(result, str):
                numbers = re.findall(r'\d+', result)
                return int(numbers[0]) if numbers else 0
            if isinstance(result, list) and len(result) > 0:
                first_row = result[0]
                if isinstance(first_row, tuple) and len(first_row) > 0:
                    return int(first_row[0])
            return int(result)
        except (ValueError, TypeError, IndexError):
            return 0

    def build_graph(self) -> Pregel:
        """
        Constrói e compila o grafo do LangGraph com o ciclo de validação.
        """
        graph = StateGraph(AgentState)

        # Adicionar todos os nós
        graph.add_node("translator", self.semantic_translation_node)
        graph.add_node("router", self.route_query)
        graph.add_node("agent", self.run_agent)
        graph.add_node("fallback", self.run_fallback)
        graph.add_node("validator", self.validation_node)

        # Definir o ponto de entrada
        graph.set_entry_point("translator")

        # Definir o fluxo
        graph.add_edge("translator", "router")
        graph.add_conditional_edges(
            "router",
            self.should_use_fallback,
            {"agent": "agent", "fallback": "fallback"}
        )
        graph.add_edge("agent", "validator")
        graph.add_conditional_edges(
            "validator",
            self.decide_after_validation,
            {"fallback": "fallback", "end": END}
        )
        graph.add_edge("fallback", END)

        return graph.compile()
