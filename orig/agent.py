from langchain_ollama import OllamaLLM
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents import AgentType
from langchain_community.utilities import SQLDatabase
from langchain.prompts import PromptTemplate
from langchain.agents.agent import AgentExecutor
from langchain.agents.mrkl.base import ZeroShotAgent
from langchain.chains.llm import LLMChain
import sys
import os


def limpar_terminal():
    """Limpa o terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')


def mostrar_banner():
    """Mostra o banner inicial do programa"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 AGENTE SQL INTERATIVO                  ║
║                    🇧🇷 Respostas em Português               ║
║                                                              ║
║  Faça perguntas sobre o banco de dados em linguagem natural ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def criar_prompt_personalizado():
    """Cria um prompts personalizado em português brasileiro"""

    template = """
Você é um assistente especialista em SQL que SEMPRE responde em português brasileiro.

INSTRUÇÕES IMPORTANTES:
- SEMPRE responda em português brasileiro (pt-BR)
- Seja claro, educado e direto nas respostas
- Use terminologia técnica adequada em português
- Quando perguntado sobre "colunas", use: SELECT COUNT(*) FROM pragma_table_info('nome_tabela')
- Quando perguntado sobre "registros" ou "linhas", use: SELECT COUNT(*) FROM nome_tabela
- Forneça explicações breves e úteis junto com os resultados

CONTEXTO DO BANCO DE DADOS:
Você tem acesso a um banco de dados SQLite com dados do SUS (Sistema Único de Saúde) brasileiro.
A tabela principal é 'dados_sus3' que contém informações sobre internações hospitalares.

FERRAMENTAS DISPONÍVEIS:
{tools}

FORMATO DE RESPOSTA:
Use exatamente este formato:

Pergunta: a pergunta de entrada aqui
Pensamento: eu devo descobrir como responder esta pergunta
Ação: a ação a ser tomada, deve ser uma das [{tool_names}]
Entrada da Ação: a entrada para a ação
Observação: o resultado da ação
... (este Pensamento/Ação/Entrada da Ação/Observação pode repetir N vezes)
Pensamento: eu agora sei a resposta final
Resposta Final: a resposta final em português brasileiro

PERGUNTA: {input}
{agent_scratchpad}
"""

    return PromptTemplate(
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
        template=template
    )


def criar_dicionario_colunas():
    """Cria um dicionário com descrições semânticas das colunas"""

    return {
        "DIAG_PRINC": "Diagnóstico principal do paciente (código CID-10)",
        "MUNIC_RES": "Código do município de residência do paciente",
        "MUNIC_MOV": "Código do município onde ocorreu a internação",
        "PROC_REA": "Código do procedimento realizado durante a internação",
        "IDADE": "Idade do paciente em anos",
        "SEXO": "Sexo do paciente (1=Masculino, 2=Feminino, 3=Não informado)",
        "CID_MORTE": "Código CID-10 da CAUSA da morte (quando aplicável) - NÃO indica se morreu",
        "MORTE": "Indicador de óbito (0=Não morreu, 1=Morreu) - USAR ESTA COLUNA para verificar mortes",
        "CNES": "Código Nacional de Estabelecimento de Saúde",
        "VAL_TOT": "Valor total gasto na internação em reais",
        "UTI_MES_TO": "Quantidade de dias em UTI",
        "DT_INTER": "Data de internação (formato YYYYMMDD)",
        "DT_SAIDA": "Data de saída/alta (formato YYYYMMDD)",
        "total_ocorrencias": "Total de ocorrências similares",
        "UF_RESIDENCIA_PACIENTE": "Estado (UF) de residência do paciente",
        "CIDADE_RESIDENCIA_PACIENTE": "Cidade de residência do paciente",
        "LATI_CIDADE_RES": "Latitude da cidade de residência",
        "LONG_CIDADE_RES": "Longitude da cidade de residência"
    }


