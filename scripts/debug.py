#!/usr/bin/env python3
"""
Exemplo de uso do Agente SQL com funcionalidades de debug.

Este script demonstra como usar o agente SQL em modo de desenvolvimento
para visualizar e analisar as queries SQL geradas.
"""

import sys
import os
from typing import List, Dict, Any

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.agent import SQLAgent
from src.interface.display import DisplayManager


def demonstrate_debug_features():
    """Demonstra as funcionalidades de debug do agente SQL."""

    print("🚀 Demonstração das Funcionalidades de Debug")
    print("=" * 60)

    # Inicializar componentes
    try:
        agent = SQLAgent()
        display = DisplayManager()

        # Ativar modo debug
        agent.set_debug_mode(True)
        print("✅ Agente inicializado com sucesso!\n")

    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
        return

    # Lista de perguntas de exemplo para demonstração
    sample_questions = [
        "Quantas colunas tem a tabela dados_sus3?",
        "Quantos registros existem na tabela?",
        "Quantos estados diferentes temos nos dados?",
        "Qual a idade média dos pacientes?",
        "Quantos pacientes são do sexo masculino?"
    ]

    print("📚 Testando perguntas de exemplo com debug ativado:")
    print("-" * 60)

    for i, question in enumerate(sample_questions, 1):
        print(f"\n🔍 TESTE {i}: {question}")
        print("=" * 50)

        try:
            # Processar pergunta
            result = agent.process_query(question)

            # Mostrar resultado com debug
            display.show_query_result(result, show_queries=True)

            # Análise adicional das queries
            if 'executed_queries' in result and result['executed_queries']:
                print(f"\n📊 ANÁLISE DAS QUERIES:")

                for j, query in enumerate(result['executed_queries'], 1):
                    print(f"\n   Query {j}: {query}")

                    # Analisar performance da query
                    perf_data = agent.analyze_query_performance(query)
                    complexity = perf_data.get('estimated_complexity', 'desconhecida')
                    analysis_time = perf_data.get('analysis_time_ms', 0)

                    print(f"   ⚡ Complexidade: {complexity}")
                    print(f"   🕐 Tempo de análise: {analysis_time:.2f}ms")

                    if 'error' in perf_data:
                        print(f"   ⚠️  Erro na análise: {perf_data['error']}")

        except Exception as e:
            print(f"❌ Erro ao processar pergunta: {e}")

        print("\n" + "─" * 60)


def demonstrate_query_analysis():
    """Demonstra análise de queries SQL específicas."""

    print("\n\n🔬 Demonstração de Análise de Queries Específicas")
    print("=" * 60)

    try:
        agent = SQLAgent()
        display = DisplayManager()

        # Queries de exemplo para análise
        sample_queries = [
            # Query simples
            "SELECT COUNT(*) FROM dados_sus3;",

            # Query com filtro
            "SELECT COUNT(*) FROM dados_sus3 WHERE SEXO = 1;",

            # Query com GROUP BY
            "SELECT UF_RESIDENCIA_PACIENTE, COUNT(*) FROM dados_sus3 GROUP BY UF_RESIDENCIA_PACIENTE;",

            # Query mais complexa
            """SELECT UF_RESIDENCIA_PACIENTE,
                      AVG(IDADE) as idade_media,
                      COUNT(*)   as total_pacientes
               FROM dados_sus3
               WHERE IDADE > 18
               GROUP BY UF_RESIDENCIA_PACIENTE
               ORDER BY total_pacientes DESC LIMIT 10;"""
        ]

        for i, query in enumerate(sample_queries, 1):
            print(f"\n📝 ANÁLISE DE QUERY {i}:")
            print("-" * 40)

            # Mostrar query formatada
            formatted_query = display._format_sql_query(query)
            print("Query:")
            print(formatted_query)

            # Analisar performance
            perf_data = agent.analyze_query_performance(query)
            display.show_query_performance(perf_data)

    except Exception as e:
        print(f"❌ Erro na análise: {e}")


def demonstrate_development_workflow():
    """Demonstra um workflow típico de desenvolvimento."""

    print("\n\n🛠️  Workflow de Desenvolvimento Típico")
    print("=" * 60)

    print("""
📋 PASSOS RECOMENDADOS PARA DESENVOLVIMENTO:

1️⃣  CONFIGURAÇÃO INICIAL:
   • Configure .env com DEBUG_MODE=true
   • Use MODEL_TEMPERATURE=0.1 para consistência
   • Ative VERBOSE=true para logs detalhados

2️⃣  TESTE DE PERGUNTAS BÁSICAS:
   • "Quantas colunas tem a tabela?"
   • "Quantos registros existem?"
   • Verifique se as queries SQL fazem sentido

3️⃣  ANÁLISE DE QUERIES:
   • Use /debug on na CLI
   • Observe as queries geradas
   • Identifique padrões e problemas

4️⃣  OTIMIZAÇÃO:
   • Use /performance on para medir tempos
   • Teste queries com /analyze
   • Ajuste prompts se necessário

5️⃣  VALIDAÇÃO:
   • Teste casos extremos
   • Verifique tratamento de erros
   • Confirme segurança das queries

💡 DICAS IMPORTANTES:

✅ DO (Faça):
   • Sempre verifique as queries SQL geradas
   • Teste com dados reais do seu domínio
   • Use fallbacks para queries comuns
   • Monitore performance de queries complexas

❌ DON'T (Não faça):
   • Não confie cegamente nas queries geradas
   • Não ignore queries muito lentas
   • Não permita queries destrutivas
   • Não esqueça de validar entradas do usuário

🔧 COMANDOS ÚTEIS NA CLI:

   /debug on          # Ativar visualização de queries
   /performance on    # Ativar análise de performance
   /analyze SELECT... # Testar query específica
   /tips             # Ver dicas de desenvolvimento
    """)


def main():
    """Função principal do exemplo."""

    print("🤖 EXEMPLO DE USO - AGENTE SQL COM DEBUG")
    print("=" * 70)

    try:
        # Demonstrar funcionalidades de debug
        demonstrate_debug_features()

        # Demonstrar análise de queries
        demonstrate_query_analysis()

        # Mostrar workflow de desenvolvimento
        demonstrate_development_workflow()

        print("\n✅ Demonstração concluída com sucesso!")
        print("\n💡 Para usar na prática:")
        print("   1. Execute: python -m src.main")
        print("   2. Use /debug on para ativar debug")
        print("   3. Faça suas perguntas e observe as queries SQL")

    except Exception as e:
        print(f"\n❌ Erro durante demonstração: {e}")
        print("🔧 Verifique se:")
        print("   • O banco de dados existe")
        print("   • As dependências estão instaladas")
        print("   • O modelo Ollama está disponível")


if __name__ == "__main__":
    main()