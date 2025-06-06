"""Configurações compartilhadas para testes."""

import pytest
import tempfile
import os
from unittest.mock import Mock
from src.core.database import DatabaseManager
from src.core.agent import SQLAgent


@pytest.fixture
def mock_database():
    """Fixture para mock do banco de dados."""
    mock_db = Mock()
    mock_db.get_usable_table_names.return_value = ['dados_sus3']
    mock_db.run.return_value = [(100,)]  # Mock result
    mock_db.table_info = "Mocked table info"
    return mock_db


@pytest.fixture
def temp_database():
    """Fixture para banco de dados temporário."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name

    # Criar banco temporário básico
    import sqlite3
    conn = sqlite3.connect(temp_db_path)
    conn.execute('''
                 CREATE TABLE dados_sus3
                 (
                     id                         INTEGER PRIMARY KEY,
                     idade                      INTEGER,
                     uf_residencia_paciente     TEXT,
                     cidade_residencia_paciente TEXT
                 )
                 ''')
    conn.execute('''
                 INSERT INTO dados_sus3 (idade, uf_residencia_paciente, cidade_residencia_paciente)
                 VALUES (25, 'RS', 'Porto Alegre'),
                        (30, 'SP', 'São Paulo')
                 ''')
    conn.commit()
    conn.close()

    yield temp_db_path

    # Cleanup
    os.unlink(temp_db_path)


@pytest.fixture
def mock_llm():
    """Fixture para mock do LLM."""
    mock = Mock()
    mock.invoke.return_value = "Mocked LLM response"
    return mock


@pytest.fixture
def sample_queries():
    """Fixture com queries de exemplo para teste."""
    return [
        "Quantas colunas tem a tabela?",
        "Quantos registros existem?",
        "Qual a idade média dos pacientes?",
        "Quantos estados diferentes temos?"
    ]