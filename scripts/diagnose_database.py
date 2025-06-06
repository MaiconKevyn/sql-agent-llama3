#!/usr/bin/env python3
"""
Script completo para diagnosticar problemas no banco de dados.
Localização: scripts/diagnose_database.py
"""

import os
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Any


def diagnose_database():
    """Diagnostica problemas comuns no banco de dados."""

    print("🔍 DIAGNÓSTICO DO BANCO DE DADOS")
    print("=" * 50)

    # Verificar arquivo de banco
    db_paths = [
        "database/sus_data.db",
        "sus_data.db",
        "data/sus_data.db",
        "./database/sus_data.db",
        "../database/sus_data.db"
    ]

    db_found = None
    for db_path in db_paths:
        if os.path.exists(db_path):
            db_found = db_path
            break

    if not db_found:
        print("❌ PROBLEMA: Arquivo de banco de dados não encontrado!")
        print("\n💡 SOLUÇÕES:")
        print("1. Criar banco de dados:")
        print("   python scripts/setup_database.py --csv data/dados_sus3.csv")
        print("\n2. Verificar se CSV existe:")
        print("   ls -la data/")
        print("\n3. Listar CSVs disponíveis:")
        print("   python scripts/setup_database.py --list")
        return

    print(f"✅ Banco encontrado: {db_found}")
    file_size = os.path.getsize(db_found) / (1024 * 1024)  # MB
    print(f"📊 Tamanho do arquivo: {file_size:.2f} MB")

    # Conectar e verificar tabelas
    try:
        conn = sqlite3.connect(db_found)
        cursor = conn.cursor()

        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("❌ PROBLEMA: Banco existe mas não tem tabelas!")
            print("\n💡 SOLUÇÃO:")
            print("   Recriar banco: python scripts/setup_database.py --csv data/dados_sus3.csv")
        else:
            print(f"\n📊 Tabelas encontradas ({len(tables)}):")

            total_records = 0
            for table in tables:
                table_name = table[0]
                print(f"\n   🏥 Tabela: {table_name}")

                # Contar registros
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
                    count = cursor.fetchone()[0]
                    total_records += count
                    print(f"      📊 Registros: {count:,}")

                    # Verificar estrutura
                    cursor.execute(f"PRAGMA table_info(`{table_name}`);")
                    columns = cursor.fetchall()
                    print(f"      📋 Colunas: {len(columns)}")

                    # Mostrar algumas colunas importantes
                    important_columns = ['MORTE', 'CID_MORTE', 'SEXO', 'IDADE', 'UF_RESIDENCIA_PACIENTE']
                    found_columns = []

                    for col in columns:
                        col_name = col[1]  # Nome da coluna
                        if col_name in important_columns:
                            found_columns.append(col_name)

                    if found_columns:
                        print(f"      ✅ Colunas importantes: {', '.join(found_columns)}")

                    # Verificar dados de amostra se a tabela contém dados SUS
                    if any(col in table_name.upper() for col in ['SUS', 'DADOS']):
                        print(f"      🔍 Verificando dados de amostra...")

                        # Verificar mortalidade
                        if 'MORTE' in [col[1] for col in columns]:
                            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE MORTE = 1;")
                            deaths = cursor.fetchone()[0]
                            print(f"         💀 Mortes (MORTE=1): {deaths:,}")

                            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE CID_MORTE > 0;")
                            cid_deaths = cursor.fetchone()[0]
                            print(f"         🏷️  Com CID da morte: {cid_deaths:,}")

                            if deaths != cid_deaths:
                                print(
                                    f"         ⚠️  ATENÇÃO: Diferença entre MORTE=1 ({deaths}) e CID_MORTE>0 ({cid_deaths})")
                                print(f"         💡 Use MORTE=1 para contar mortes, não CID_MORTE>0")

                        # Verificar sexo
                        if 'SEXO' in [col[1] for col in columns]:
                            cursor.execute(f"SELECT SEXO, COUNT(*) FROM `{table_name}` GROUP BY SEXO ORDER BY SEXO;")
                            sexo_counts = cursor.fetchall()
                            print(f"         👥 Distribuição por sexo:")
                            for sexo, count in sexo_counts:
                                if sexo == 1:
                                    print(f"            Masculino (1): {count:,}")
                                elif sexo == 3:
                                    print(f"            Feminino (3): {count:,}")
                                else:
                                    print(f"            Outros/Inválido ({sexo}): {count:,}")

                        # Verificar estados
                        if 'UF_RESIDENCIA_PACIENTE' in [col[1] for col in columns]:
                            cursor.execute(f"SELECT COUNT(DISTINCT UF_RESIDENCIA_PACIENTE) FROM `{table_name}`;")
                            estados_count = cursor.fetchone()[0]
                            print(f"         🗺️  Estados diferentes: {estados_count}")

                            # Top 3 estados
                            cursor.execute(f"""
                                SELECT UF_RESIDENCIA_PACIENTE, COUNT(*) 
                                FROM `{table_name}` 
                                GROUP BY UF_RESIDENCIA_PACIENTE 
                                ORDER BY COUNT(*) DESC 
                                LIMIT 3
                            """)
                            top_states = cursor.fetchall()
                            print(f"         🥇 Top 3 estados:")
                            for uf, count in top_states:
                                print(f"            {uf}: {count:,}")

                except Exception as e:
                    print(f"      ❌ Erro ao analisar tabela: {e}")

            print(f"\n📈 Total de registros no banco: {total_records:,}")

        # Verificar se tabela específica 'dados_sus3' existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dados_sus3';")
        sus_table = cursor.fetchone()

        if not sus_table:
            print("\n⚠️  PROBLEMA ESPECÍFICO:")
            print("   Tabela 'dados_sus3' não encontrada!")

            if tables:
                print(f"\n💡 SOLUÇÃO RÁPIDA:")
                actual_table = tables[0][0]
                print(f"   Tabela disponível: '{actual_table}'")
                print(f"   OPÇÕES:")
                print(f"   1. Renomear tabela: ALTER TABLE `{actual_table}` RENAME TO dados_sus3;")
                print(f"   2. Atualizar código para usar: '{actual_table}'")
                print(f"   3. Recriar banco com nome correto")
        else:
            print("\n✅ Tabela 'dados_sus3' encontrada e é válida!")

        conn.close()

    except Exception as e:
        print(f"❌ Erro ao acessar banco: {e}")
        print("\n💡 SOLUÇÃO:")
        print("   Recriar banco: python scripts/setup_database.py --csv data/dados_sus3.csv")


