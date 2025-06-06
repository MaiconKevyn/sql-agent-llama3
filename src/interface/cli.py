"""Interface de linha de comando."""

import sys
import os
from typing import Optional

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.agent import SQLAgent
from src.interface.display import DisplayManager
from src.utils.commands import CommandProcessor


class CLIInterface:
    """Interface de linha de comando para o agente SQL."""

    def __init__(self):
        """Inicializa a interface CLI."""
        self.agent: Optional[SQLAgent] = None
        self.display = DisplayManager()
        self.command_processor = CommandProcessor()

    def initialize_agent(self) -> bool:
        """
        Inicializa o agente SQL.

        Returns:
            True se inicialização foi bem-sucedida, False caso contrário
        """
        try:
            print("🚀 Iniciando agente SQL...")
            self.agent = SQLAgent()
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
                query = input("🗣️  Digite sua pergunta (ou /help): ").strip()

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
        command_lower = command.lower().strip()

        if command_lower in ['/help', '/ajuda']:
            self.display.show_help()
            return True

        elif command_lower == '/info':
            if self.agent:
                db_info = self.agent.get_database_info()
                self.display.show_database_info(db_info)
            return True

        elif command_lower == '/exemplos':
            self.display.show_examples()
            return True

        elif command_lower == '/limpar':
            self.display.clear_terminal()
            self.display.show_banner()
            return True

        elif command_lower in ['/quit', '/sair', '/exit']:
            return False

        else:
            print(f"❌ Comando desconhecido: {command}")
            print("💡 Digite /help para ver comandos disponíveis")
            return True

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
            result = self.agent.process_query(query)
            self.display.show_query_result(result)
        except Exception as e:
            error_result = {
                "success": False,
                "response": f"Erro ao processar pergunta: {str(e)}",
                "method": "exception"
            }
            self.display.show_query_result(error_result)