def gerar_contexto_colunas():
    """Gera contexto detalhado sobre as colunas para a LLM"""

    dicionario = criar_dicionario_colunas()

    contexto = """
IMPORTANTE - DESCRIÇÃO DETALHADA DAS COLUNAS:

📊 INFORMAÇÕES DEMOGRÁFICAS:
- IDADE: Idade do paciente em anos
- SEXO: Sexo (1=Masculino, 2=Feminino, 3=Não informado)
- UF_RESIDENCIA_PACIENTE: Estado onde o paciente reside
- CIDADE_RESIDENCIA_PACIENTE: Cidade onde o paciente reside

🏥 INFORMAÇÕES MÉDICAS:
- DIAG_PRINC: Diagnóstico principal (código CID-10)
- PROC_REA: Procedimento realizado (código)
- CID_MORTE: Código da CAUSA da morte (só preenchido se morreu)
- MORTE: Indicador se o paciente morreu (0=Vivo, 1=Morreu) ⚠️ USAR ESTA COLUNA PARA CONTAR MORTES

🏥 INTERNAÇÃO:
- DT_INTER: Data de internação
- DT_SAIDA: Data de alta/saída
- UTI_MES_TO: Dias em UTI
- VAL_TOT: Valor total gasto

🌍 LOCALIZAÇÃO:
- MUNIC_RES: Código município residência
- MUNIC_MOV: Código município internação
- CNES: Código do hospital

REGRAS CRÍTICAS:
1. Para contar MORTES: use MORTE = 1 (NÃO use CID_MORTE)
2. Para filtrar por ESTADO: use UF_RESIDENCIA_PACIENTE
3. Para filtrar por CIDADE: use CIDADE_RESIDENCIA_PACIENTE
4. Para calcular IDADE MÉDIA: use AVG(IDADE)
5. Para contar SEXO: 1=Masculino, 2=Feminino
"""


def mostrar_ajuda():
    """Mostra comandos disponíveis"""
    ajuda = """
📚 COMANDOS DISPONÍVEIS:

  /help ou /ajuda    - Mostra esta ajuda
  /info             - Informações sobre o banco de dados
  /exemplos         - Exemplos de perguntas que você pode fazer
  /limpar           - Limpa a tela
  /quit ou /sair    - Sai do programa

🔍 TIPOS DE PERGUNTAS:

  • Sobre estrutura: "Quantas colunas tem a tabela?"
  • Sobre dados: "Quantos registros existem?"
  • Análises: "Qual a média de idade dos pacientes?"
  • Filtros: "Quantos pacientes são do Rio Grande do Sul?"

"""
    print(ajuda)


def mostrar_exemplos():
    """Mostra exemplos de perguntas"""
    exemplos = """
💡 EXEMPLOS DE PERGUNTAS:

📊 ESTRUTURA:
  • "Quantas colunas tem a tabela dados_sus3?"
  • "Qual é a estrutura da tabela?"
  • "Quais são os tipos de dados das colunas?"

📈 CONTAGENS:
  • "Quantos registros existem na tabela?"
  • "Quantos pacientes são do sexo masculino?" (SEXO = 1)
  • "Quantos pacientes morreram?" (MORTE = 1)
  • "Quantos pacientes morreram no Rio Grande do Sul?"

🔍 ANÁLISES:
  • "Qual a idade média dos pacientes?"
  • "Qual o valor total gasto em internações?"
  • "Quantos pacientes ficaram na UTI?"

🏥 FILTROS ESPECÍFICOS:
  • "Quantos pacientes são de Santa Maria?"
  • "Quais os principais diagnósticos?"
  • "Qual o procedimento mais realizado?"

🌍 GEOGRÁFICAS:
  • "Quantos estados diferentes temos?"
  • "Quais as cidades com mais pacientes?"

⚠️  DICA IMPORTANTE:
  • Para contar MORTES: use MORTE = 1 (não CID_MORTE)
  • Para filtrar SEXO: 1=Masculino, 2=Feminino
  • Para filtrar ESTADOS: use nome completo como 'Rio Grande do Sul'
"""
    print(exemplos)


