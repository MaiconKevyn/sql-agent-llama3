"""
Nó de execução de fallback - extrai lógica do _try_fallback_query().
Localização: src/core/nodes/fallback_execution.py (CRIAR ESTE ARQUIVO)
"""

import sys
import os

# Adicionar path para imports (temporário para testes)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ..states.agent_state import FallbackState


def execute_fallback_node(state: FallbackState) -> FallbackState:
    """
    Executa fallback baseado no intent detectado.

    EXTRAI: Parte da lógica de _try_fallback_query() do agent.py (linha 219)
    MOTIVO: Separar a DECISÃO (análise) da EXECUÇÃO (SQL).

    IMPLEMENTA APENAS: Os 4 fallbacks mais simples para começar.
    """

    if not state["should_use_fallback"]:
        # Se não deve usar fallback, não faz nada
        return state

    intent = state["query_intent"]

    # MAPEAMENTO: Intent → SQL Query
    # EXTRAÍDO do seu _try_fallback_query() mas simplificado
    fallback_queries = {
        "column_count": {
            "sql": "SELECT COUNT(*) FROM pragma_table_info('dados_sus3');",
            "method": "fallback_columns"
        },
        "record_count": {
            "sql": "SELECT COUNT(*) FROM dados_sus3;",
            "method": "fallback_records"
        },
        "death_count": {
            "sql": "SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1;",
            "method": "fallback_deaths"
        },
        "state_count": {
            "sql": "SELECT COUNT(DISTINCT UF_RESIDENCIA_PACIENTE) FROM dados_sus3;",
            "method": "fallback_states"
        },
        "city_count": {
            "sql": "SELECT COUNT(DISTINCT CIDADE_RESIDENCIA_PACIENTE) FROM dados_sus3;",
            "method": "fallback_cities"
        }
    }

    if intent in fallback_queries:
        query_info = fallback_queries[intent]
        state["sql_query"] = query_info["sql"]
        state["method"] = query_info["method"]
        state["success"] = True  # Marcar como sucesso (SQL válido gerado)

        # Preparar resposta template (será preenchida após execução)
        response_templates = {
            "column_count": "A tabela dados_sus3 tem {} colunas.",
            "record_count": "A tabela dados_sus3 tem {:,} registros.",
            "death_count": "Houve {:,} mortes registradas nos dados.",
            "state_count": "Existem {} estados diferentes nos dados.",
            "city_count": "Existem {} cidades diferentes nos dados."
        }

        # Guardar template para usar depois da execução SQL
        state["response_template"] = response_templates.get(intent, "Resultado: {}")

    else:
        # Intent não suportado ainda
        state["success"] = False
        state["response"] = f"Fallback para intent '{intent}' ainda não implementado."

    return state


def sql_execution_node(state: FallbackState) -> FallbackState:
    """
    Executa a SQL query e processa resultado.

    MOTIVO: Separar geração de SQL da execução para melhor testabilidade.
    """

    if not state.get("sql_query"):
        return state

    try:
        # SIMULAÇÃO de execução SQL para teste
        # Na implementação real, importaria DatabaseManager

        # Para teste, simular resultados baseado na query
        query = state["sql_query"]

        # Simular resultados baseado no tipo de query
        if "pragma_table_info" in query:
            simulated_result = [(18,)]  # 18 colunas
        elif "COUNT(*) FROM dados_sus3;" in query:
            simulated_result = [(58655,)]  # 58655 registros
        elif "MORTE = 1" in query:
            simulated_result = [(5420,)]  # Exemplo: 5420 mortes
        elif "DISTINCT UF_RESIDENCIA_PACIENTE" in query:
            simulated_result = [(27,)]  # 27 estados
        elif "DISTINCT CIDADE_RESIDENCIA_PACIENTE" in query:
            simulated_result = [(1234,)]  # Exemplo: 1234 cidades
        else:
            simulated_result = [(0,)]

        state["sql_result"] = simulated_result

        # Extrair valor e formatar resposta
        count = _safe_extract_count(simulated_result)
        response_template = state.get("response_template", "Resultado: {}")
        state["response"] = response_template.format(count)
        state["success"] = True

    except Exception as e:
        state["success"] = False
        state["response"] = f"Erro na execução SQL: {str(e)}"

    return state


def _safe_extract_count(result) -> int:
    """
    Extrai count de resultado SQL de forma segura.
    COPIADO do seu agent.py (linha 195) mas simplificado.
    """
    try:
        if isinstance(result, list) and len(result) > 0:
            first_row = result[0]
            if isinstance(first_row, tuple) and len(first_row) > 0:
                return int(first_row[0])
        return 0
    except:
        return 0


# FUNÇÃO DE TESTE COMPLETO
def test_fallback_execution():
    """Teste do pipeline completo: análise → execução → resultado."""

    print("🧪 TESTANDO PIPELINE COMPLETO DE FALLBACK\n")

    test_cases = [
        ("Quantas colunas tem a tabela?", "column_count", "18 colunas"),
        ("Quantos registros existem?", "record_count", "58,655 registros"),
        ("Quantas mortes houve?", "death_count", "5,420 mortes"),
        ("Quantos estados diferentes?", "state_count", "27 estados"),
    ]

    # Importar o nó de análise
    from .fallback_analysis import analyze_fallback_node

    for query, expected_intent, expected_in_response in test_cases:
        print(f"🔍 Testando: '{query}'")

        # Estado inicial
        state = FallbackState(
            user_query=query,
            should_use_fallback=False,
            query_intent="",
            fallback_reason=None,
            sql_query=None,
            sql_result=None,
            response="",
            success=False,
            method="",
            execution_time=None
        )

        # PIPELINE: Análise → Execução → SQL
        state = analyze_fallback_node(state)
        print(f"   Análise: {state['query_intent']} (fallback: {state['should_use_fallback']})")

        state = execute_fallback_node(state)
        print(f"   SQL: {state['sql_query']}")

        state = sql_execution_node(state)
        print(f"   Resposta: {state['response']}")
        print(f"   Sucesso: {state['success']}")

        # Verificar se funcionou
        assert state["query_intent"] == expected_intent
        assert state["success"] == True
        assert expected_in_response.split()[0] in state["response"]  # Verificar número

        print("   ✅ PASSOU!\n")

    print("🎉 TODOS OS TESTES DO PIPELINE PASSARAM!")


if __name__ == "__main__":
    test_fallback_execution()