#!/usr/bin/env python3
"""
Teste individual para executar dentro da pasta nodes.
Execute: cd src/core/nodes && python test_individual.py
"""

import sys
import os

# Adicionar path correto
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)


def test_analysis_node():
    """Testa apenas o nó de análise."""

    print("🔍 TESTANDO NÓ DE ANÁLISE INDIVIDUAL")
    print("=" * 40)

    try:
        # Import direto
        from src.core.states.agent_state import FallbackState
        from src.core.nodes.fallback_analysis import analyze_fallback_node

        print("✅ Imports OK")

        # Teste 1
        state = FallbackState(
            user_query="Quantas colunas tem a tabela?",
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

        result = analyze_fallback_node(state)

        print(f"\n🔍 Query: '{result['user_query']}'")
        print(f"   Fallback: {result['should_use_fallback']}")
        print(f"   Intent: {result['query_intent']}")
        print(f"   Motivo: {result['fallback_reason']}")

        if result["should_use_fallback"] and result["query_intent"] == "column_count":
            print("   ✅ FUNCIONOU!")
        else:
            print("   ❌ Resultado inesperado")

    except Exception as e:
        print(f"❌ Erro: {e}")


def test_execution_node():
    """Testa nó de execução."""

    print("\n⚡ TESTANDO NÓ DE EXECUÇÃO")
    print("=" * 40)

    try:
        from src.core.states.agent_state import FallbackState
        from src.core.nodes.fallback_execution import execute_fallback_node, sql_execution_node

        # Estado simulando resultado da análise
        state = FallbackState(
            user_query="Quantos registros existem?",
            should_use_fallback=True,
            query_intent="record_count",
            fallback_reason="Padrão detectado",
            sql_query=None,
            sql_result=None,
            response="",
            success=False,
            method="",
            execution_time=None
        )

        # Executar
        result = execute_fallback_node(state)
        print(f"SQL gerado: {result['sql_query']}")

        result = sql_execution_node(result)
        print(f"Resposta: {result['response']}")
        print(f"Sucesso: {result['success']}")

        if result["success"]:
            print("✅ EXECUÇÃO OK!")
        else:
            print("❌ Execução falhou")

    except Exception as e:
        print(f"❌ Erro: {e}")


def main():
    """Teste completo individual."""

    print("🧪 TESTE INDIVIDUAL DOS NÓS")
    print("Executando de: src/core/nodes/\n")

    test_analysis_node()
    test_execution_node()

    print("\n🎯 Se tudo funcionou aqui, os nós estão corretos!")
    print("Execute o teste completo da raiz: python test_imports.py")


if __name__ == "__main__":
    main()