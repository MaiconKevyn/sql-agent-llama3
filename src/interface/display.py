"""Componentes de exibição com controle correto do modo debug."""

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
║                                                              ║
║                                                              ║
║               Faça perguntas sobre o banco de dados          ║
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
  /debug on/off     - Liga/desliga modo debug (mostra SQL executado)
  /performance on/off - Liga/desliga análise de performance
  /analyze <SQL>    - Analisa uma query SQL específica
  /tips             - Dicas de desenvolvimento e otimização
  /status           - Status atual do sistema
  /test             - Executa testes rápidos
  /limpar           - Limpa a tela
  /quit ou /sair    - Sai do programa

🔍 TIPOS DE PERGUNTAS:

  • Sobre estrutura: "Quantas colunas tem a tabela?"
  • Sobre dados: "Quantos registros existem?"
  • Análises: "Qual a média de idade dos pacientes?"
  • Filtros: "Quantos pacientes são do Rio Grande do Sul?"
  • Mortalidade: "Quantas mortes houve em Porto Alegre?"

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
  • "Quantas cidades diferentes temos?"

🔍 ANÁLISES:
  • "Qual a idade média dos pacientes?"
  • "Qual o valor total gasto em internações?"
  • "Quantos pacientes ficaram na UTI?"

🏥 FILTROS ESPECÍFICOS:
  • "Quantos pacientes são de Santa Maria?"
  • "Quantas mortes houve em Porto Alegre?"
  • "Quais os principais diagnósticos?"
  • "Qual o procedimento mais realizado?"

🌍 GEOGRÁFICAS:
  • "Quantos estados diferentes temos?"
  • "Quais as cidades com mais pacientes?"
  • "Quais cidades distintas existem?"

💡 DICA: Use modo debug (/debug on) para ver as queries SQL executadas!
        """
        print(examples)

    @staticmethod
    def show_development_tips() -> None:
        """Mostra dicas de desenvolvimento e otimização."""
        tips = """
🛠️  DICAS DE DESENVOLVIMENTO:

📊 ANÁLISE DE DADOS:
  • Use /debug on para ver queries SQL executadas
  • Use /performance on para medir tempo de execução
  • Use /analyze <SQL> para testar queries específicas

🔍 TROUBLESHOOTING:
  • Se resposta está incorreta, verifique a query SQL no debug
  • Mortalidade: sempre use MORTE = 1, nunca CID_MORTE > 0
  • Geografia: prefira CIDADE_RESIDENCIA_PACIENTE ao invés de MUNIC_RES
  • Sexo: 1=Masculino, 3=Feminino (não existe 2!)

⚡ PERFORMANCE:
  • Queries com DISTINCT são mais lentas
  • LIMIT reduz tempo de execução para listagens
  • GROUP BY pode ser custoso em tabelas grandes

🧪 TESTES:
  • Use /test para executar verificações rápidas
  • Use /status para ver estado do sistema
  • Teste sempre com dados reais antes de confiar

