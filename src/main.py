"""Ponto de entrada principal da aplicação."""

import sys
import os

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.interface.cli import CLIInterface
from src.utils.helpers import SystemHelper, ConfigHelper


def check_environment() -> bool:
    """
    Verifica se o ambiente está configurado corretamente.

    Returns:
        True se ambiente está OK, False caso contrário
    """
    print("🔍 Verificando ambiente...")

    # Verificar dependências
    dependencies = SystemHelper.check_dependencies()
    missing_deps = [dep for dep, available in dependencies.items() if not available]

    if missing_deps:
        print("❌ Dependências faltando:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\n💡 Execute: pip install -r requirements.txt")
        return False

    print("✅ Todas as dependências estão disponíveis")

    # Verificar configuração
    config_issues = ConfigHelper.validate_config()

    if config_issues:
        print("⚠️  Problemas de configuração encontrados:")
        for issue in config_issues:
            print(f"   • {issue}")
        print("\n💡 Verifique o arquivo .env ou config/settings.py")
        return False

    print("✅ Configuração válida")
    return True


def main() -> None:
    """Função principal da aplicação."""
    try:
        # Verificar ambiente
        if not check_environment():
            print("\n❌ Ambiente não está configurado corretamente")
            sys.exit(1)

        # Inicializar e executar interface CLI
        cli = CLIInterface()
        cli.run()

    except KeyboardInterrupt:
        print("\n\n⚠️  Aplicação interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro crítico na aplicação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()