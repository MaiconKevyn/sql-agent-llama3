"""
Estado mínimo para experimentar LangGraph apenas com fallbacks.
Localização: src/core/states/agent_state.py (CRIAR ESTE ARQUIVO)
"""

from typing import TypedDict, List, Optional, Dict, Any


class FallbackState(TypedDict):
    """
    Estado MÍNIMO para testar LangGraph apenas com sistema de fallback.

    Contém apenas o essencial - não todos os campos que vamos precisar depois.
    """

    # Input básico
    user_query: str

    # Análise de fallback
    should_use_fallback: bool
    query_intent: str  # "column_count", "record_count", "death_count", etc.
    fallback_reason: Optional[str]

    # Execução SQL (apenas para fallback)
    sql_query: Optional[str]  # Uma query só para começar
    sql_result: Optional[Any]

    # Output
    response: str
    success: bool
    method: str  # "fallback_columns", "fallback_records", etc.

    # Debug mínimo
    execution_time: Optional[float]