"""
Nó de análise de fallback - extrai lógica do agent.py.
Localização: src/core/nodes/fallback_analysis.py (CRIAR ESTE ARQUIVO)
"""

from .agent_state import FallbackState


def analyze_fallback_node(state: FallbackState) -> FallbackState:
    """
    Analisa se a query deve usar fallback.

    EXTRAI: Lógica de _should_use_fallback() do agent.py (linha 78-114)
    MOTIVO: Isolar esta decisão em um nó testável e observável.
    """

    query_lower = state["user_query"].lower()

    # COPIADO EXATAMENTE do seu agent.py - _should_use_fallback()
    fallback_triggers = [
        # Contagem de colunas - problema identificado
        ("quantas colunas", "tem", "column_count"),
        ("colunas tem", "tabela", "column_count"),
        ("número de colunas", "", "column_count"),
        ("numero de colunas", "", "column_count"),
        ("how many columns", "", "column_count"),
        ("columns does", "", "column_count"),

        # Contagem de registros - às vezes confunde com colunas
        ("quantos registros", "", "record_count"),
        ("quantas linhas", "", "record_count"),
        ("número de registros", "", "record_count"),
        ("how many records", "", "record_count"),
        ("how many rows", "", "record_count"),

        # Mortalidade - frequentemente usa CID_MORTE incorretamente
        ("quantas mortes", "", "death_count"),
        ("quantos morreram", "", "death_count"),
        ("número de mortes", "", "death_count"),
        ("total de mortes", "", "death_count"),
        ("how many deaths", "", "death_count"),

        # Geografia simples - às vezes usa códigos IBGE incorretos
        ("quantos estados", "", "state_count"),
        ("quantas cidades", "", "city_count"),
        ("estados diferentes", "", "state_count"),
        ("cidades diferentes", "", "city_count")
    ]

    # Verificar se a query bate com algum padrão de fallback
    for trigger1, trigger2, intent in fallback_triggers:
        if trigger1 in query_lower and (not trigger2 or trigger2 in query_lower):
            state["should_use_fallback"] = True
            state["query_intent"] = intent
            state["fallback_reason"] = f"Padrão detectado: {trigger1}"
            return state

    # Se não bateu com nenhum padrão, não usar fallback
    state["should_use_fallback"] = False
    state["query_intent"] = "general"
    state["fallback_reason"] = None

    return state


# FUNÇÃO DE TESTE - para verificar se funciona isoladamente
def test_analyze_fallback_node():
    """Teste simples para verificar se o nó funciona."""

    # Teste 1: Deve detectar fallback para colunas
    test_state = FallbackState(
        user_query="Quantas colunas tem a tabela?",
        should_use_fallback=False,  # Valores iniciais
        query_intent="",
        fallback_reason=None,
        sql_query=None,
        sql_result=None,
        response="",
        success=False,
        method="",
        execution_time=None
    )

    result = analyze_fallback_node(test_state)

    print("🧪 TESTE 1 - Colunas:")
    print(f"   Query: '{result['user_query']}'")
    print(f"   Usar fallback: {result['should_use_fallback']}")
    print(f"   Intent: {result['query_intent']}")
    print(f"   Motivo: {result['fallback_reason']}")

    assert result["should_use_fallback"] == True
    assert result["query_intent"] == "column_count"
    print("   ✅ PASSOU!")

    # Teste 2: NÃO deve detectar fallback para query geral
    test_state2 = FallbackState(
        user_query="Qual a média de idade dos pacientes?",
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

    result2 = analyze_fallback_node(test_state2)

    print("\n🧪 TESTE 2 - Query Geral:")
    print(f"   Query: '{result2['user_query']}'")
    print(f"   Usar fallback: {result2['should_use_fallback']}")
    print(f"   Intent: {result2['query_intent']}")

    assert result2["should_use_fallback"] == False
    assert result2["query_intent"] == "general"
    print("   ✅ PASSOU!")

    print("\n🎉 TODOS OS TESTES PASSARAM!")


if __name__ == "__main__":
    # Executar testes se rodar este arquivo diretamente
    test_analyze_fallback_node()