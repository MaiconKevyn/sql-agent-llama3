"""Interface de linha de comando completa com suporte a debug e performance."""

import sys
import os
from typing import Optional

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.agent import SQLAgent
from src.interface.display import DisplayManager
from src.utils.commands import CommandProcessor


class CLIInterface:
    """Interface de linha de comando para o agente SQL com funcionalidades completas."""

    def __init__(self):
        """Inicializa a interface CLI."""
        self.agent: Optional[SQLAgent] = None
        self.display = DisplayManager()
        self.command_processor = CommandProcessor()
        self.debug_mode = True  # Ativado por padrão durante desenvolvimento
        self.show_performance = False

    def initialize_agent(self) -> bool:
        """
        Inicializa o agente SQL.

        Returns:
            True se inicialização foi bem-sucedida, False caso contrário
        """
        try:
            print("🚀 Iniciando agente SQL...")
            self.agent = SQLAgent()

            # Configurar debug mode no agente
            self.agent.set_debug_mode(self.debug_mode)

            return True
        except Exception as e:
            self.display.show_critical_error(str(e))
            return False

    def run(self) -> None:
        """Executa o loop principal da interface."""
        # Inicializar agente
        if not self.initialize_agent():
            return

        # Mostrar interface inicial
        self.display.clear_terminal()
        self.display.show_banner()
        self.display.show_initialization_success()

        # Loop principal
        while True:
            try:
                # Receber input do usuário
                prompt = "🗣️  Digite sua pergunta (ou /help): "
                if self.debug_mode:
                    prompt = "🐛 [DEBUG] Digite sua pergunta (ou /help): "

                query = input(prompt).strip()

                # Verificar se não está vazio
                if not query:
                    continue

                # Processar comandos especiais
                if query.startswith('/'):
                    should_continue = self._process_command(query)
                    if not should_continue:
                        break
                    continue

                # Processar pergunta normal
                self._process_query(query)
                self.display.show_separator()

            except KeyboardInterrupt:
                self.display.show_interruption()
                break
            except EOFError:
                self.display.show_eof()
                break
            except Exception as e:
                self.display.show_unexpected_error(str(e))

        self.display.show_goodbye()

    def _process_command(self, command: str) -> bool:
        """
        Processa comandos especiais.

        Args:
            command: Comando a ser processado

        Returns:
            True para continuar, False para sair
        """
        command_parts = command.lower().strip().split()
        main_command = command_parts[0] if command_parts else ""

        if main_command in ['/help', '/ajuda']:
            self.display.show_help()
            return True

        elif main_command == '/info':
            if self.agent:
                db_info = self.agent.get_database_info()
                self.display.show_database_info(db_info)
            return True

        elif main_command == '/exemplos':
            self.display.show_examples()
            return True

        elif main_command == '/debug':
            return self._handle_debug_command(command_parts)

        elif main_command == '/performance':
            return self._handle_performance_command(command_parts)

        elif main_command == '/analyze':
            return self._handle_analyze_command(command_parts)

        elif main_command == '/tips':
            self.display.show_development_tips()
            return True

        elif main_command == '/status':
            self._show_status()
            return True

        elif main_command == '/test':
            self._run_test_queries()
            return True

        elif main_command == '/validate':
            return self._handle_validate_command(command_parts)

        elif main_command == '/schema':
            return self._handle_schema_command(command_parts)

        elif main_command == '/limpar':
            self.display.clear_terminal()
            self.display.show_banner()
            return True

        elif main_command in ['/quit', '/sair', '/exit']:
            return False

        else:
            print(f"❌ Comando desconhecido: {command}")
            print("💡 Digite /help para ver comandos disponíveis")
            return True

    def _handle_debug_command(self, command_parts: list) -> bool:
        """
        Processa comando de debug.

        Args:
            command_parts: Partes do comando (/debug on/off)

        Returns:
            True para continuar
        """
        if len(command_parts) < 2:
            self.display.show_debug_status(self.debug_mode)
            print("💡 Use: /debug on ou /debug off")
            return True

        action = command_parts[1].lower()

        if action == 'on':
            self.debug_mode = True
            if self.agent:
                self.agent.set_debug_mode(True)
            self.display.show_debug_status(True)

        elif action == 'off':
            self.debug_mode = False
            if self.agent:
                self.agent.set_debug_mode(False)
            self.display.show_debug_status(False)

        else:
            print("❌ Use: /debug on ou /debug off")

        return True

    def _handle_performance_command(self, command_parts: list) -> bool:
        """
        Processa comando de performance.

        Args:
            command_parts: Partes do comando

        Returns:
            True para continuar
        """
        if len(command_parts) < 2:
            self.show_performance = not self.show_performance
            status = "ativado" if self.show_performance else "desativado"
            print(f"⚡ Modo performance {status}")
            return True

        action = command_parts[1].lower()

        if action == 'on':
            self.show_performance = True
            print("⚡ Análise de performance ativada")
        elif action == 'off':
            self.show_performance = False
            print("⚡ Análise de performance desativada")
        else:
            print("❌ Use: /performance on ou /performance off")

        return True

    def _handle_analyze_command(self, command_parts: list) -> bool:
        """
        Analisa uma query SQL específica.

        Args:
            command_parts: Partes do comando

        Returns:
            True para continuar
        """
        if len(command_parts) < 2:
            print("❌ Use: /analyze SELECT * FROM dados_sus3 LIMIT 10")
            print("💡 Exemplo: /analyze SELECT COUNT(*) FROM dados_sus3")
            return True

        # Juntar todas as partes exceto a primeira para formar a query
        sql_query = " ".join(command_parts[1:])

        if not self.agent:
            print("❌ Agente não inicializado")
            return True

        print(f"🔍 Analisando query: {sql_query}")

        try:
            performance_data = self.agent.analyze_query_performance(sql_query)
            self.display.show_query_performance(performance_data)
        except Exception as e:
            print(f"❌ Erro ao analisar query: {e}")

        return True

    def _handle_validate_command(self, command_parts: list) -> bool:
        """
        Valida uma query SQL específica contra o schema.

        Args:
            command_parts: Partes do comando

        Returns:
            True para continuar
        """
        if len(command_parts) < 2:
            print("❌ Use: /validate SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1")
            print("💡 Exemplo: /validate SELECT COUNT(*) FROM dados_sus3 WHERE CID_MORTE > 0")
            return True

        # Juntar todas as partes exceto a primeira para formar a query
        sql_query = " ".join(command_parts[1:])

        if not self.agent:
            print("❌ Agente não inicializado")
            return True

        print(f"🔍 Validando query: {sql_query}")

        try:
            validation_result = self.agent.validate_query_against_schema(sql_query)

            print(f"\n📋 RESULTADO DA VALIDAÇÃO:")
            print("=" * 40)

            if validation_result['is_valid']:
                print("✅ Query válida - nenhum problema detectado")
            else:
                print("⚠️  Problemas detectados:")
                for issue in validation_result['issues']:
                    print(f"   ❌ {issue}")

                if validation_result['suggestions']:
                    print("\n💡 Sugestões:")
                    for suggestion in validation_result['suggestions']:
                        print(f"   • {suggestion}")

            print("=" * 40)

        except Exception as e:
            print(f"❌ Erro ao validar query: {e}")

        return True

    def _handle_schema_command(self, command_parts: list) -> bool:
        """
        Mostra informações do schema para uma coluna específica.

        Args:
            command_parts: Partes do comando

        Returns:
            True para continuar
        """
        if len(command_parts) < 2:
            print("❌ Use: /schema NOME_COLUNA")
            print("💡 Exemplo: /schema MORTE")
            print("💡 Exemplo: /schema CIDADE_RESIDENCIA_PACIENTE")
            return True

        column_name = command_parts[1].upper()

        if not self.agent:
            print("❌ Agente não inicializado")
            return True

        try:
            from src.utils.schema_documentation import schema_docs
            column_info = schema_docs.get_column_info(column_name)

            print(f"\n📋 INFORMAÇÕES DA COLUNA: {column_name}")
            print("=" * 50)

            if 'descricao' in column_info and column_info['descricao'] != "Coluna não documentada":
                print(f"📖 Nome: {column_info.get('nome', column_name)}")
                print(f"📊 Tipo: {column_info.get('tipo', 'N/A')}")
                print(f"📝 Descrição: {column_info.get('descricao', 'N/A')}")

                if 'valores_validos' in column_info:
                    print(f"✅ Valores válidos:")
                    for key, value in column_info['valores_validos'].items():
                        print(f"   {key}: {value}")

                if 'exemplos' in column_info:
                    exemplos = ", ".join(map(str, column_info['exemplos'][:5]))
                    print(f"💡 Exemplos: {exemplos}")

                if 'uso_comum' in column_info:
                    print(f"🎯 Uso comum: {column_info['uso_comum']}")

                if 'nota' in column_info:
                    print(f"⚠️  Nota: {column_info['nota']}")

                if 'query_exemplo' in column_info:
                    print(f"📋 Query exemplo: {column_info['query_exemplo']}")

            else:
                print(f"❌ Coluna '{column_name}' não encontrada na documentação")
                print("💡 Colunas disponíveis: MORTE, SEXO, CIDADE_RESIDENCIA_PACIENTE, UF_RESIDENCIA_PACIENTE, IDADE, etc.")

            print("=" * 50)

        except Exception as e:
            print(f"❌ Erro ao buscar informações da coluna: {e}")

        return True

    def _show_status(self) -> None:
        """Mostra status atual do sistema."""
        print("\n📊 STATUS DO SISTEMA:")
        print("=" * 40)
        print(f"🐛 Debug Mode: {'✅ Ativado' if self.debug_mode else '❌ Desativado'}")
        print(f"⚡ Performance Mode: {'✅ Ativado' if self.show_performance else '❌ Desativado'}")
        print(f"🤖 Agente: {'✅ Inicializado' if self.agent else '❌ Não inicializado'}")

        if self.agent:
            try:
                db_info = self.agent.get_database_info()
                total_tables = db_info.get('total_tables', 0)
                print(f"🗄️  Tabelas disponíveis: {total_tables}")

                # Mostrar informação da primeira tabela se existir
                if db_info.get('tables'):
                    first_table = db_info['tables'][0]
                    record_count = first_table.get('record_count', 'N/A')
                    if isinstance(record_count, int):
                        print(f"📊 Registros na tabela principal: {record_count:,}")
                    else:
                        print(f"📊 Registros na tabela principal: {record_count}")

            except Exception as e:
                print(f"⚠️  Erro ao obter info do banco: {e}")

        print("=" * 40)

    def _run_test_queries(self) -> None:
        """Executa queries de teste para verificar funcionamento."""
        if not self.agent:
            print("❌ Agente não inicializado")
            return

        print("\n🧪 EXECUTANDO TESTES RÁPIDOS...")
        print("=" * 50)

        test_queries = [
            "Quantas colunas tem a tabela?",
            "Quantos registros existem?",
            "Quantos estados diferentes temos?",
            "Quantas cidades diferentes existem?",
            "Quantas mortes houve?"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Teste {i}: {query}")
            try:
                result = self.agent.process_query(query)
                if result['success']:
                    print(f"✅ {result['response']}")
                    if self.debug_mode and 'executed_queries' in result:
                        for sql in result['executed_queries']:
                            print(f"   SQL: {sql}")

                    # Mostrar se houve correção automática
                    if 'agent_bypassed' in result:
                        print(f"🔧 Bypass aplicado: {result['bypass_reason']}")
                    elif 'agent_error_detected' in result:
                        print(f"🔧 Erro corrigido: {result['agent_error']}")

                else:
                    print(f"❌ {result['response']}")
            except Exception as e:
                print(f"❌ Erro: {e}")

        print("\n✅ Testes concluídos!")

    def _process_query(self, query: str) -> None:
        """
        Processa uma pergunta do usuário.

        Args:
            query: Pergunta em linguagem natural
        """
        if not self.agent:
            print("❌ Agente não inicializado")
            return

        self.display.show_query_processing(query)

        try:
            # Medir tempo de processamento se modo performance ativo
            import time
            start_time = time.time()

            result = self.agent.process_query(query)

            processing_time = time.time() - start_time

            # 🔧 CORREÇÃO PRINCIPAL: Passar corretamente o debug mode
            self.display.show_query_result(result, show_queries=self.debug_mode)

            # Mostrar informações de performance se ativo
            if self.show_performance:
                print(f"\n⚡ INFORMAÇÕES DE PERFORMANCE:")
                print(f"   🕐 Tempo total: {processing_time:.3f}s")

                if 'query_count' in result and result['query_count'] > 0:
                    avg_time = processing_time / result['query_count']
                    print(f"   📊 Tempo médio por query: {avg_time:.3f}s")
                    print(f"   🔢 Total de queries: {result['query_count']}")

                # Analisar complexidade de cada query se debug ativo
                if self.debug_mode and 'executed_queries' in result:
                    print(f"\n   📋 Análise de complexidade:")
                    for i, sql_query in enumerate(result['executed_queries'], 1):
                        try:
                            perf_data = self.agent.analyze_query_performance(sql_query)
                            complexity = perf_data.get('estimated_complexity', 'desconhecida')
                            print(f"      Query {i}: {complexity}")
                        except:
                            print(f"      Query {i}: erro na análise")

        except Exception as e:
            error_result = {
                "success": False,
                "response": f"Erro ao processar pergunta: {str(e)}",
                "method": "exception",
                "executed_queries": [],
                "query_count": 0,
                "error_details": str(e)
            }
            # 🔧 Passar debug mode também para erros
            self.display.show_query_result(error_result, show_queries=self.debug_mode)

    def get_debug_mode(self) -> bool:
        """Retorna status do modo debug."""
        return self.debug_mode

    def get_performance_mode(self) -> bool:
        """Retorna status do modo performance."""
        return self.show_performance

    def set_modes(self, debug: bool = None, performance: bool = None) -> None:
        """
        Define modos de operação.

        Args:
            debug: Ativar/desativar debug (None para manter atual)
            performance: Ativar/desativar performance (None para manter atual)
        """
        if debug is not None:
            self.debug_mode = debug
            if self.agent:
                self.agent.set_debug_mode(debug)

        if performance is not None:
            self.show_performance = performance

    def toggle_debug(self) -> bool:
        """
        Alterna modo debug.

        Returns:
            Novo status do debug mode
        """
        self.debug_mode = not self.debug_mode
        if self.agent:
            self.agent.set_debug_mode(self.debug_mode)
        return self.debug_mode

    def toggle_performance(self) -> bool:
        """
        Alterna modo performance.

        Returns:
            Novo status do performance mode
        """
        self.show_performance = not self.show_performance
        return self.show_performance