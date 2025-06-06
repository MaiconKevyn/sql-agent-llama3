"""Testes para o agente SQL."""

import pytest
from unittest.mock import Mock, patch
from src.core.agent import SQLAgent
from src.core.database import DatabaseManager
from src.utils.helpers import ValidationHelper, QueryHelper


class TestSQLAgent:
    """Testes para a classe SQLAgent."""

    @patch('src.core.agent.DatabaseManager')
    @patch('src.core.agent.OllamaLLM')
    def test_agent_initialization(self, mock_llm, mock_db_manager):
        """Testa inicialização do agente."""
        # Arrange
        mock_db_manager.return_value.get_database.return_value = Mock()

        # Act
        agent = SQLAgent()

        # Assert
        assert agent is not None
        assert agent.db_manager is not None
        assert agent.llm is not None
        assert agent.agent_executor is not None

    def test_process_query_success(self, mock_database):
        """Testa processamento bem-sucedido de query."""
        # Arrange
        with patch('src.core.agent.DatabaseManager') as mock_db_manager:
            mock_db_manager.return_value.get_database.return_value = mock_database

            with patch('src.core.agent.create_sql_agent') as mock_create_agent:
                mock_executor = Mock()
                mock_executor.invoke.return_value = {
                    'output': 'A tabela tem 10 colunas.'
                }
                mock_create_agent.return_value = mock_executor

                agent = SQLAgent()

                # Act
                result = agent.process_query("Quantas colunas tem a tabela?")

                # Assert
                assert result['success'] is True
                assert 'A tabela tem 10 colunas.' in result['response']
                assert result['method'] == 'agent'

    def test_fallback_columns_query(self, mock_database):
        """Testa fallback para consulta de colunas."""
        # Arrange
        with patch('src.core.agent.DatabaseManager') as mock_db_manager:
            mock_db_manager.return_value.get_database.return_value = mock_database
            mock_db_manager.return_value.execute_query.return_value = [(5,)]

            with patch('src.core.agent.create_sql_agent') as mock_create_agent:
                mock_executor = Mock()
                mock_executor.invoke.side_effect = Exception("Agent failed")
                mock_create_agent.return_value = mock_executor

                agent = SQLAgent()

                # Act
                result = agent.process_query("quantas colunas tem a tabela?")

                # Assert
                assert result['success'] is True
                assert 'tem 5 colunas' in result['response']
                assert result['method'] == 'fallback_columns'

    def test_fallback_records_query(self, mock_database):
        """Testa fallback para consulta de registros."""
        # Arrange
        with patch('src.core.agent.DatabaseManager') as mock_db_manager:
            mock_db_manager.return_value.get_database.return_value = mock_database
            mock_db_manager.return_value.execute_query.return_value = [(1000,)]

            with patch('src.core.agent.create_sql_agent') as mock_create_agent:
                mock_executor = Mock()
                mock_executor.invoke.side_effect = Exception("Agent failed")
                mock_create_agent.return_value = mock_executor

                agent = SQLAgent()

                # Act
                result = agent.process_query("quantos registros existem?")

                # Assert
                assert result['success'] is True
                assert 'tem 1,000 registros' in result['response']
                assert result['method'] == 'fallback_records'


class TestDatabaseManager:
    """Testes para a classe DatabaseManager."""

    def test_get_table_info(self, temp_database):
        """Testa obtenção de informações da tabela."""
        # Arrange
        with patch('config.settings.config') as mock_config:
            mock_config.database.uri = f"sqlite:///{temp_database}"
            mock_config.database.sample_rows = 3

            db_manager = DatabaseManager()

            # Act
            table_info = db_manager.get_table_info('dados_sus3')

            # Assert
            assert table_info['name'] == 'dados_sus3'
            assert table_info['record_count'] == 2
            assert isinstance(table_info['columns_count'], int)

    def test_execute_query(self, temp_database):
        """Testa execução de query."""
        # Arrange
        with patch('config.settings.config') as mock_config:
            mock_config.database.uri = f"sqlite:///{temp_database}"
            mock_config.database.sample_rows = 3

            db_manager = DatabaseManager()

            # Act
            result = db_manager.execute_query("SELECT COUNT(*) FROM dados_sus3")

            # Assert
            assert len(result) == 1
            assert result[0][0] == 2


class TestValidationHelper:
    """Testes para helpers de validação."""

    def test_sanitize_input_removes_dangerous_chars(self):
        """Testa remoção de caracteres perigosos."""
        # Arrange
        dangerous_input = "SELECT * FROM table; DROP TABLE users;"

        # Act
        sanitized = ValidationHelper.sanitize_input(dangerous_input)

        # Assert
        assert ";" not in sanitized
        assert "DROP" in sanitized  # Só remove caracteres, não palavras

    def test_sanitize_input_limits_length(self):
        """Testa limitação de tamanho."""
        # Arrange
        long_input = "a" * 1000

        # Act
        sanitized = ValidationHelper.sanitize_input(long_input, max_length=100)

        # Assert
        assert len(sanitized) == 100

    def test_is_safe_query_blocks_dangerous_keywords(self):
        """Testa bloqueio de palavras-chave perigosas."""
        # Arrange
        dangerous_queries = [
            "DROP TABLE users",
            "DELETE FROM table",
            "UPDATE table SET x=1"
        ]

        safe_queries = [
            "SELECT * FROM table",
            "SELECT COUNT(*) FROM users"
        ]

        # Act & Assert
        for query in dangerous_queries:
            assert ValidationHelper.is_safe_query(query) is False

        for query in safe_queries:
            assert ValidationHelper.is_safe_query(query) is True


class TestQueryHelper:
    """Testes para helpers de query."""

    def test_extract_table_names(self):
        """Testa extração de nomes de tabelas."""
        # Arrange
        query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"

        # Act
        tables = QueryHelper.extract_table_names(query)

        # Assert
        assert 'users' in tables
        assert 'orders' in tables
        assert len(tables) == 2

    def test_is_select_query(self):
        """Testa identificação de queries SELECT."""
        # Arrange
        select_queries = [
            "SELECT * FROM table",
            "  select id from users",
            "SELECT COUNT(*) FROM data"
        ]

        non_select_queries = [
            "INSERT INTO table VALUES (1)",
            "UPDATE table SET x=1",
            "DELETE FROM table"
        ]

        # Act & Assert
        for query in select_queries:
            assert QueryHelper.is_select_query(query) is True

        for query in non_select_queries:
            assert QueryHelper.is_select_query(query) is False

    def test_estimate_query_complexity(self):
        """Testa estimativa de complexidade de query."""
        # Arrange
        simple_query = "SELECT * FROM table"
        medium_query = "SELECT * FROM table ORDER BY id"
        complex_query = "SELECT u.name, COUNT(o.id) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id HAVING COUNT(o.id) > 5"

        # Act & Assert
        assert QueryHelper.estimate_query_complexity(simple_query) == 'simples'
        assert QueryHelper.estimate_query_complexity(medium_query) == 'média'
        assert QueryHelper.estimate_query_complexity(complex_query) == 'complexa'