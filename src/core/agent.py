"""Implementação completa do agente SQL com todas as correções."""

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

    def _should_use_fallback(self, query: str) -> bool:
        """
        🔧 SISTEMA DE BYPASS INTELIGENTE
        Determina se deve usar fallback ao invés do agente LLM.

        Args:
            query: Pergunta do usuário

        Returns:
            True se deve usar fallback direto
        """
        query_lower = query.lower()

        # Casos onde o agente LLM frequentemente erra
        fallback_triggers = [
            # Contagem de colunas - problema identificado
            ("quantas colunas", "tem"),
            ("colunas tem", "tabela"),
            ("número de colunas", ""),
            ("numero de colunas", ""),
            ("how many columns", ""),
            ("columns does", ""),

            # Contagem de registros - às vezes confunde com colunas
            ("quantos registros", ""),
            ("quantas linhas", ""),
            ("número de registros", ""),
            ("how many records", ""),
            ("how many rows", ""),

            # Mortalidade - frequentemente usa CID_MORTE incorretamente
            ("quantas mortes", ""),
            ("quantos morreram", ""),
            ("número de mortes", ""),
            ("total de mortes", ""),
            ("how many deaths", ""),

            # Geografia simples - às vezes usa códigos IBGE incorretos
            ("quantos estados", ""),
            ("quantas cidades", ""),
            ("estados diferentes", ""),
            ("cidades diferentes", "")
        ]

        # Verificar se a query bate com algum padrão de fallback
        for trigger1, trigger2 in fallback_triggers:
            if trigger1 in query_lower and (not trigger2 or trigger2 in query_lower):
                return True

        return False

    def _validate_agent_response(self, query: str, agent_output: str, executed_queries: List[str]) -> Dict[str, Any]:
        """
        🔧 VALIDAÇÃO DE RESPOSTA DO AGENTE
        Valida se a resposta do agente faz sentido baseada na pergunta original.

        Args:
            query: Pergunta original do usuário
            agent_output: Resposta do agente
            executed_queries: Queries SQL executadas

        Returns:
            Dict com validação e correção se necessário
        """
        query_lower = query.lower()

        # VALIDAÇÃO 1: Pergunta sobre colunas mas resposta muito alta
        if any(word in query_lower for word in ["quantas colunas", "colunas tem", "número de colunas", "how many columns"]):
            # Extrair número da resposta do agente
            import re
            numbers = re.findall(r'\d+', agent_output.replace(',', '').replace('.', ''))
            if numbers:
                reported_count = int(numbers[0])
                # Se resposta é muito alta para ser número de colunas (>50), provavelmente está errado
                if reported_count > 50:
                    return {
                        "is_valid": False,
                        "issue": f"Agente reportou {reported_count} colunas, mas isso parece ser número de registros",
                        "correction_needed": "column_count",
                        "executed_queries": executed_queries
                    }

        # VALIDAÇÃO 2: Pergunta sobre registros mas resposta muito baixa
        elif any(word in query_lower for word in ["quantos registros", "quantas linhas", "how many records", "how many rows"]):
            import re
            numbers = re.findall(r'\d+', agent_output.replace(',', '').replace('.', ''))
            if numbers:
                reported_count = int(numbers[0])
                # Se resposta é muito baixa para ser número de registros (<100), pode estar errado
                if reported_count < 100:
                    return {
                        "is_valid": False,
                        "issue": f"Agente reportou {reported_count} registros, mas isso parece muito baixo",
                        "correction_needed": "record_count",
                        "executed_queries": executed_queries
                    }

        # VALIDAÇÃO 3: Verificar queries SQL executadas
        for sql_query in executed_queries:
            sql_upper = sql_query.upper()

            # Se pergunta é sobre colunas mas query conta registros
            if any(word in query_lower for word in ["quantas colunas", "colunas tem", "how many columns"]):
                if "COUNT(*) FROM dados_sus3" in sql_upper and "pragma_table_info" not in sql_upper:
                    return {
                        "is_valid": False,
                        "issue": "Query conta registros ao invés de colunas",
                        "wrong_query": sql_query,
                        "correction_needed": "column_count",
                        "executed_queries": executed_queries
                    }

            # Se pergunta é sobre registros mas query conta colunas
            elif any(word in query_lower for word in ["quantos registros", "quantas linhas", "how many records"]):
                if "pragma_table_info" in sql_upper:
                    return {
                        "is_valid": False,
                        "issue": "Query conta colunas ao invés de registros",
                        "wrong_query": sql_query,
                        "correction_needed": "record_count",
                        "executed_queries": executed_queries
                    }

        return {
            "is_valid": True,
            "executed_queries": executed_queries
        }

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
        # 🔧 CORREÇÃO PRINCIPAL: Usar fallback para perguntas problemáticas
        if self._should_use_fallback(query):
            if self.debug_mode:
                print("🔧 [DEBUG] Usando fallback direto")

            fallback_result = self._try_fallback_query(query)
            if fallback_result:
                fallback_result["agent_bypassed"] = True
                fallback_result["bypass_reason"] = "Pergunta propensa a erro do agente LLM"
                return fallback_result

        # Adicionar contexto em português com documentação do schema
        try:
            contextualized_query = self.prompt_manager.create_contextualized_query_with_schema(query)
        except AttributeError:
            # Fallback se método não existe
            contextualized_query = self.prompt_manager.create_contextualized_query(query)

        try:
            # Tentar com o agente
            result = self.agent_executor.invoke({"input": contextualized_query})

            # ✅ Inicializar variáveis ANTES dos blocos condicionais
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

                # 🔧 NOVA VALIDAÇÃO: Verificar se resposta do agente faz sentido
                response_validation = self._validate_agent_response(query, result['output'], executed_queries)

                if not response_validation['is_valid']:
                    # Resposta do agente é suspeita, usar fallback
                    if self.debug_mode:
                        print(f"🔧 [DEBUG] Resposta do agente suspeita: {response_validation['issue']}")
                        print(f"🔧 [DEBUG] Aplicando correção via fallback")

                    fallback_result = self._try_fallback_query(query)
                    if fallback_result:
                        fallback_result["agent_error_detected"] = True
                        fallback_result["agent_error"] = response_validation['issue']
                        fallback_result["wrong_agent_response"] = result['output']
                        if 'wrong_query' in response_validation:
                            fallback_result["wrong_query"] = response_validation['wrong_query']
                        return fallback_result

                response_data = {
                    "success": True,
                    "response": result['output'],
                    "method": "agent",
                    "executed_queries": executed_queries,
                    "query_count": len(executed_queries),
                    "intermediate_steps": result.get('intermediate_steps', []) if self.debug_mode else None
                }

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
        """Tenta processar consulta com fallbacks específicos e mais robustos."""
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

            # ✅ Fallback para listar cidades distintas
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

            # 🔧 FALLBACK MELHORADO: Mortalidade com múltiplas variações
            elif any(phrase in query_lower for phrase in [
                "quantas mortes", "quantos morreram", "número de mortes", "total de mortes",
                "how many deaths", "death count", "mortality count"
            ]) and not any(filter_word in query_lower for filter_word in [
                "porto alegre", "santa maria", "caxias", "pelotas", "uruguaiana",
                "masculino", "feminino", "homem", "mulher", "sexo", "idade", "estado", "cidade"
            ]):
                executed_query = "SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1;"
                result = self.db_manager.execute_query(executed_query)
                count = self._safe_extract_count(result)
                return {
                    "success": True,
                    "response": f"Houve {count:,} mortes registradas nos dados.",
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