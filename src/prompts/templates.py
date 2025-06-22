"""Templates de prompts para o agente SQL com documentação de schema."""

from langchain.prompts import PromptTemplate
from src.utils.schema_documentation import schema_docs


class PromptManager:
    """Gerencia templates de prompts em português brasileiro com contexto de schema."""

    def __init__(self):
        """Inicializa o gerenciador de prompts."""
        self.custom_template = self._create_custom_template()
        self.cid_knowledge = self._build_cid_knowledge()

    def _build_cid_knowledge(self) -> str:
        """
        Constrói base de conhecimento sobre códigos CID-10 para o agente.
        """
        return """
        CÓDIGOS CID-10 - CAPÍTULOS PRINCIPAIS:

        🫁 DOENÇAS RESPIRATÓRIAS (J00-J99):
           - J00-J06: Infecções respiratórias agudas
           - J09-J18: Influenza e pneumonia  
           - J20-J22: Outras infecções respiratórias agudas
           - J40-J47: Doenças crônicas das vias respiratórias inferiores
           - J60-J70: Doenças pulmonares devido a agentes externos
           - Exemplos: J128 (pneumonia), J44 (DPOC), J45 (asma)

        ❤️ DOENÇAS CARDIOVASCULARES (I00-I99):
           - I20-I25: Doenças isquêmicas do coração
           - I60-I69: Doenças cerebrovasculares
           - I10-I15: Doenças hipertensivas
           - Exemplos: I21 (infarto), I64 (AVC), I10 (hipertensão)

        🎗️ NEOPLASIAS/CÂNCER (C00-D49):
           - C00-C97: Neoplasias malignas
           - D00-D09: Neoplasias in situ
           - Exemplos: C78 (metástases), C50 (câncer mama)

        🩺 OUTROS CAPÍTULOS IMPORTANTES:
           - A00-B99: Doenças infecciosas e parasitárias
           - E00-E89: Doenças endócrinas (E10-E14: diabetes)
           - F00-F99: Transtornos mentais
           - G00-G99: Doenças do sistema nervoso
           - K00-K95: Doenças do aparelho digestivo
           - N00-N99: Doenças do aparelho geniturinário
        """

    def _create_custom_template(self) -> PromptTemplate:
        """Cria template personalizado em português brasileiro."""

        schema_context = schema_docs.get_contextual_prompt()
        cid_knowledge = self._build_cid_knowledge()

        template = f"""
        Você é um assistente especialista em SQL que SEMPRE responde em português brasileiro.
        
        ⚠️  REGRAS CRÍTICAS - SEMPRE SEGUIR:
        1. 🇧🇷 SEMPRE responda APENAS em português brasileiro
        2. 🏥 DIAG_PRINC contém CÓDIGOS CID-10, NÃO descrições em português
        3. 📊 Execute a query SQL e forneça o RESULTADO NUMÉRICO
        4. ✅ Seja direto: "Existem X casos de..." ao invés de explicar o que faria
        
        {cid_knowledge}

        📋 COMO TRABALHAR COM DOENÇAS ESPECÍFICAS:
        
        ✅ CORRETO para doenças respiratórias:
           - SELECT COUNT(*) FROM dados_sus3 WHERE DIAG_PRINC LIKE 'J%'
           - SELECT COUNT(*) FROM dados_sus3 WHERE DIAG_PRINC >= 'J00' AND DIAG_PRINC <= 'J99'
        
        ❌ INCORRETO:
           - WHERE DIAG_PRINC LIKE '%respiratória%' (códigos não têm texto em português!)
           - WHERE DIAG_PRINC LIKE '%doenças respiratórias%' (nunca funciona!)
        
        🎯 PARA DIFERENTES TIPOS DE CONSULTA:
        - Casos totais: COUNT(*)
        - Mortes: COUNT(*) WHERE MORTE = 1
        - Internações: COUNT(*) (todos registros são internações)
        
        ⚡ FLUXO DE TRABALHO:
        1. Identifique o tipo de doença na pergunta
        2. Mapeie para o capítulo CID-10 correto
        3. Use LIKE 'X%' para capítulo completo (ex: 'J%' para respiratórias)
        4. Execute a query
        5. Responda com o número encontrado
        
        {schema_context}
        
        🚨 LEMBRE-SE:
        - DIAG_PRINC = códigos como "J128", "I21", "C50" (não texto!)
        - Sempre teste sua query antes de responder
        - Forneça número exato, não explicações longas
        - Responda em português brasileiro sempre!
        
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