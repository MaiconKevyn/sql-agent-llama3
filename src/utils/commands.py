"""Processamento de comandos especiais."""

from typing import Dict, Callable, Any


class CommandProcessor:
    """Processador de comandos especiais da interface."""

    def __init__(self):
        """Inicializa o processador de comandos."""
        self.commands: Dict[str, Callable] = {}
        self._register_commands()

    def _register_commands(self) -> None:
        """Registra comandos disponíveis."""
        # Comandos são processados na CLI interface
        # Este módulo pode ser expandido para lógica mais complexa
        pass

    def is_valid_command(self, command: str) -> bool:
        """
        Verifica se um comando é válido.

        Args:
            command: Comando a ser verificado

        Returns:
            True se comando é válido, False caso contrário
        """
        valid_commands = [
            '/help', '/ajuda', '/info', '/exemplos',
            '/limpar', '/quit', '/sair', '/exit'
        ]

        return command.lower().strip() in valid_commands