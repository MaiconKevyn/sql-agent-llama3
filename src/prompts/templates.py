"""Templates de prompts para o agente SQL com documentação de schema."""

from langchain.prompts import PromptTemplate
from src.utils.schema_documentation import schema_docs


class PromptManager:
    """Gerencia templates de prompts em português brasileiro com contexto de schema."""

    def __init__(self):
        """Inicializa o gerenciador de prompts."""
        self.custom_template = self._create_custom_template()

    def _create_custom_template(self) -> PromptTemplate:
        """Cria template personalizado em português brasileiro."""

        schema_context = schema_docs.get_contextual_prompt()

        template = f"""
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
        
        {schema_context}
        
        PERGUNTA: {{input}}
        """

        return PromptTemplate(
            input_variables=["input"],
            template=template
        )

    def create_contextualized_query(self, query: str) -> str:
        """Cria consulta contextualizada em português (versão legada)."""
        return self.create_contextualized_query_with_schema(query)

    def create_contextualized_query_with_schema(self, query: str) -> str:
        """Cria consulta contextualizada com documentação do schema."""

        # Obter sugestões de colunas baseadas na intenção
        column_suggestions = schema_docs.get_column_suggestions(query)
        suggestions_text = ""
        if column_suggestions:
            suggestions_text = f"\nSUGESTÕES DE COLUNAS PARA SUA PERGUNTA:\n" + "\n".join(f"- {s}" for s in column_suggestions)

        return f"""
        Responda em português brasileiro: {query}
    
        IMPORTANTE - DOCUMENTAÇÃO ESPECÍFICA:
        
        1. PARA MORTALIDADE:
           - Use MORTE = 1 para contar óbitos
           - NÃO use CID_MORTE > 0 (incorreto!)
           - CID_MORTE contém a CAUSA da morte, não indica se morreu
        
        2. PARA CIDADES:
           - Use CIDADE_RESIDENCIA_PACIENTE = 'Nome da Cidade'
           - NÃO use MUNIC_RES = código (menos preciso)
           - Exemplos: 'Porto Alegre', 'Santa Maria', 'Caxias do Sul'
        
        3. PARA SEXO:
           - SEXO = 1 significa Masculino
           - SEXO = 3 significa Feminino
           - NÃO existe SEXO = 2
        
        4. PARA UTI:
           - UTI_MES_TO = 0 significa que NÃO ficou em UTI
           - UTI_MES_TO > 0 significa número de dias em UTI
        
        5. QUERIES CORRETAS PARA MORTALIDADE:
           - Total de mortes: SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1
           - Mortes por cidade: SELECT COUNT(*) FROM dados_sus3 WHERE CIDADE_RESIDENCIA_PACIENTE = 'Nome' AND MORTE = 1
           - Mortes por estado: SELECT COUNT(*) FROM dados_sus3 WHERE UF_RESIDENCIA_PACIENTE = 'UF' AND MORTE = 1
        
        {suggestions_text}
        
        SEMPRE valide se está usando as colunas corretas para o que foi perguntado!
        Dê preferência para nomes de cidades ao invés de códigos IBGE!
        """

    def get_custom_template(self) -> PromptTemplate:
        """Retorna o template personalizado."""
        return self.custom_template

    def get_mortality_correction_prompt(self) -> str:
        """Retorna prompt específico para correção de consultas de mortalidade."""
        return """
        CORREÇÃO IMPORTANTE SOBRE MORTALIDADE:
        
        ❌ INCORRETO: SELECT COUNT(*) FROM dados_sus3 WHERE CID_MORTE > 0
        ✅ CORRETO: SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1
        
        EXPLICAÇÃO:
        - MORTE = campo que indica se houve óbito (0=não, 1=sim)
        - CID_MORTE = código da CAUSA da morte (pode estar vazio mesmo quando houve morte)
        
        Use sempre MORTE = 1 para contar mortes!
        """

    def get_geography_correction_prompt(self) -> str:
        """Retorna prompt específico para correção de consultas geográficas."""
        return """
        CORREÇÃO IMPORTANTE SOBRE GEOGRAFIA:
        
        ❌ INCORRETO: SELECT COUNT(*) FROM dados_sus3 WHERE MUNIC_RES = 431490
        ✅ CORRETO: SELECT COUNT(*) FROM dados_sus3 WHERE CIDADE_RESIDENCIA_PACIENTE = 'Porto Alegre'
        
        EXPLICAÇÃO:
        - MUNIC_RES = código IBGE (pode ter dados incompletos)
        - CIDADE_RESIDENCIA_PACIENTE = nome completo da cidade (mais preciso)
        
        Use sempre o nome da cidade para maior precisão!
        """