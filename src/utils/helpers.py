"""Funções auxiliares e utilitários gerais."""

import re
import sys
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class ValidationHelper:
    """Helpers para validação de dados."""

    @staticmethod
    def sanitize_input(input_text: str, max_length: int = 500) -> str:
        """
        Sanitiza entrada do usuário removendo caracteres perigosos.

        Args:
            input_text: Texto a ser sanitizado
            max_length: Tamanho máximo permitido

        Returns:
            Texto sanitizado
        """
        if not input_text:
            return ""

        # Remove caracteres potencialmente perigosos
        sanitized = re.sub(r'[;\'"\\]', '', input_text)

        # Limita o tamanho
        return sanitized[:max_length]

    @staticmethod
    def is_safe_query(query: str) -> bool:
        """
        Verifica se uma query é segura (não contém comandos perigosos).

        Args:
            query: Query a ser verificada

        Returns:
            True se query é segura, False caso contrário
        """
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
            'CREATE', 'TRUNCATE', 'REPLACE', 'EXEC', 'EXECUTE'
        ]

        query_upper = query.upper()
        return not any(keyword in query_upper for keyword in dangerous_keywords)


class FormattingHelper:
    """Helpers para formatação de dados."""

    @staticmethod
    def format_number(number: int) -> str:
        """
        Formata número com separadores de milhares.

        Args:
            number: Número a ser formatado

        Returns:
            Número formatado como string
        """
        return f"{number:,}".replace(',', '.')

    @staticmethod
    def format_percentage(value: float, total: float) -> str:
        """
        Calcula e formata porcentagem.

        Args:
            value: Valor
            total: Total

        Returns:
            Porcentagem formatada
        """
        if total == 0:
            return "0%"

        percentage = (value / total) * 100
        return f"{percentage:.1f}%"

    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """
        Trunca texto se exceder tamanho máximo.

        Args:
            text: Texto a ser truncado
            max_length: Tamanho máximo

        Returns:
            Texto truncado se necessário
        """
        if len(text) <= max_length:
            return text

        return text[:max_length - 3] + "..."


class ErrorHelper:
    """Helpers para tratamento de erros."""

    @staticmethod
    def categorize_error(error: Exception) -> Dict[str, Any]:
        """
        Categoriza erro para melhor tratamento.

        Args:
            error: Exceção capturada

        Returns:
            Dicionário com informações do erro
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Categorizar tipos comuns de erro
        if "connection" in error_message.lower():
            category = "database_connection"
            user_message = "Erro de conexão com o banco de dados"
        elif "syntax" in error_message.lower():
            category = "sql_syntax"
            user_message = "Erro de sintaxe na consulta SQL"
        elif "permission" in error_message.lower():
            category = "permission"
            user_message = "Erro de permissão"
        elif "timeout" in error_message.lower():
            category = "timeout"
            user_message = "Consulta demorou muito para executar"
        else:
            category = "unknown"
            user_message = "Erro desconhecido"

        return {
            "type": error_type,
            "category": category,
            "original_message": error_message,
            "user_message": user_message,
            "timestamp": datetime.now().isoformat()
        }


class SystemHelper:
    """Helpers para operações do sistema."""

    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """
        Verifica se dependências estão disponíveis.

        Returns:
            Dicionário com status das dependências
        """
        dependencies = {}

        try:
            import langchain_ollama
            dependencies['langchain_ollama'] = True
        except ImportError:
            dependencies['langchain_ollama'] = False

        try:
            import langchain_community
            dependencies['langchain_community'] = True
        except ImportError:
            dependencies['langchain_community'] = False

        try:
            import langchain
            dependencies['langchain'] = True
        except ImportError:
            dependencies['langchain'] = False

        try:
            import sqlalchemy
            dependencies['sqlalchemy'] = True
        except ImportError:
            dependencies['sqlalchemy'] = False

        return dependencies

    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """
        Retorna informações do sistema.

        Returns:
            Dicionário com informações do sistema
        """
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "executable": sys.executable
        }


class QueryHelper:
    """Helpers específicos para consultas SQL."""

    @staticmethod
    def extract_table_names(query: str) -> List[str]:
        """
        Extrai nomes de tabelas de uma query SQL.

        Args:
            query: Query SQL

        Returns:
            Lista de nomes de tabelas encontrados
        """
        # Regex simples para encontrar padrões FROM e JOIN
        pattern = r'(?:FROM|JOIN)\s+(\w+)'
        matches = re.findall(pattern, query, re.IGNORECASE)
        return list(set(matches))  # Remove duplicatas

    @staticmethod
    def is_select_query(query: str) -> bool:
        """
        Verifica se query é do tipo SELECT (somente leitura).

        Args:
            query: Query SQL

        Returns:
            True se é SELECT, False caso contrário
        """
        query_trimmed = query.strip().upper()
        return query_trimmed.startswith('SELECT')

    @staticmethod
    def estimate_query_complexity(query: str) -> str:
        """
        Estima complexidade de uma query SQL.

        Args:
            query: Query SQL

        Returns:
            Nível de complexidade: 'simples', 'média', 'complexa'
        """
        query_upper = query.upper()

        # Contar operações complexas
        complex_operations = [
            'JOIN', 'SUBQUERY', 'UNION', 'GROUP BY',
            'ORDER BY', 'HAVING', 'CASE WHEN'
        ]

        complexity_score = sum(
            1 for operation in complex_operations
            if operation in query_upper
        )

        if complexity_score == 0:
            return 'simples'
        elif complexity_score <= 2:
            return 'média'
        else:
            return 'complexa'


class ConfigHelper:
    """Helpers para configuração."""

    @staticmethod
    def validate_config() -> List[str]:
        """
        Valida configuração atual.

        Returns:
            Lista de problemas encontrados (vazia se tudo OK)
        """
        try:
            from config.settings import config

            issues = []

            # Validar configurações do modelo
            if not config.model.name:
                issues.append("Nome do modelo não configurado")

            if config.model.temperature < 0 or config.model.temperature > 1:
                issues.append("Temperature deve estar entre 0 e 1")
            
            # Validar configurações do banco
            if not config.database.uri:
                issues.append("URI do banco de dados não configurada")

            # Validar configurações do agente
            if config.agent.max_iterations <= 0:
                issues.append("Max iterations deve ser maior que 0")

            return issues

        except Exception as e:
            return [f"Erro ao validar configuração: {str(e)}"]