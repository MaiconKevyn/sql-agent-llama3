#!/usr/bin/env python3
"""
Script para debugar problema no fallback com correção.
"""

import sys
import os

# Adicionar ao path
sys.path.insert(0, '.')


def test_database_query():
    """Testa o retorno das queries do database manager."""

    print("🔍 DEBUGGING FALLBACK QUERIES - VERSÃO CORRIGIDA")
    print("=" * 60)

    try:
        from src.core.database import DatabaseManager

        db_manager = DatabaseManager()

        # Testar query simples primeiro
        test_query = "SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1;"

        print(f"🧪 Testando query: {test_query}")

        # Testar método direto (sem processamento)
        try:
            raw_result = db_manager.execute_query_direct(test_query)
            print(f"   📊 Resultado RAW: {raw_result}")
            print(f"   📊 Tipo RAW: {type(raw_result)}")
        except Exception as e:
            print(f"   ❌ Erro RAW: {e}")

        # Testar método corrigido
        try:
            processed_result = db_manager.execute_query(test_query)
            print(f"   📊 Resultado PROCESSADO: {processed_result}")
            print(f"   📊 Tipo PROCESSADO: {type(processed_result)}")

            if processed_result:
                count = processed_result[0][0]
                print(f"   📊 Count extraído: {count}")
                print(f"   📊 Tipo count: {type(count)}")

                # Testar formatação
                response = f"Houve {count} mortes registradas nos dados."
                print(f"   ✅ Resposta: {response}")

        except Exception as e:
            print(f"   ❌ Erro PROCESSADO: {e}")

        # Testar outras queries
        other_queries = [
            "SELECT COUNT(DISTINCT CIDADE_RESIDENCIA_PACIENTE) FROM dados_sus3;",
            "SELECT COUNT(*) FROM dados_sus3;"
        ]

        for query in other_queries:
            print(f"\n🧪 Testando: {query}")
            try:
                result = db_manager.execute_query(query)
                count = result[0][0]
                print(f"   ✅ Resultado: {count} (tipo: {type(count)})")
            except Exception as e:
                print(f"   ❌ Erro: {e}")

    except Exception as e:
        print(f"❌ Erro geral: {e}")


if __name__ == "__main__":
    test_database_query()