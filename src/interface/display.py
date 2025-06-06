"""Componentes de exibição e formatação."""

import os
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
  /limpar           - Limpa a tela
  /quit ou /sair    - Sai do programa

🔍 TIPOS DE PERGUNTAS:

  • Sobre estrutura: "Quantas colunas tem a tabela?"
  • Sobre dados: "Quantos registros existem?"
  • Análises: "Qual a média de idade dos pacientes?"
  • Filtros: "Quantos pacientes são do Rio Grande do Sul?"

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
    def show_query_result(result: Dict[str, Any]) -> None:
        """Mostra resultado de uma query."""
        if result["success"]:
            print(f"\n✅ Resposta: {result['response']}")
        else:
            print(f"\n❌ {result['response']}")

            if result["method"] == "failed":
                print("💡 Tente usar os comandos /exemplos para ver perguntas válidas.")
                print("🔍 Ou reformule a pergunta de forma mais específica.")

    @staticmethod
    def show_separator() -> None:
        """Mostra separador entre perguntas."""
        print("\n" + "-" * 60 + "\n")

    @staticmethod
    def show_initialization_success() -> None:
        """Mostra mensagem de inicialização bem-sucedida."""
        print("✅ Agente inicializado com sucesso!")
        print("🇧🇷 Configurado para responder em português brasileiro")
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