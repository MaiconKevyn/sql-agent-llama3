"""Implementação do agente SQL principal com documentação de schema e correções."""

import re
from typing import Dict, Any, Optional, List
from langchain_ollama import OllamaLLM
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents import AgentType

from config.settings import config
from src.core.database import DatabaseManager
from src.prompts.templates import PromptManager
from src.utils.schema_documentation import schema_docs


class SQLAgent:
    """Agente SQL principal para processamento de consultas em linguagem natural."""

    def __init__(self):
        """Inicializa o agente SQL."""
        self.db_manager = DatabaseManager()
        self.prompt_manager = PromptManager()
        self.llm = self._setup_llm()
        self.agent_executor = self._create_agent()
        self.debug_mode = True  # Ativar debug durante desenvolvimento

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

    def _extract_sql_queries(self, intermediate_steps: List) -> List[str]:
        """
        Extrai queries SQL dos passos intermediários do agente.

        Args:
            intermediate_steps: Lista de passos do agente

        Returns:
            Lista de queries SQL encontradas
        """
        queries = []

        for step in intermediate_steps:
            if len(step) >= 2:
                action, observation = step[0], step[1]

                # Verificar se é uma ação de query SQL
                if hasattr(action, 'tool') and 'sql' in action.tool.lower():
                    if hasattr(action, 'tool_input'):
                        query = action.tool_input
                        if isinstance(query, str) and query.strip():
                            queries.append(query.strip())

                # Também procurar por padrões SQL no texto
                if isinstance(observation, str):
                    sql_patterns = re.findall(
                        r'(SELECT.*?(?:;|\n|$))',
                        observation,
                        re.IGNORECASE | re.DOTALL
                    )
                    queries.extend([q.strip() for q in sql_patterns if q.strip()])

        # Remover duplicatas mantendo ordem
        unique_queries = []
        for query in queries:
            if query not in unique_queries:
                unique_queries.append(query)

        return unique_queries

    def _format_query_for_display(self, query: str) -> str:
        """
        Formata query SQL para exibição legível.

        Args:
            query: Query SQL bruta

        Returns:
            Query formatada
        """
        # Remover quebras de linha extras e espaços
        clean_query = ' '.join(query.split())

        # Adicionar quebras de linha em pontos estratégicos
        formatted = clean_query
        formatted = re.sub(r'\bSELECT\b', '\nSELECT', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bFROM\b', '\nFROM', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bWHERE\b', '\nWHERE', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bGROUP BY\b', '\nGROUP BY', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bORDER BY\b', '\nORDER BY', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bLIMIT\b', '\nLIMIT', formatted, flags=re.IGNORECASE)

        return formatted.strip()

    def _safe_extract_count(self, result) -> int:
        """
        Extrai de forma segura o count de um resultado de query.
        VERSÃO ROBUSTA que funciona mesmo com string.

        Args:
            result: Resultado da query (pode ser string, lista, etc.)

        Returns:
            Número inteiro ou 0 se houver problema
        """
        try:
            # Se é None ou vazio
            if not result:
                return 0

            # Se é string (problema identificado)
            if isinstance(result, str):
                # Tentar fazer parsing da string
                import re

                # Procurar por números na string
                # Padrões como "[(2202,)]" ou "2202"
                numbers = re.findall(r'\d+', result)
                if numbers:
                    return int(numbers[0])  # Primeiro número encontrado

                # Se não encontrou números, tentar eval seguro
                try:
                    import ast
                    parsed = ast.literal_eval(result)
                    # Se conseguiu fazer parsing, processar recursivamente
                    return self._safe_extract_count(parsed)
                except:
                    pass

                return 0

            # Se é lista
            if isinstance(result, list) and len(result) > 0:
                first_row = result[0]

                # Se primeiro item é tupla
                if isinstance(first_row, tuple) and len(first_row) > 0:
                    return int(first_row[0])

                # Se primeiro item é lista
                if isinstance(first_row, list) and len(first_row) > 0:
                    return int(first_row[0])

                # Se primeiro item é número direto
                if isinstance(first_row, (int, float)):
                    return int(first_row)

                # Se primeiro item é string, processar recursivamente
                if isinstance(first_row, str):
                    return self._safe_extract_count(first_row)

            # Se é tupla
            if isinstance(result, tuple) and len(result) > 0:
                return int(result[0])

            # Se é número direto
            if isinstance(result, (int, float)):
                return int(result)

            # Última tentativa: converter direto para int
            return int(result)

        except (ValueError, TypeError, IndexError, AttributeError) as e:
            # Em caso de qualquer erro, tentar extrair números via regex
            try:
                import re
                result_str = str(result)
                numbers = re.findall(r'\d+', result_str)
                if numbers:
                    return int(numbers[0])
            except:
                pass

            # Se tudo falhou, retorna 0
            return 0

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Processa uma consulta em linguagem natural.

        Args:
            query: Pergunta em linguagem natural

        Returns:
            Dict com resultado da consulta, metadados e queries executadas
        """
        # Adicionar contexto em português com documentação do schema
        contextualized_query = self.prompt_manager.create_contextualized_query_with_schema(query)

        try:
            # Tentar com o agente
            result = self.agent_executor.invoke({"input": contextualized_query})

            # ✅ CORREÇÃO PRINCIPAL: Inicializar variáveis ANTES dos blocos condicionais
            executed_queries = []
            validation_results = []

            # Extrair queries SQL dos passos intermediários
            if 'intermediate_steps' in result:
                executed_queries = self._extract_sql_queries(result['intermediate_steps'])

                # Validar semântica das queries executadas
                for sql_query in executed_queries:
                    validation = schema_docs.validate_query_semantics(sql_query)
                    validation_results.append(validation)

            if 'output' in result and result['output'] != 'Agent stopped due to iteration limit or time limit.':
                response_data = {
                    "success": True,
                    "response": result['output'],
                    "method": "agent",
                    "executed_queries": executed_queries,
                    "query_count": len(executed_queries),
                    "intermediate_steps": result.get('intermediate_steps', []) if self.debug_mode else None
                }

                # ✅ Agora validation_results sempre existe
                # Adicionar validações se houver issues
                if validation_results and any(not v['is_valid'] for v in validation_results):
                    response_data["query_validation"] = validation_results

                return response_data

            # Fallback para consultas diretas
            fallback_result = self._try_fallback_query(query)
            if fallback_result:
                return fallback_result

            return {
                "success": False,
                "response": "Não foi possível processar a consulta.",
                "method": "failed",
                "executed_queries": executed_queries,
                "query_count": len(executed_queries)
            }

        except Exception as e:
            # Tentar fallback em caso de erro
            fallback_result = self._try_fallback_query(query)
            if fallback_result:
                return fallback_result

            return {
                "success": False,
                "response": f"Erro ao processar consulta: {str(e)}",
                "method": "error",
                "executed_queries": [],
                "query_count": 0,
                "error_details": str(e)
            }

    def _try_fallback_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Tenta processar consulta com fallbacks específicos."""
        query_lower = query.lower()
        executed_query = None

        try:
            # 🔧 FALLBACK MELHORADO: Contagem de colunas com múltiplas variações
            if any(phrase in query_lower for phrase in [
                "quantas colunas", "colunas tem", "número de colunas", "numero de colunas",
                "how many columns", "columns does", "count columns"
            ]):
                executed_query = "SELECT COUNT(*) FROM pragma_table_info('dados_sus3');"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                return {
                    "success": True,
                    "response": f"A tabela dados_sus3 tem {count} colunas.",
                    "method": "fallback_columns",
                    "executed_queries": [executed_query],
                    "query_count": 1,
                    "fallback_reason": "Correção automática: pergunta sobre colunas"
                }

            # 🔧 FALLBACK MELHORADO: Contagem de registros
            elif any(phrase in query_lower for phrase in [
                "quantos registros", "quantas linhas", "número de registros", "numero de registros",
                "how many records", "how many rows", "count records", "count rows"
            ]):
                executed_query = "SELECT COUNT(*) FROM dados_sus3;"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                return {
                    "success": True,
                    "response": f"A tabela dados_sus3 tem {count:,} registros.",
                    "method": "fallback_records",
                    "executed_queries": [executed_query],
                    "query_count": 1,
                    "fallback_reason": "Correção automática: pergunta sobre registros"
                }


            # Fallback para estados
            elif "quantos estados" in query_lower or "estados diferentes" in query_lower:
                executed_query = "SELECT COUNT(DISTINCT UF_RESIDENCIA_PACIENTE) FROM dados_sus3;"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                return {
                    "success": True,
                    "response": f"Existem {count} estados diferentes nos dados.",
                    "method": "fallback_states",
                    "executed_queries": [executed_query],
                    "query_count": 1
                }

            # Fallback para cidades
            elif "quantas cidades" in query_lower or "cidades diferentes" in query_lower:
                executed_query = "SELECT COUNT(DISTINCT CIDADE_RESIDENCIA_PACIENTE) FROM dados_sus3;"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                return {
                    "success": True,
                    "response": f"Existem {count} cidades diferentes nos dados.",
                    "method": "fallback_cities",
                    "executed_queries": [executed_query],
                    "query_count": 1
                }

            elif ("quais cidades" in query_lower or "cidades distintas" in query_lower) and "existem" in query_lower:
                executed_query = "SELECT DISTINCT CIDADE_RESIDENCIA_PACIENTE FROM dados_sus3 ORDER BY CIDADE_RESIDENCIA_PACIENTE LIMIT 20;"
                result = self.db_manager.execute_query(executed_query)

                if result:
                    # Extrair nomes das cidades do resultado
                    cities = []
                    for row in result:
                        if isinstance(row, tuple) and len(row) > 0:
                            cities.append(row[0])
                        elif isinstance(row, str):
                            cities.append(row)

                    if cities:
                        cities_list = ", ".join(cities[:15])  # Limitar a 15 cidades
                        total_count = len(result)
                        response = f"Algumas das cidades nos dados: {cities_list}"
                        if total_count > 15:
                            response += f" (e mais {total_count - 15} outras)"

                        return {
                            "success": True,
                            "response": response,
                            "method": "fallback_list_cities",
                            "executed_queries": [executed_query],
                            "query_count": 1
                        }

            elif any(city in query_lower for city in ["porto alegre", "santa maria", "caxias do sul", "pelotas", "uruguaiana"]) and any(word in query_lower for word in ["morte", "morreu", "óbito", "death", "deaths"]):
                # Detectar nome da cidade
                city_name = None
                city_mapping = {
                    "porto alegre": "Porto Alegre",
                    "santa maria": "Santa Maria",
                    "caxias do sul": "Caxias do Sul",
                    "pelotas": "Pelotas",
                    "uruguaiana": "Uruguaiana"
                }

                for key, value in city_mapping.items():
                    if key in query_lower:
                        city_name = value
                        break

                if city_name:
                    executed_query = f"SELECT COUNT(*) FROM dados_sus3 WHERE CIDADE_RESIDENCIA_PACIENTE = '{city_name}' AND MORTE = 1;"
                    result = self.db_manager.execute_query(executed_query)
                    count = self._safe_extract_count(result)
                    return {
                        "success": True,
                        "response": f"Houve {count} mortes em {city_name}.",
                        "method": "fallback_city_deaths",
                        "executed_queries": [executed_query],
                        "query_count": 1,
                        "schema_correction": f"Corrigido: usando CIDADE_RESIDENCIA_PACIENTE = '{city_name}' e MORTE = 1"
                    }

            # Fallback para mortes por sexo - NOVO
            elif any(word in query_lower for word in ["masculino", "feminino", "homem", "mulher"]) and any(word in query_lower for word in ["morte", "morreu", "óbito", "death", "deaths"]):
                if any(word in query_lower for word in ["masculino", "homem"]):
                    sexo_code = 1
                    sexo_desc = "masculino"
                else:
                    sexo_code = 3
                    sexo_desc = "feminino"

                executed_query = f"SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1 AND SEXO = {sexo_code};"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                return {
                    "success": True,
                    "response": f"Houve {count} mortes para o sexo {sexo_desc}.",
                    "method": "fallback_deaths_by_gender",
                    "executed_queries": [executed_query],
                    "query_count": 1,
                    "schema_correction": f"Corrigido: usando MORTE = 1 e SEXO = {sexo_code} ({sexo_desc})"
                }

            # Fallback para mortes gerais - APENAS PARA CASOS MUITO SIMPLES
            elif query_lower in ["how many deaths?", "how many deaths", "quantas mortes?", "quantas mortes", "total de mortes", "número de mortes"] or (any(word in query_lower for word in ["morte", "morreu", "óbito", "death", "deaths"]) and not any(city in query_lower for city in ["porto alegre", "santa maria", "caxias", "pelotas", "uruguaiana"]) and not any(filter_word in query_lower for filter_word in ["sexo", "masculino", "feminino", "homem", "mulher", "idade", "estado", "cidade", "para", "por", "em", "de", "and", "onde", "com"])):
                executed_query = "SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1;"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                return {
                    "success": True,
                    "response": f"Houve {count} mortes registradas nos dados.",
                    "method": "fallback_deaths",
                    "executed_queries": [executed_query],
                    "query_count": 1,
                    "schema_correction": "Corrigido: usando MORTE = 1 ao invés de CID_MORTE > 0"
                }

            # Fallback para idade média
            elif "idade média" in query_lower or "media idade" in query_lower:
                executed_query = "SELECT AVG(IDADE) FROM dados_sus3;"
                result = self.db_manager.execute_query(executed_query)

                # Para idade média, precisa tratar float
                try:
                    if result:
                        # Tentar extrair valor float
                        if isinstance(result, str):
                            import re
                            numbers = re.findall(r'\d+\.?\d*', result)
                            if numbers:
                                avg_age = float(numbers[0])
                            else:
                                avg_age = 0.0
                        else:
                            avg_age = result[0][0] if result else 0.0

                        return {
                            "success": True,
                            "response": f"A idade média dos pacientes é {avg_age:.1f} anos.",
                            "method": "fallback_age",
                            "executed_queries": [executed_query],
                            "query_count": 1
                        }
                except:
                    pass

            # Fallback para estrutura
            elif "estrutura" in query_lower or "schema" in query_lower:
                executed_query = "SELECT sql FROM sqlite_master WHERE type='table' AND name='dados_sus3';"
                schema = self.db_manager.get_schema_info()
                return {
                    "success": True,
                    "response": f"Estrutura da tabela dados_sus3:\n{schema}",
                    "method": "fallback_schema",
                    "executed_queries": [executed_query] if executed_query else [],
                    "query_count": 1 if executed_query else 0
                }

        except Exception as e:
            return {
                "success": False,
                "response": f"Erro no fallback: {str(e)}",
                "method": "fallback_error",
                "executed_queries": [executed_query] if executed_query else [],
                "query_count": 1 if executed_query else 0,
                "error_details": str(e)
            }

        return None

    def get_database_info(self) -> Dict[str, Any]:
        """Retorna informações do banco de dados."""
        return self.db_manager.get_database_summary()

    def set_debug_mode(self, enabled: bool) -> None:
        """
        Ativa/desativa modo debug.

        Args:
            enabled: True para ativar debug, False para desativar
        """
        self.debug_mode = enabled

    def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """
        Analisa performance de uma query específica.

        Args:
            query: Query SQL para análise

        Returns:
            Dict com informações de performance
        """
        import time

        try:
            start_time = time.time()
            result = self.db_manager.execute_query(f"EXPLAIN QUERY PLAN {query}")
            execution_time = time.time() - start_time

            return {
                "query": query,
                "execution_plan": result,
                "analysis_time_ms": execution_time * 1000,
                "estimated_complexity": self._estimate_query_complexity(query)
            }
        except Exception as e:
            return {
                "query": query,
                "error": str(e),
                "analysis_time_ms": 0,
                "estimated_complexity": "unknown"
            }

    def _estimate_query_complexity(self, query: str) -> str:
        """Estima complexidade de uma query."""
        query_upper = query.upper()

        complexity_indicators = [
            'JOIN', 'SUBQUERY', 'UNION', 'GROUP BY',
            'ORDER BY', 'HAVING', 'CASE WHEN', 'WITH'
        ]

        complexity_score = sum(
            1 for indicator in complexity_indicators
            if indicator in query_upper
        )

        if complexity_score == 0:
            return 'simples'
        elif complexity_score <= 2:
            return 'média'
        else:
            return 'complexa'

    def get_schema_suggestions(self, query: str) -> List[str]:
        """
        Retorna sugestões baseadas na documentação do schema.

        Args:
            query: Pergunta do usuário

        Returns:
            Lista de sugestões
        """
        return schema_docs.get_column_suggestions(query)

    def validate_query_against_schema(self, sql_query: str) -> Dict[str, Any]:
        """
        Valida uma query SQL contra a documentação do schema.

        Args:
            sql_query: Query SQL para validar

        Returns:
            Resultado da validação
        """
        return schema_docs.validate_query_semantics(sql_query)