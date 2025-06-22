#!/usr/bin/env python3
"""
Exemplo de teste do CLI com funcionalidades de debug.

Este script demonstra como usar a interface CLI atualizada
com todas as funcionalidades de debug implementadas.
"""

import sys
import os
from typing import List
from unittest.mock import Mock, patch

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.interface.cli import CLIInterface
from src.utils.commands import CommandProcessor


class CLITester:
    """Classe para testar funcionalidades do CLI."""

    def __init__(self):
        self.cli = CLIInterface()
        self.command_processor = CommandProcessor()

    def test_command_validation(self):
        """Testa validação de comandos."""
        print("🧪 TESTANDO VALIDAÇÃO DE COMANDOS")
        print("=" * 50)

        test_commands = [
            "/help",
            "/debug on",
            "/debug off",
            "/debug invalid",
            "/performance on",
            "/analyze SELECT COUNT(*) FROM dados_sus3",
            "/analyze",
            "/invalid_command",
            "/quit"
        ]

        for command in test_commands:
            validation = self.command_processor.validate_command_parameters(command)
            status = "✅" if validation['valid'] else "❌"
            print(f"{status} {command:<30} - {validation.get('error', 'Válido')}")

    def test_command_help(self):
        """Testa sistema de ajuda."""
        print("\n🧪 TESTANDO SISTEMA DE AJUDA")
        print("=" * 50)

        # Ajuda geral
        help_text = self.command_processor.get_help_text(detailed=False)
        print("📚 Ajuda Resumida:")
        print(help_text[:300] + "..." if len(help_text) > 300 else help_text)

        # Comandos por categoria
        categories = self.command_processor.get_commands_by_category()
        print(f"\n📊 Categorias encontradas: {list(categories.keys())}")

        # Sugestões de comandos
        suggestions = self.command_processor.get_command_suggestions("/deb")
        print(f"💡 Sugestões para '/deb': {suggestions}")

    def test_debug_functionality(self):
        """Testa funcionalidades específicas de debug."""
        print("\n🧪 TESTANDO FUNCIONALIDADES DE DEBUG")
        print("=" * 50)

        # Status inicial
        print(f"🐛 Debug inicial: {self.cli.get_debug_mode()}")
        print(f"⚡ Performance inicial: {self.cli.get_performance_mode()}")

        # Alterar modos
        self.cli.set_modes(debug=False, performance=True)
        print(f"🐛 Debug após mudança: {self.cli.get_debug_mode()}")
        print(f"⚡ Performance após mudança: {self.cli.get_performance_mode()}")

        # Comandos de debug disponíveis
        debug_commands = self.command_processor.get_debug_commands()
        print(f"🔧 Comandos de debug: {debug_commands}")

    def simulate_user_session(self):
        """Simula uma sessão típica de usuário."""
        print("\n🧪 SIMULANDO SESSÃO DE USUÁRIO")
        print("=" * 50)

        # Simular comandos que um usuário típico faria
        user_commands = [
            "/help",
            "/status",
            "/debug on",
            "/exemplos",
            "/debug off",
            "/performance on",
            "/tips"
        ]

        for command in user_commands:
            print(f"\n👤 Usuário digita: {command}")

            if self.command_processor.is_valid_command(command):
                cmd_info = self.command_processor.get_command_info(command)
                print(f"   ✅ Comando válido: {cmd_info.get('description', 'N/A')}")

                # Simular processamento específico
                if command == "/status":
                    print("   📊 [Simulado] Status do sistema exibido")
                elif command.startswith("/debug"):
                    mode = "ativado" if "on" in command else "desativado"
                    print(f"   🐛 [Simulado] Debug mode {mode}")
                elif command == "/performance on":
                    print("   ⚡ [Simulado] Performance mode ativado")
                elif command == "/exemplos":
                    print("   💡 [Simulado] Exemplos de perguntas exibidos")
                elif command == "/tips":
                    print("   🛠️ [Simulado] Dicas de desenvolvimento exibidas")

            else:
                error_msg = self.command_processor.format_command_error(command, "Comando inválido")
                print(f"   {error_msg}")

    def test_query_processing_flow(self):
        """Testa fluxo de processamento de queries."""
        print("\n🧪 TESTANDO FLUXO DE PROCESSAMENTO")
        print("=" * 50)

        # Simular perguntas típicas sem realmente executar
        sample_questions = [
            "Quantas colunas tem a tabela?",
            "Quantos registros existem?",
            "Qual a idade média dos pacientes?",
            "Quantos estados diferentes temos?"
        ]

        print("📝 Perguntas que seriam processadas:")
        for i, question in enumerate(sample_questions, 1):
            print(f"   {i}. {question}")

            # Simular resultado
            print(f"      🔍 [Simulado] Query SQL seria gerada")
            print(f"      ✅ [Simulado] Resultado seria exibido")
            if self.cli.get_debug_mode():
                print(f"      🐛 [Simulado] Query SQL seria mostrada")
            if self.cli.get_performance_mode():
                print(f"      ⚡ [Simulado]