def check_csv_files():
    """Verifica arquivos CSV disponíveis."""

    print(f"\n📁 VERIFICANDO ARQUIVOS CSV")
    print("=" * 50)

    data_dirs = ["data", ".", "../data"]
    csv_found = False

    for data_dir in data_dirs:
        data_path = Path(data_dir)
        if data_path.exists():
            csv_files = list(data_path.glob("*.csv"))

            if csv_files:
                csv_found = True
                print(f"✅ Arquivos CSV encontrados em '{data_dir}' ({len(csv_files)}):")

                for csv_file in csv_files:
                    size_mb = csv_file.stat().st_size / (1024 * 1024)
                    print(f"   📄 {csv_file.name} ({size_mb:.1f} MB)")

                    # Verificar se é arquivo SUS
                    if any(keyword in csv_file.name.lower() for keyword in ['sus', 'dados', 'sih']):
                        print(f"      🏥 Parece ser arquivo do SUS")

                        # Tentar ler header
                        try:
                            with open(csv_file, 'r', encoding='utf-8') as f:
                                header = f.readline().strip()
                                columns = header.split(',')
                                print(f"      📋 Colunas detectadas: {len(columns)}")

                                # Verificar colunas importantes
                                important_cols = []
                                for col in ['MORTE', 'CID_MORTE', 'SEXO', 'IDADE']:
                                    if col in header.upper():
                                        important_cols.append(col)

                                if important_cols:
                                    print(f"      ✅ Colunas SUS encontradas: {', '.join(important_cols)}")
                                else:
                                    print(f"      ⚠️  Não parecem ser dados SUS padrão")

                        except Exception as e:
                            print(f"      ❌ Erro ao ler arquivo: {e}")
                break

    if not csv_found:
        print("❌ Nenhum arquivo CSV encontrado!")
        print("💡 SOLUÇÕES:")
        print("   1. Criar diretório: mkdir data")
        print("   2. Colocar arquivos CSV na pasta 'data/'")
        print("   3. Baixar dados do DATASUS")