def mostrar_info_banco(db):
    """Mostra informações sobre o banco de dados"""
    print("\n📊 INFORMAÇÕES DO BANCO DE DADOS:")
    print("=" * 50)

    try:
        # Informações básicas
        tabelas = db.get_usable_table_names()
        print(f"📁 Tabelas disponíveis: {', '.join(tabelas)}")

        for tabela in tabelas:
            # Contar registros
            registros = db.run(f"SELECT COUNT(*) FROM {tabela};")
            registros_count = registros[0][0] if registros else 0

            # Contar colunas
            colunas = db.run(f"SELECT COUNT(*) FROM pragma_table_info('{tabela}');")
            colunas_count = colunas[0][0] if colunas else 0

            print(f"\n🏥 Tabela: {tabela}")
            print(f"   📊 Registros: {registros_count:,}")
            print(f"   📋 Colunas: {colunas_count}")

        print("\n" + "=" * 50)

    except Exception as e:
        print(f"❌ Erro ao obter informações: {e}")


def criar_agente_personalizado(llm, db):
    """Cria um agente SQL com prompts personalizado em português"""

    # Usar o agente padrão mas com configurações customizadas
    agent_executor = create_sql_agent(
        llm,
        db=db,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=10,
        return_intermediate_steps=True,
        # Adicionar instrução em português no prompts do sistema
        agent_executor_kwargs={
            "handle_parsing_errors": True,
        }
    )

    return agent_executor


def processar_comando(comando, db, agent_executor):
    """Processa comandos especiais"""
    comando = comando.lower().strip()

    if comando in ['/help', '/ajuda']:
        mostrar_ajuda()
        return True
    elif comando == '/info':
        mostrar_info_banco(db)
        return True
    elif comando == '/exemplos':
        mostrar_exemplos()
        return True
    elif comando == '/limpar':
        limpar_terminal()
        mostrar_banner()
        return True
    elif comando in ['/quit', '/sair', '/exit']:
        return False

    return None


def processar_pergunta(pergunta, agent_executor, db):
    """Processa uma pergunta normal"""

    # Adicionar contexto para melhor interpretação em português
    pergunta_com_contexto = f"""
    Responda em português brasileiro: {pergunta}

    IMPORTANTE: 
    - Se a pergunta for sobre colunas/estrutura, use: SELECT COUNT(*) FROM pragma_table_info('nome_tabela')
    - Se a pergunta for sobre registros/dados, use: SELECT COUNT(*) FROM nome_tabela
    - Sempre explique o resultado em português brasileiro
    """

    print(f"\n🤔 Processando: {pergunta}")
    print("⏳ Aguarde...")

    try:
        # Tentar com o agente primeiro
        resultado = agent_executor.invoke({"input": pergunta_com_contexto})

        if 'output' in resultado:
            resposta = resultado['output']
            if resposta != 'Agent stopped due to iteration limit or time limit.':
                print(f"\n✅ Resposta: {resposta}")
                return True

        # Se o agente falhou, tentar fallback direto
        print("\n⚠️  Agente não conseguiu responder. Tentando consulta direta...")

        # Fallbacks inteligentes baseados na pergunta
        pergunta_lower = pergunta.lower()

        if "quantas colunas" in pergunta_lower or "colunas tem" in pergunta_lower:
            tabela = "dados_sus3"
            resultado_direto = db.run(f"SELECT COUNT(*) FROM pragma_table_info('{tabela}');")
            print(f"✅ A tabela {tabela} tem {resultado_direto[0][0] if resultado_direto else 'N/A'} colunas.")

        elif "quantos registros" in pergunta_lower or "quantas linhas" in pergunta_lower:
            tabela = "dados_sus3"
            resultado_direto = db.run(f"SELECT COUNT(*) FROM {tabela};")
            print(f"✅ A tabela {tabela} tem {resultado_direto[0][0]:,} registros.")

        elif "quantos estados" in pergunta_lower or "estados diferentes" in pergunta_lower:
            try:
                resultado_direto = db.run("SELECT COUNT(DISTINCT UF_RESIDENCIA_PACIENTE) FROM dados_sus3;")
                print(
                    f"✅ Existem {resultado_direto[0][0] if resultado_direto else 'N/A'} estados diferentes nos dados.")
            except Exception as e:
                print(f"❌ Erro na consulta de estados: {e}")

        elif "quantas cidades" in pergunta_lower or "cidades diferentes" in pergunta_lower:
            try:
                resultado_direto = db.run("SELECT COUNT(DISTINCT CIDADE_RESIDENCIA_PACIENTE) FROM dados_sus3;")
                print(
                    f"✅ Existem {resultado_direto[0][0] if resultado_direto else 'N/A'} cidades diferentes nos dados.")
            except Exception as e:
                print(f"❌ Erro na consulta de cidades: {e}")

        elif "idade média" in pergunta_lower or "media idade" in pergunta_lower:
            try:
                resultado_direto = db.run("SELECT AVG(IDADE) FROM dados_sus3;")
                idade_media = resultado_direto[0][0] if resultado_direto else None
                if idade_media:
                    print(f"✅ A idade média dos pacientes é {idade_media:.1f} anos.")
                else:
                    print("❌ Não foi possível calcular a idade média.")
            except Exception as e:
                print(f"❌ Erro na consulta de idade média: {e}")

        elif "estrutura" in pergunta_lower or "schema" in pergunta_lower:
            print("✅ Estrutura da tabela dados_sus3:")
            print(db.table_info)

        else:
            print("❌ Não foi possível processar a pergunta automaticamente.")
            print("💡 Tente usar os comandos /exemplos para ver perguntas válidas.")
            print("🔍 Ou reformule a pergunta de forma mais específica.")

    except Exception as e:
        print(f"❌ Erro ao processar pergunta: {e}")

        # Fallback adicional para consultas diretas
        print("🔄 Tentando fallback adicional...")
        pergunta_lower = pergunta.lower()

        if "estados" in pergunta_lower:
            try:
                resultado = db.run("SELECT COUNT(DISTINCT UF_RESIDENCIA_PACIENTE) FROM dados_sus3;")
                print(f"✅ Fallback: Existem {resultado[0][0]} estados diferentes.")
            except:
                print("❌ Fallback também falhou.")

        return False

    return True


