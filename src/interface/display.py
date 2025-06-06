"""Componentes de exibição e formatação com suporte a debug de queries."""

import os
import re
from typing import Dict, Any, List


class DisplayManager:
    """Gerencia exibição de informações na interface."""

    @staticmethod
    def clear_terminal() -> None:
        """Limpa o terminal."""
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def show_banner() -> None:
        """Mostra o banner inicial do programa."""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 AGENTE SQL INTERATIVO                  ║
║                    🇧🇷 Respostas em Português               ║
║                                                              ║
║  Faça perguntas sobre o banco de dados em linguagem natural ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)

    @staticmethod
    def show_help() -> None:
        """Mostra comandos disponíveis."""
        help_text = """
📚 COMANDOS DISPONÍVEIS:

  /help ou /ajuda    - Mostra esta ajuda
  /info             - Informações sobre o banco de dados
  /exemplos         - Exemplos de perguntas que você pode fazer
  /debug on/off     - Ativa/desativa exibição de queries SQL
  /limpar           - Limpa a tela
  /quit ou /sair    - Sai do programa

🔍 TIPOS DE PERGUNTAS:

  • Sobre estrutura: "Quantas colunas tem a tabela?"
  • Sobre dados: "Quantos registros existem?"
  • Análises: "Qual a média de idade dos pacientes?"
  • Filtros: "Quantos pacientes são do Rio Grande do Sul?"

💡 MODO DEBUG:
  
  Durante o desenvolvimento, use '/debug on' para ver as queries SQL
  que são executadas para responder suas perguntas.

        """
        print(help_text)

    @staticmethod
    def show_examples() -> None:
        """Mostra exemplos de perguntas."""
        examples = """
💡 EXEMPLOS DE PERGUNTAS:

📊 ESTRUTURA:
  • "Quantas colunas tem a tabela dados_sus3?"
  • "Qual é a estrutura da tabela?"
  • "Quais são os tipos de dados das colunas?"

📈 CONTAGENS:
  • "Quantos registros existem na tabela?"
  • "Quantos pacientes são do sexo masculino?"
  • "Quantos pacientes morreram?"

🔍 ANÁLISES:
  • "Qual a idade média dos pacientes?"
  • "Qual o valor total gasto em internações?"
  • "Quantos pacientes ficaram na UTI?"

🏥 FILTROS ESPECÍFICOS:
  • "Quantos pacientes são de Santa Maria?"
  • "Quais os principais diagnósticos?"
  • "Qual o procedimento mais realizado?"

🌍 GEOGRÁFICAS:
  • "Quantos estados diferentes temos?"
  • "Quais as cidades com mais pacientes?"
        """
        print(examples)

    @staticmethod
    def show_database_info(db_info: Dict[str, Any]) -> None:
        """Mostra informações sobre o banco de dados."""
        print("\n📊 INFORMAÇÕES DO BANCO DE DADOS:")
        print("=" * 50)

        table_names = [table["name"] for table in db_info["tables"]]
        print(f"📁 Tabelas disponíveis: {', '.join(table_names)}")

        for table in db_info["tables"]:
            print(f"\n🏥 Tabela: {table['name']}")

            if isinstance(table['record_count'], int):
                print(f"   📊 Registros: {table['record_count']:,}")
            else:
                print(f"   📊 Registros: {table['record_count']}")

            print(f"   📋 Colunas: {table['columns_count']}")

            if 'error' in table:
                print(f"   ⚠️  Erro: {table['error']}")

        print("\n" + "=" * 50)

    @staticmethod
    def show_query_processing(query: str) -> None:
        """Mostra que a query está sendo processada."""
        print(f"\n🤔 Processando: {query}")
        print("⏳ Aguarde...")

    @staticmethod
    def _format_sql_query(query: str) -> str:
        """
        Formata query SQL para exibição com destaque de sintaxe básico.

        Args:
            query: Query SQL bruta

        Returns:
            Query formatada com indentação
        """
        # Remover quebras de linha extras e espaços
        clean_query = ' '.join(query.split())

        # Adicionar quebras de linha em pontos estratégicos
        formatted = clean_query
        formatted = re.sub(r'\bSELECT\b', '\nSELECT', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bFROM\b', '\n  FROM', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bWHERE\b', '\n  WHERE', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bGROUP BY\b', '\n  GROUP BY', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bORDER BY\b', '\n  ORDER BY', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bLIMIT\b', '\n  LIMIT', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bINNER JOIN\b', '\n  INNER JOIN', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bLEFT JOIN\b', '\n  LEFT JOIN', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\bRIGHT JOIN\b', '\n  RIGHT JOIN', formatted, flags=re.IGNORECASE)

        return formatted.strip()

    @staticmethod
    def show_executed_queries(queries: List[str], method: str) -> None:
        """
        Mostra as queries SQL que foram executadas.

        Args:
            queries: Lista de queries executadas
            method: Método usado (agent, fallback, etc.)
        """
        if not queries:
            return

        print(f"\n🔍 QUERY(S) EXECUTADA(S) [{method.upper()}]:")
        print("=" * 60)

        for i, query in enumerate(queries, 1):
            if len(queries) > 1:
                print(f"\n📝 Query {i}:")

            formatted_query = DisplayManager._format_sql_query(query)

            # Adicionar box ao redor da query
            query_lines = formatted_query.split('\n')
            max_length = max(len(line) for line in query_lines) if query_lines else 0

            print("┌─" + "─" * max_length + "─┐")
            for line in query_lines:
                print(f"│ {line:<{max_length}} │")
            print("└─" + "─" * max_length + "─┘")

        print("=" * 60)

    @staticmethod
    def show_query_result(result: Dict[str, Any], show_queries: bool = True) -> None:
        """
        Mostra resultado de uma query.

        Args:
            result: Resultado da consulta
            show_queries: Se deve mostrar as queries executadas
        """
        # Mostrar queries executadas primeiro (se habilitado)
        if show_queries and 'executed_queries' in result and result['executed_queries']:
            DisplayManager.show_executed_queries(
                result['executed_queries'],
                result.get('method', 'unknown')
            )

        # Mostrar resultado principal
        if result["success"]:
            print(f"\n✅ Resposta: {result['response']}")

            # Mostrar estatísticas se disponíveis
            if 'query_count' in result and result['query_count'] > 0:
                print(f"📊 {result['query_count']} query(s) executada(s)")

        else:
            print(f"\n❌ {result['response']}")

            # Mostrar queries mesmo em caso de erro (para debug)
            if show_queries and 'executed_queries' in result and result['executed_queries']:
                print("🔍 Queries que foram tentadas:")
                for query in result['executed_queries']:
                    print(f"   • {query}")

            if result["method"] == "failed":
                print("💡 Tente usar os comandos /exemplos para ver perguntas válidas.")
                print("🔍 Ou reformule a pergunta de forma mais específica.")

            # Mostrar detalhes do erro se disponível
            if 'error_details' in result:
                print(f"🐛 Detalhes do erro: {result['error_details']}")

    @staticmethod
    def show_debug_status(enabled: bool) -> None:
        """
        Mostra status do modo debug.

        Args:
            enabled: True se debug está ativado
        """
        if enabled:
            print("🐛 Modo DEBUG ativado - Queries SQL serão exibidas")
        else:
            print("🔒 Modo DEBUG desativado - Queries SQL não serão exibidas")

    @staticmethod
    def show_query_performance(performance_data: Dict[str, Any]) -> None:
        """
        Mostra informações de performance de uma query.

        Args:
            performance_data: Dados de performance da query
        """
        print(f"\n⚡ ANÁLISE DE PERFORMANCE:")
        print("=" * 50)

        if 'error' in performance_data:
            print(f"❌ Erro na análise: {performance_data['error']}")
        else:
            print(f"🕐 Tempo de análise: {performance_data['analysis_time_ms']:.2f}ms")
            print(f"📊 Complexidade estimada: {performance_data['estimated_complexity']}")

            if 'execution_plan' in performance_data:
                print("\n📋 Plano de execução:")
                for step in performance_data['execution_plan']:
                    print(f"   • {step}")

        print("=" * 50)

    @staticmethod
    def show_separator() -> None:
        """Mostra separador entre perguntas."""
        print("\n" + "-" * 60 + "\n")

    @staticmethod
    def show_initialization_success() -> None:
        """Mostra mensagem de inicialização bem-sucedida."""
        print("✅ Agente inicializado com sucesso!")
        print("🇧🇷 Configurado para responder em português brasileiro")
        print("🐛 Modo DEBUG ativado - use '/debug off' para desativar")
        print("💡 Digite /help para ver comandos disponíveis\n")

    @staticmethod
    def show_goodbye() -> None:
        """Mostra mensagem de despedida."""
        print("\n👋 Obrigado por usar o Agente SQL! Até mais!")

    @staticmethod
    def show_interruption() -> None:
        """Mostra mensagem de interrupção."""
        print("\n\n⚠️  Interrompido pelo usuário (Ctrl+C)")

    @staticmethod
    def show_eof() -> None:
        """Mostra mensagem de EOF."""
        print("\n\n👋 Finalizando...")

    @staticmethod
    def show_unexpected_error(error: str) -> None:
        """Mostra erro inesperado."""
        print(f"\n❌ Erro inesperado: {error}")
        print("💡 Tente novamente ou digite /help")

    @staticmethod
    def show_critical_error(error: str) -> None:
        """Mostra erro crítico de inicialização."""
        print(f"❌ Erro crítico ao inicializar: {error}")
        print("🔧 Verifique se:")
        print("   • O modelo llama3 está disponível no Ollama")
        print("   • O arquivo sus_data.db existe")
        print("   • As dependências estão instaladas")

    @staticmethod
    def show_development_tips() -> None:
        """Mostra dicas para desenvolvimento."""
        tips = """
🛠️  DICAS PARA DESENVOLVIMENTO:

📊 ANÁLISE DE QUERIES:
  • Use '/debug on' para ver todas as queries SQL executadas
  • Observe como a LLM interpreta suas perguntas
  • Identifique padrões de queries ineficientes

🔍 DEBUG EFICIENTE:
  • Teste perguntas similares para ver variações nas queries
  • Verifique se as queries fazem sentido para a pergunta
  • Use queries simples para testar funcionalidades específicas

⚡ OTIMIZAÇÃO:
  • Queries com muitos JOINs podem ser lentas
  • COUNT(*) é geralmente mais rápido que COUNT(coluna)
  • LIMIT é seu amigo para testes rápidos

🐛 TROUBLESHOOTING:
  • Se uma query falha, veja exatamente qual SQL foi gerado
  • Compare com queries que funcionam
  • Teste a query manualmente no SQLite se necessário
        """
        print(tips)