def check_configuration():
    """Verifica configuração."""

    print(f"\n⚙️  VERIFICANDO CONFIGURAÇÃO")
    print("=" * 50)

    # Verificar .env
    env_files = [".env", "../.env", ".env.example"]
    env_found = False

    for env_file in env_files:
        if os.path.exists(env_file):
            env_found = True
            print(f"✅ Arquivo de configuração: {env_file}")

            # Ler algumas configurações importantes
            try:
                with open(env_file, 'r') as f:
                    content = f.read()

                    important_vars = ['MODEL_NAME', 'DATABASE_URI', 'DEBUG_MODE']
                    for var in important_vars:
                        if var in content:
                            # Extrair valor
                            for line in content.split('\n'):
                                if line.startswith(f"{var}="):
                                    value = line.split('=', 1)[1].strip()
                                    print(f"   {var}: {value}")
                                    break
                        else:
                            print(f"   ⚠️  {var}: não encontrado")

            except Exception as e:
                print(f"   ❌ Erro ao ler {env_file}: {e}")
            break

    if not env_found:
        print("⚠️  Nenhum arquivo .env encontrado")
        print("💡 SOLUÇÃO:")
        print("   1. Copiar: cp .env.example .env")
        print("   2. Editar configurações conforme necessário")

    # Verificar se consegue importar configuração
    try:
        # Tentar adicionar ao path
        current_dir = os.getcwd()
        possible_paths = [current_dir, os.path.join(current_dir, '..'), '.']

        for path in possible_paths:
            config_path = os.path.join(path, 'config', 'settings.py')
            if os.path.exists(config_path):
                sys.path.insert(0, path)
                break

        from config.settings import config

        print(f"\n✅ Configuração carregada com sucesso:")
        print(f"   🤖 Modelo: {config.model.name}")
        print(f"   🗄️  Database URI: {config.database.uri}")
        print(f"   📊 Sample rows: {config.database.sample_rows}")
        print(f"   🌡️  Temperature: {config.model.temperature}")
        print(f"   🔄 Max iterations: {config.agent.max_iterations}")

    except Exception as e:
        print(f"❌ Erro ao carregar configuração: {e}")
        print("💡 SOLUÇÕES:")
        print("   1. Verificar se config/settings.py existe")
        print("   2. Verificar dependências: pip install -r requirements.txt")
        print("   3. Verificar sintaxe do arquivo de configuração")


def check_dependencies():
    """Verifica dependências do projeto."""

    print(f"\n📦 VERIFICANDO DEPENDÊNCIAS")
    print("=" * 50)

    required_packages = [
        'langchain_ollama',
        'langchain_community',
        'langchain',
        'sqlalchemy',
        'pandas',
        'python-dotenv'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - FALTANDO")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️  Pacotes faltando: {len(missing_packages)}")
        print("💡 SOLUÇÃO:")
        print(f"   pip install {' '.join(missing_packages)}")
    else:
        print(f"\n✅ Todas as dependências estão instaladas!")