💾 SCHEMA:
  • dados_sus3: tabela principal com ~58k registros
  • MORTE = 1: indica óbito hospitalar
  • CIDADE_RESIDENCIA_PACIENTE: nome completo da cidade
  • UTI_MES_TO: dias em UTI (0 = não ficou)
        """
        print(tips)

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
    def show_debug_status(debug_enabled: bool) -> None:
        """Mostra status do modo debug."""
        if debug_enabled:
            print("🐛 Debug mode: ✅ ATIVADO")
            print("   💡 Queries SQL serão exibidas")
            print("   💡 Passos intermediários serão mostrados")
            print("   💡 Use '/debug off' para desativar")
        else:
            print("🐛 Debug mode: ❌ DESATIVADO")
            print("   💡 Queries SQL NÃO serão exibidas")
            print("   💡 Use '/debug on' para ativar")

    @staticmethod
    def show_query_processing(query: str) -> None:
        """Mostra que a query está sendo processada."""
        print(f"\n🤔 Processando: {query}")
        print("⏳ Aguarde...")

    @staticmethod
    def show_query_result(result: Dict[str, Any], show_queries: bool = False) -> None:
        """
        🔧 VERSÃO CORRIGIDA - Mostra resultado de uma query respeitando modo debug.

        Args:
            result: Resultado da query
            show_queries: Se deve mostrar queries SQL executadas (baseado no debug mode)
        """
        if result["success"]:
            print(f"\n✅ Resposta: {result['response']}")

            # 🔧 Mostrar se houve correção automática (SEMPRE mostrar, independente do debug)
            if 'agent_bypassed' in result:
                print(f"🔧 Correção automática aplicada: {result['bypass_reason']}")

            if 'agent_error_detected' in result:
                print(f"⚠️  Erro detectado no agente LLM: {result['agent_error']}")
                print(f"❌ Resposta incorreta do agente: {result['wrong_agent_response']}")
                if 'wrong_query' in result:
                    print(f"❌ Query incorreta executada: {result['wrong_query']}")
                print(f"✅ Correção aplicada automaticamente via fallback")

            if 'fallback_reason' in result:
                print(f"💡 Motivo: {result['fallback_reason']}")

            # 🔧 CORREÇÃO PRINCIPAL: Só mostrar informações de debug se show_queries=True
            if show_queries:
                # Mostrar queries SQL executadas
                if 'executed_queries' in result and result['executed_queries']:
                    print(f"\n🐛 DEBUG - SQL Executado:")
                    for i, query in enumerate(result['executed_queries'], 1):
                        print(f"   {i}. {query}")

                # Mostrar método usado
                if 'method' in result:
                    method_info = {
                        'agent': '🤖 Agente LLM',
                        'fallback_columns': '📊 Fallback - Contagem de colunas',
                        'fallback_records': '📈 Fallback - Contagem de registros',
                        'fallback_cities': '🏙️  Fallback - Contagem de cidades',
                        'fallback_states': '🗺️  Fallback - Contagem de estados',
                        'fallback_list_cities': '📋 Fallback - Lista de cidades',
                        'fallback_deaths': '💀 Fallback - Contagem de mortes',
                        'fallback_age': '👶 Fallback - Idade média',
                        'fallback_schema': '🗂️  Fallback - Estrutura da tabela'
                    }
                    method_desc = method_info.get(result['method'], result['method'])
                    print(f"   📋 Método: {method_desc}")

                # Mostrar correções de schema se houver
                if 'schema_correction' in result:
                    print(f"   🔧 {result['schema_correction']}")

                # Mostrar validações se houver problemas
                if 'query_validation' in result:
                    print(f"\n⚠️  VALIDAÇÃO DE SCHEMA:")
                    for validation in result['query_validation']:
                        if not validation['is_valid']:
                            for issue in validation['issues']:
                                print(f"   ❌ {issue}")
                            for suggestion in validation['suggestions']:
                                print(f"   💡 {suggestion}")

                # Mostrar passos intermediários se disponíveis
                if 'intermediate_steps' in result and result['intermediate_steps']:
                    print(f"\n🔍 DEBUG - Passos do Agente LLM:")
                    for i, step in enumerate(result['intermediate_steps'][:3], 1):  # Limitar a 3 passos
                        print(f"   Passo {i}: {str(step)[:100]}...")  # Truncar para não poluir

            # 🔧 Mostrar apenas correções importantes mesmo sem debug
            elif 'schema_correction' in result:
                print(f"🔧 {result['schema_correction']}")

        else:
            print(f"\n❌ {result['response']}")

            # Mostrar detalhes do erro APENAS se em modo debug
            if show_queries and 'error_details' in result:
                print(f"🐛 Detalhes do erro: {result['error_details']}")

            if result["method"] == "failed":
                print("💡 Tente usar os comandos /exemplos para ver perguntas válidas.")
                print("🔍 Ou reformule a pergunta de forma mais específica.")

    @staticmethod
    def show_query_performance(performance_data: Dict[str, Any]) -> None:
        """
        Mostra informações de performance de uma query.

        Args:
            performance_data: Dados de performance da query
        """
        print(f"\n⚡ ANÁLISE DE PERFORMANCE:")
        print("=" * 40)

        if 'error' in performance_data:
            print(f"❌ Erro na análise: {performance_data['error']}")
            return

        print(f"🔍 Query: {performance_data['query']}")
        print(f"⏱️  Tempo de análise: {performance_data['analysis_time_ms']:.2f}ms")
        print(f"📊 Complexidade estimada: {performance_data['estimated_complexity']}")

        if 'execution_plan' in performance_data:
            print(f"\n📋 Plano de execução:")
            for i, step in enumerate(performance_data['execution_plan'], 1):
                print(f"   {i}. {step}")

        print("=" * 40)

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
        print("   • Execute: python scripts/setup_database.py se necessário")