def main():
    """Função principal do programa"""

    try:
        # Inicialização
        print("🚀 Iniciando agente SQL...")

        # Configurar o modelo com parâmetros para português
        llm = OllamaLLM(
            model="llama3",
            temperature=0.1,  # Menor temperatura para respostas mais consistentes
            top_p=0.9,
            num_predict=2048  # Limite de tokens para respostas
        )

        # Configurar o banco de dados
        db = SQLDatabase.from_uri("sqlite:///sus_data.db", sample_rows_in_table_info=3)

        # Criar o agente com prompts personalizado
        agent_executor = criar_agente_personalizado(llm, db)

        # Mostrar interface inicial
        limpar_terminal()
        mostrar_banner()
        print("✅ Agente inicializado com sucesso!")
        print("🇧🇷 Configurado para responder em português brasileiro")
        print("💡 Digite /help para ver comandos disponíveis\n")

        # Loop principal
        while True:
            try:
                # Receber input do usuário
                pergunta = input("🗣️  Digite sua pergunta (ou /help): ").strip()

                # Verificar se não está vazio
                if not pergunta:
                    continue

                # Processar comandos especiais
                if pergunta.startswith('/'):
                    resultado = processar_comando(pergunta, db, agent_executor)
                    if resultado is False:  # Comando /quit
                        break
                    elif resultado is True:  # Comando processado
                        continue

                # Processar pergunta normal
                processar_pergunta(pergunta, agent_executor, db)

                print("\n" + "-" * 60 + "\n")

            except KeyboardInterrupt:
                print("\n\n⚠️  Interrompido pelo usuário (Ctrl+C)")
                break
            except EOFError:
                print("\n\n👋 Finalizando...")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                print("💡 Tente novamente ou digite /help")

        print("\n👋 Obrigado por usar o Agente SQL! Até mais!")

    except Exception as e:
        print(f"❌ Erro crítico ao inicializar: {e}")
        print("🔧 Verifique se:")
        print("   • O modelo llama3 está disponível no Ollama")
        print("   • O arquivo sus_data.db existe")
        print("   • As dependências estão instaladas")
        sys.exit(1)


if __name__ == "__main__":
    main()