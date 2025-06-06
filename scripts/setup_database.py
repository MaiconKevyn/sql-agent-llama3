#!/usr/bin/env python3
"""Script para criação da base de dados a partir de arquivos CSV."""

import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from typing import Optional, Dict, Any
import argparse
from datetime import datetime

# Adicionar o diretório raiz ao path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.helpers import FormattingHelper, ErrorHelper


class DatabaseSetup:
    """Classe para configuração e criação da base de dados."""

    def __init__(self):
        """Inicializa o configurador de base de dados."""
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.db_dir = self.project_root / "database"
        self.logs_dir = self.project_root / "logs"

        # Criar diretórios se não existirem
        self._create_directories()

    def _create_directories(self) -> None:
        """Cria diretórios necessários."""
        for directory in [self.data_dir, self.db_dir, self.logs_dir]:
            directory.mkdir(exist_ok=True)

    def _log_operation(self, message: str, level: str = "INFO") -> None:
        """Registra operação em log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}"

        # Imprimir no console
        if level == "ERROR":
            print(f"❌ {message}")
        elif level == "WARNING":
            print(f"⚠️  {message}")
        elif level == "SUCCESS":
            print(f"✅ {message}")
        else:
            print(f"ℹ️  {message}")

        # Salvar em arquivo de log
        log_file = self.logs_dir / f"database_setup_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")

    def validate_csv_file(self, csv_path: Path) -> Dict[str, Any]:
        """
        Valida arquivo CSV e retorna informações sobre ele.

        Args:
            csv_path: Caminho para o arquivo CSV

        Returns:
            Dict com informações do arquivo e status de validação
        """
        validation_result = {
            "is_valid": False,
            "file_exists": False,
            "file_size": 0,
            "rows_count": 0,
            "columns_count": 0,
            "columns": [],
            "encoding": "utf-8",
            "errors": []
        }

        # Verificar se arquivo existe
        if not csv_path.exists():
            validation_result["errors"].append(f"Arquivo não encontrado: {csv_path}")
            return validation_result

        validation_result["file_exists"] = True
        validation_result["file_size"] = csv_path.stat().st_size

        # Tentar diferentes encodings
        encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
        df = None

        for encoding in encodings:
            try:
                # Ler apenas algumas linhas para validação inicial
                df = pd.read_csv(csv_path, encoding=encoding, nrows=5)
                validation_result["encoding"] = encoding
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                validation_result["errors"].append(f"Erro ao ler arquivo: {str(e)}")
                return validation_result

        if df is None:
            validation_result["errors"].append("Não foi possível ler o arquivo com nenhum encoding testado")
            return validation_result

        # Ler arquivo completo
        try:
            df_full = pd.read_csv(csv_path, encoding=validation_result["encoding"])
            validation_result["rows_count"] = len(df_full)
            validation_result["columns_count"] = len(df_full.columns)
            validation_result["columns"] = df_full.columns.tolist()
            validation_result["is_valid"] = True

        except Exception as e:
            validation_result["errors"].append(f"Erro ao ler arquivo completo: {str(e)}")

        return validation_result

    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa nomes das colunas para compatibilidade com SQL.

        Args:
            df: DataFrame original

        Returns:
            DataFrame com colunas renomeadas
        """
        # Backup das colunas originais
        original_columns = df.columns.tolist()

        # Limpar nomes das colunas
        cleaned_columns = []
        for col in df.columns:
            # Remover espaços e caracteres especiais
            clean_col = col.strip()
            clean_col = clean_col.replace(" ", "_")
            clean_col = clean_col.replace("-", "_")
            clean_col = clean_col.replace("(", "")
            clean_col = clean_col.replace(")", "")
            clean_col = clean_col.replace("/", "_")
            clean_col = clean_col.replace("\\", "_")
            clean_col = clean_col.replace(".", "_")
            clean_col = clean_col.upper()

            # Garantir que não comece com número
            if clean_col[0].isdigit():
                clean_col = f"COL_{clean_col}"

            cleaned_columns.append(clean_col)

        # Aplicar novos nomes
        df.columns = cleaned_columns

        # Log das mudanças
        changes = []
        for orig, clean in zip(original_columns, cleaned_columns):
            if orig != clean:
                changes.append(f"'{orig}' → '{clean}'")

        if changes:
            self._log_operation(f"Colunas renomeadas: {', '.join(changes[:5])}" +
                                (f" (e mais {len(changes) - 5})" if len(changes) > 5 else ""))

        return df

    def create_database_from_csv(
            self,
            csv_path: str,
            db_name: str = "sus_data.db",
            table_name: Optional[str] = None,
            clean_columns: bool = True,
            chunk_size: int = 10000
    ) -> bool:
        """
        Cria banco de dados SQLite a partir de arquivo CSV.

        Args:
            csv_path: Caminho para arquivo CSV
            db_name: Nome do arquivo de banco de dados
            table_name: Nome da tabela (se None, será inferido do arquivo)
            clean_columns: Se deve limpar nomes das colunas
            chunk_size: Tamanho do chunk para processamento

        Returns:
            True se criação foi bem-sucedida, False caso contrário
        """
        csv_file = Path(csv_path)

        self._log_operation(f"Iniciando criação de banco de dados a partir de: {csv_file.absolute()}")

        # Validar arquivo CSV
        validation = self.validate_csv_file(csv_file)

        if not validation["is_valid"]:
            for error in validation["errors"]:
                self._log_operation(error, "ERROR")
            return False

        # Mostrar informações do arquivo
        file_size_mb = validation["file_size"] / (1024 * 1024)
        self._log_operation(f"Arquivo: {csv_file.name}")
        self._log_operation(f"Tamanho: {file_size_mb:.2f} MB")
        self._log_operation(f"Linhas: {FormattingHelper.format_number(validation['rows_count'])}")
        self._log_operation(f"Colunas: {validation['columns_count']}")
        self._log_operation(f"Encoding: {validation['encoding']}")

        # Definir nome da tabela
        if table_name is None:
            table_name = csv_file.stem.replace('-', '_').replace(' ', '_')

        # Caminho do banco de dados
        db_path = self.db_dir / db_name
        engine = create_engine(f"sqlite:///{db_path}")

        try:
            # Processar arquivo em chunks se for muito grande
            if validation["rows_count"] > chunk_size:
                self._log_operation(
                    f"Processando arquivo em chunks de {FormattingHelper.format_number(chunk_size)} linhas...")

                chunk_count = 0
                total_rows_processed = 0

                for chunk in pd.read_csv(
                        csv_file,
                        encoding=validation["encoding"],
                        chunksize=chunk_size
                ):
                    chunk_count += 1

                    if clean_columns and chunk_count == 1:
                        chunk = self.clean_column_names(chunk)
                    elif clean_columns:
                        # Aplicar os mesmos nomes de colunas do primeiro chunk
                        chunk.columns = [
                            col.strip().replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "").replace(
                                "/", "_").replace("\\", "_").replace(".", "_").upper() for col in chunk.columns]
                        for i, col in enumerate(chunk.columns):
                            if col[0].isdigit():
                                chunk.columns[i] = f"COL_{col}"

                    # Salvar chunk
                    if_exists_mode = 'replace' if chunk_count == 1 else 'append'
                    chunk.to_sql(table_name, engine, if_exists=if_exists_mode, index=False)

                    total_rows_processed += len(chunk)
                    self._log_operation(
                        f"Chunk {chunk_count} processado - {FormattingHelper.format_number(total_rows_processed)} linhas totais")

            else:
                # Processar arquivo inteiro
                self._log_operation("Carregando arquivo completo...")
                df = pd.read_csv(csv_file, encoding=validation["encoding"])

                if clean_columns:
                    df = self.clean_column_names(df)

                # Salvar no banco
                self._log_operation("Salvando dados no banco...")
                df.to_sql(table_name, engine, if_exists='replace', index=False)

            # Verificar se dados foram inseridos corretamente
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()

                # Verificar estrutura da tabela
                columns_result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns_info = columns_result.fetchall()

            self._log_operation(f"Base de dados criada com sucesso!", "SUCCESS")
            self._log_operation(f"Arquivo de banco: {db_path.absolute()}", "SUCCESS")
            self._log_operation(f"Tabela: {table_name}", "SUCCESS")
            self._log_operation(f"Registros inseridos: {FormattingHelper.format_number(row_count)}", "SUCCESS")
            self._log_operation(f"Colunas criadas: {len(columns_info)}", "SUCCESS")

            # Mostrar algumas colunas como exemplo
            column_names = [col[1] for col in columns_info[:5]]
            self._log_operation(f"Primeiras colunas: {', '.join(column_names)}" +
                                (f" (e mais {len(columns_info) - 5})" if len(columns_info) > 5 else ""))

            return True

        except Exception as e:
            error_info = ErrorHelper.categorize_error(e)
            self._log_operation(f"Erro ao criar banco de dados: {error_info['user_message']}", "ERROR")
            self._log_operation(f"Detalhes técnicos: {error_info['original_message']}", "ERROR")
            return False

    def list_available_csvs(self) -> None:
        """Lista arquivos CSV disponíveis no diretório de dados."""
        csv_files = list(self.data_dir.glob("*.csv"))

        if not csv_files:
            print(f"❌ Nenhum arquivo CSV encontrado em: {self.data_dir.absolute()}")
            print("💡 Coloque seus arquivos CSV no diretório 'data/'")
            return

        print(f"\n📁 Arquivos CSV disponíveis em {self.data_dir.absolute()}:")
        print("=" * 70)

        for i, csv_file in enumerate(csv_files, 1):
            file_size = csv_file.stat().st_size / (1024 * 1024)  # MB
            print(f"{i:2d}. {csv_file.name}")
            print(f"     📊 Tamanho: {file_size:.2f} MB")
            print(f"     📍 Path: {csv_file.absolute()}")
            print()


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Cria base de dados SQLite a partir de arquivos CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Listar CSVs disponíveis
  python scripts/setup_database.py --list

  # Criar base com CSV específico
  python scripts/setup_database.py --csv data/dados_sus3.csv

  # Criar base com nome customizado
  python scripts/setup_database.py --csv data/dados_sus3.csv --db minha_base.db --table meus_dados

  # Modo interativo
  python scripts/setup_database.py
        """
    )

    parser.add_argument(
        "--csv",
        type=str,
        help="Caminho para o arquivo CSV"
    )

    parser.add_argument(
        "--db",
        type=str,
        default="sus_data.db",
        help="Nome do arquivo de banco de dados (padrão: sus_data.db)"
    )

    parser.add_argument(
        "--table",
        type=str,
        help="Nome da tabela (se não especificado, será inferido do nome do arquivo)"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista arquivos CSV disponíveis"
    )

    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Não limpar nomes das colunas"
    )

    args = parser.parse_args()

    # Inicializar configurador
    db_setup = DatabaseSetup()

    # Mostrar banner
    print("🗄️  CONFIGURADOR DE BASE DE DADOS")
    print("=" * 50)

    # Listar CSVs se solicitado
    if args.list:
        db_setup.list_available_csvs()
        return

    # Modo interativo se nenhum CSV especificado
    if not args.csv:
        print("📁 Modo interativo ativado")
        db_setup.list_available_csvs()

        # Solicitar entrada do usuário
        csv_input = input("\n🗣️  Digite o caminho do arquivo CSV (ou pressione Enter para cancelar): ").strip()

        if not csv_input:
            print("❌ Operação cancelada")
            return

        args.csv = csv_input

    # Criar base de dados
    success = db_setup.create_database_from_csv(
        csv_path=args.csv,
        db_name=args.db,
        table_name=args.table,
        clean_columns=not args.no_clean
    )

    if success:
        print("\n🎉 Base de dados criada com sucesso!")
        print("💡 Agora você pode executar: python -m src.main")
    else:
        print("\n❌ Falha ao criar base de dados")
        sys.exit(1)


if __name__ == "__main__":
    main()