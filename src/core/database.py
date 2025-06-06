"""Gerenciamento de conexão e operações com banco de dados."""

from typing import Dict, Any, List, Tuple, Optional
from langchain_community.utilities import SQLDatabase
from config.settings import config


class DatabaseManager:
    """Gerencia conexão e operações com o banco de dados."""

    def __init__(self):
        """Inicializa o gerenciador de banco de dados."""
        self.db: Optional[SQLDatabase] = None
        self._connect()

    def _connect(self) -> None:
        """Estabelece conexão com o banco de dados."""
        try:
            self.db = SQLDatabase.from_uri(
                config.database.uri,
                sample_rows_in_table_info=config.database.sample_rows
            )
        except Exception as e:
            raise ConnectionError(f"Erro ao conectar com banco de dados: {e}")

    def get_database(self) -> SQLDatabase:
        """Retorna instância do banco de dados."""
        if self.db is None:
            raise RuntimeError("Banco de dados não conectado")
        return self.db

    def get_table_names(self) -> List[str]:
        """Retorna lista de tabelas disponíveis."""
        return self.db.get_usable_table_names()

    def execute_query(self, query: str) -> List[Tuple]:
        """Executa uma query SQL e retorna os resultados."""
        try:
            return self.db.run(query)
        except Exception as e:
            raise RuntimeError(f"Erro ao executar query: {e}")

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Retorna informações sobre uma tabela específica."""
        try:
            # Contar registros
            count_query = f"SELECT COUNT(*) FROM {table_name};"
            record_count = self.execute_query(count_query)[0][0]

            # Contar colunas
            columns_query = f"SELECT COUNT(*) FROM pragma_table_info('{table_name}');"
            columns_count = self.execute_query(columns_query)[0][0]

            return {
                "name": table_name,
                "record_count": record_count,
                "columns_count": columns_count
            }
        except Exception as e:
            return {
                "name": table_name,
                "record_count": "N/A",
                "columns_count": "N/A",
                "error": str(e)
            }

    def get_database_summary(self) -> Dict[str, Any]:
        """Retorna resumo completo do banco de dados."""
        tables = self.get_table_names()
        summary = {
            "tables": [],
            "total_tables": len(tables)
        }

        for table in tables:
            table_info = self.get_table_info(table)
            summary["tables"].append(table_info)

        return summary

    def get_schema_info(self) -> str:
        """Retorna informações de schema do banco."""
        return self.db.table_info if self.db else "Schema não disponível"