def check_ollama():
    """Verifica se Ollama está funcionando."""

    print(f"\n🤖 VERIFICANDO OLLAMA")
    print("=" * 50)

    # Verificar se ollama está no PATH
    ollama_cmd = "ollama list"

    try:
        import subprocess
        result = subprocess.run(ollama_cmd.split(), capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✅ Ollama está funcionando")

            # Verificar modelos disponíveis
            models = result.stdout.strip()
            if models:
                print("🤖 Modelos disponíveis:")
                for line in models.split('\n')[1:]:  # Skip header
                    if line.strip():
                        model_name = line.split()[0]
                        print(f"   • {model_name}")

                # Verificar se llama3 está disponível
                if 'llama3' in models:
                    print("✅ Modelo llama3 encontrado")
                else:
                    print("⚠️  Modelo llama3 não encontrado")
                    print("💡 SOLUÇÃO:")
                    print("   ollama pull llama3")
            else:
                print("⚠️  Nenhum modelo instalado")
                print("💡 SOLUÇÃO:")
                print("   ollama pull llama3")

        else:
            print("❌ Ollama não está funcionando")
            print("💡 SOLUÇÕES:")
            print("   1. Instalar Ollama: https://ollama.ai/")
            print("   2. Iniciar serviço: ollama serve")

    except subprocess.TimeoutExpired:
        print("❌ Timeout ao verificar Ollama")
    except FileNotFoundError:
        print("❌ Ollama não encontrado no PATH")
        print("💡 SOLUÇÃO:")
        print("   Instalar Ollama: https://ollama.ai/")
    except Exception as e:
        print(f"❌ Erro ao verificar Ollama: {e}")


def test_connection():
    """Testa conexão completa do sistema."""

    print(f"\n🧪 TESTE DE CONEXÃO COMPLETA")
    print("=" * 50)

    try:
        # Adicionar ao path se necessário
        current_dir = os.getcwd()
        if 'scripts' in current_dir:
            parent_dir = os.path.dirname(current_dir)
            sys.path.insert(0, parent_dir)
        else:
            sys.path.insert(0, current_dir)

        print("1. Testando import da configuração...")
        from config.settings import config
        print("   ✅ Configuração importada")

        print("2. Testando conexão com banco...")
        from src.core.database import DatabaseManager
        db_manager = DatabaseManager()
        tables = db_manager.get_table_names()
        print(f"   ✅ Banco conectado - {len(tables)} tabela(s)")

        print("3. Testando query simples...")
        if 'dados_sus3' in tables:
            result = db_manager.execute_query("SELECT COUNT(*) FROM dados_sus3 LIMIT 1;")
            count = result[0][0] if result else 0
            print(f"   ✅ Query executada - {count} registros")
        else:
            print(f"   ⚠️  Tabela dados_sus3 não encontrada, mas conexão OK")

        print("4. Testando agente SQL...")
        from src.core.agent import SQLAgent
        agent = SQLAgent()
        print("   ✅ Agente inicializado")

        print("\n🎉 TESTE COMPLETO: SISTEMA FUNCIONANDO!")

    except Exception as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        print("💡 Verifique os problemas identificados acima")


def main():
    """Função principal do diagnóstico."""

    print("🚀 DIAGNÓSTICO COMPLETO DO SISTEMA")
    print("=" * 70)

    # Executar todos os diagnósticos
    check_csv_files()
    diagnose_database()
    check_configuration()
    check_dependencies()
    check_ollama()
    test_connection()

    print(f"\n🎯 RESUMO DE AÇÕES RECOMENDADAS:")
    print("=" * 70)
    print("1. Se não há CSV: Coloque arquivos CSV na pasta 'data/'")
    print("2. Se não há banco: python scripts/setup_database.py --csv data/seu_arquivo.csv")
    print("3. Se erro de config: cp .env.example .env e edite conforme necessário")
    print("4. Se dependências faltando: pip install -r requirements.txt")
    print("5. Se Ollama com problema: ollama serve && ollama pull llama3")
    print("6. Teste final: python -m src.main")

    print(f"\n💡 COMANDOS ÚTEIS:")
    print("   python scripts/setup_database.py --list    # Ver CSVs disponíveis")
    print("   python -m src.main                         # Iniciar agente")
    print("   /debug on                                  # Ativar modo debug")
    print("   /status                                    # Ver status do sistema")


if __name__ == "__main__":
    main()