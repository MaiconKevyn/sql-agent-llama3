"""Templates de prompts para o agente SQL."""

from langchain.prompts import PromptTemplate


class PromptManager:
    """Gerencia templates de prompts em português brasileiro."""

    def __init__(self):
        """Inicializa o gerenciador de prompts."""
        self.custom_template = self._create_custom_template()

    def _create_custom_template(self) -> PromptTemplate:
        """Cria template personalizado em português brasileiro."""
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
        
        PERGUNTA: {input}
        """

        return PromptTemplate(
            input_variables=["input"],
            template=template
        )

    def create_contextualized_query(self, query: str) -> str:
        """Cria consulta contextualizada em português."""
        return f"""
    Responda em português brasileiro: {query}

    IMPORTANTE: 
    - Se a pergunta for sobre colunas/estrutura, use: SELECT COUNT(*) FROM pragma_table_info('nome_tabela')
    - Se a pergunta for sobre registros/dados, use: SELECT COUNT(*) FROM nome_tabela
    - Sempre explique o resultado em português brasileiro
    """

    def get_custom_template(self) -> PromptTemplate:
        """Retorna o template personalizado."""
        return self.custom_template