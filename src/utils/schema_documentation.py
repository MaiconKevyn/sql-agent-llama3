"""
Documentação completa do schema dos dados SUS (SIH/SUS).
Localização: src/utils/schema_documentation.py
"""

from typing import Dict, Any, List


class SUSSchemaDocumentation:
    """Documentação completa do schema dos dados do SUS."""

    def __init__(self):
        """Inicializa a documentação do schema."""
        self.columns_info = self._build_columns_documentation()
        self.business_rules = self._build_business_rules()

    def _build_columns_documentation(self) -> Dict[str, Dict[str, Any]]:
        """Constrói documentação detalhada das colunas."""

        return {
            # Diagnósticos
            "DIAG_PRINC": {
                "nome": "Diagnóstico Principal",
                "tipo": "TEXT",
                "descricao": "Código CID-10 do diagnóstico principal da internação",
                "exemplos": ["A46", "C168", "J128"],
                "valores_especiais": {
                    "U99": "CID 10ª Revisão não disponível (período de transição)"
                },
                "validacao": "Código CID-10 válido",
                "uso_comum": "Identificar principal motivo da internação"
            },

            # Geografia
            "MUNIC_RES": {
                "nome": "Município de Residência",
                "tipo": "BIGINT",
                "descricao": "Código IBGE do município de residência do paciente",
                "exemplos": [431490, 430300, 355030],
                "validacao": "Código IBGE válido de 6 dígitos",
                "uso_comum": "Análises geográficas por código IBGE",
                "nota": "Use CIDADE_RESIDENCIA_PACIENTE para filtrar por nome da cidade"
            },

            "MUNIC_MOV": {
                "nome": "Município de Movimentação",
                "tipo": "BIGINT",
                "descricao": "Código IBGE do município onde ocorreu a internação",
                "exemplos": [431490, 430300, 355030],
                "validacao": "Código IBGE válido de 6 dígitos",
                "uso_comum": "Fluxos de pacientes entre municípios"
            },

            "UF_RESIDENCIA_PACIENTE": {
                "nome": "UF de Residência",
                "tipo": "TEXT",
                "descricao": "Sigla da Unidade Federativa de residência do paciente",
                "exemplos": ["RS", "SP", "RJ", "PR"],
                "validacao": "Sigla UF válida (2 caracteres)",
                "uso_comum": "Análises por estado"
            },

            "CIDADE_RESIDENCIA_PACIENTE": {
                "nome": "Cidade de Residência",
                "tipo": "TEXT",
                "descricao": "Nome completo da cidade de residência do paciente",
                "exemplos": ["Porto Alegre", "Santa Maria", "Caxias do Sul"],
                "uso_comum": "Filtrar por cidade específica - CAMPO PREFERIDO para consultas por cidade",
                "nota": "Use este campo ao invés de MUNIC_RES para perguntas sobre cidades"
            },

            # Demografia
            "IDADE": {
                "nome": "Idade",
                "tipo": "BIGINT",
                "descricao": "Idade do paciente no momento da internação (em anos)",
                "faixa_valores": "0 a 120 anos",
                "valores_especiais": {
                    "0": "Recém-nascidos (menos de 1 ano)",
                    ">= 120": "Idade inconsistente (verificar dados)"
                },
                "uso_comum": "Análises demográficas, faixas etárias"
            },

            "SEXO": {
                "nome": "Sexo",
                "tipo": "BIGINT",
                "descricao": "Sexo do paciente",
                "valores_validos": {
                    1: "Masculino",
                    3: "Feminino"
                },
                "nota": "ATENÇÃO: Usa códigos 1 e 3 (padrão DATASUS), não 1 e 2!",
                "uso_comum": "Análises de gênero, epidemiologia"
            },

            # Morte e Óbito
            "MORTE": {
                "nome": "Indicador de Óbito",
                "tipo": "BIGINT",
                "descricao": "Indica se o paciente morreu durante a internação",
                "valores_validos": {
                    0: "Paciente NÃO morreu (alta, transferência, etc.)",
                    1: "Paciente MORREU durante a internação"
                },
                "uso_comum": "Calcular mortalidade hospitalar - CAMPO PRINCIPAL PARA CONTAR MORTES",
                "query_exemplo": "SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1",
                "nota": "SEMPRE use MORTE = 1 para contar mortes, nunca CID_MORTE > 0"
            },

            "CID_MORTE": {
                "nome": "CID da Causa da Morte",
                "tipo": "BIGINT",
                "descricao": "Código CID-10 da causa básica da morte (quando MORTE = 1)",
                "valores_validos": {
                    0: "Paciente não morreu OU causa não informada",
                    "> 0": "Código CID-10 da causa da morte"
                },
                "relacao": "Só tem valor quando MORTE = 1 (mas nem sempre preenchido)",
                "uso_comum": "Análise de causas de morte hospitalar",
                "query_exemplo": "SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1 AND CID_MORTE > 0",
                "nota": "NÃO usar para contar mortes! Usar apenas para analisar causas quando MORTE = 1"
            },

            # Procedimentos e Custos
            "PROC_REA": {
                "nome": "Procedimento Realizado",
                "tipo": "BIGINT",
                "descricao": "Código do procedimento principal realizado na internação",
                "exemplos": [303080078, 304100021, 303140151],
                "uso_comum": "Análises de procedimentos médicos"
            },

            "VAL_TOT": {
                "nome": "Valor Total",
                "tipo": "FLOAT",
                "descricao": "Valor total pago pela internação (em Reais)",
                "exemplos": [292.62, 797.11, 4987.52],
                "uso_comum": "Análises de custos hospitalares"
            },

            # UTI
            "UTI_MES_TO": {
                "nome": "Dias de UTI",
                "tipo": "BIGINT",
                "descricao": "Número total de dias que o paciente permaneceu em UTI",
                "valores_validos": {
                    0: "Não ficou em UTI",
                    "> 0": "Número de dias em UTI"
                },
                "uso_comum": "Análises de complexidade, custos de UTI"
            },

            # Hospital
            "CNES": {
                "nome": "Código CNES",
                "tipo": "BIGINT",
                "descricao": "Código do estabelecimento de saúde no Cadastro Nacional de Estabelecimentos de Saúde",
                "exemplos": [2266474],
                "uso_comum": "Identificar hospital específico"
            },

            # Datas
            "DT_INTER": {
                "nome": "Data de Internação",
                "tipo": "BIGINT",
                "descricao": "Data da internação no formato AAAAMMDD",
                "exemplos": [20170803, 20170726],
                "formato": "YYYYMMDD",
                "uso_comum": "Análises temporais, sazonalidade"
            },

            "DT_SAIDA": {
                "nome": "Data de Saída",
                "tipo": "BIGINT",
                "descricao": "Data da alta/saída no formato AAAAMMDD",
                "exemplos": [20170808, 20170803],
                "formato": "YYYYMMDD",
                "uso_comum": "Calcular tempo de permanência"
            },

            # Agregações
            "TOTAL_OCORRENCIAS": {
                "nome": "Total de Ocorrências",
                "tipo": "BIGINT",
                "descricao": "Contador de ocorrências (campo calculado)",
                "uso_comum": "Agregações, contagens"
            },

            # Coordenadas
            "LATI_CIDADE_RES": {
                "nome": "Latitude da Cidade",
                "tipo": "FLOAT",
                "descricao": "Latitude da cidade de residência do paciente",
                "exemplos": [-29.6860512, -30.0346471],
                "uso_comum": "Análises geoespaciais, mapas"
            },

            "LONG_CIDADE_RES": {
                "nome": "Longitude da Cidade",
                "tipo": "FLOAT",
                "descricao": "Longitude da cidade de residência do paciente",
                "exemplos": [-53.8069214, -51.2176584],
                "uso_comum": "Análises geoespaciais, mapas"
            }
        }

    def _build_business_rules(self) -> Dict[str, List[str]]:
        """Constrói regras de negócio importantes."""

        return {
            "mortalidade": [
                "Para contar mortes: usar MORTE = 1 (NÃO MORTE > 0 ou CID_MORTE > 0)",
                "Para analisar causas de morte: usar CID_MORTE > 0 E MORTE = 1",
                "CID_MORTE = 0 significa que não houve morte OU causa não foi informada",
                "Nem todos os casos com MORTE = 1 têm CID_MORTE preenchido",
                "NUNCA use CID_MORTE > 0 para contar mortes - resultados incorretos!"
            ],

            "geografia": [
                "MUNIC_RES = código IBGE do município onde o paciente RESIDE",
                "MUNIC_MOV = código IBGE do município onde ocorreu a INTERNAÇÃO",
                "CIDADE_RESIDENCIA_PACIENTE = NOME da cidade (use para filtrar por cidade)",
                "UF_RESIDENCIA_PACIENTE = sigla do estado",
                "Para filtrar por cidade: usar CIDADE_RESIDENCIA_PACIENTE = 'Nome da Cidade'",
                "Para filtrar por código: usar MUNIC_RES = código_ibge",
                "IMPORTANTE: Porto Alegre = código 431490, Santa Maria = código 430300",
                "PREFERIR nome da cidade ao invés de código para maior precisão"
            ],

            "sexo": [
                "SEXO = 1 significa Masculino",
                "SEXO = 3 significa Feminino",
                "Não usar SEXO = 2 (não existe no padrão DATASUS)",
                "Cuidado: não é 1=M, 2=F como em outros sistemas"
            ],

            "uti": [
                "UTI_MES_TO = 0 significa que não ficou em UTI",
                "UTI_MES_TO > 0 indica número de dias em UTI",
                "Pacientes com UTI_MES_TO > 0 geralmente têm maior VAL_TOT"
            ],

            "datas": [
                "DT_INTER <= DT_SAIDA (data internação antes ou igual à saída)",
                "Formato YYYYMMDD (ex: 20170803 = 03/08/2017)",
                "Tempo permanência = DT_SAIDA - DT_INTER (cuidado com cálculo de dias)"
            ],

            "valores": [
                "VAL_TOT em Reais (moeda corrente)",
                "Valores muito baixos podem indicar procedimentos simples",
                "Valores altos geralmente associados a UTI ou procedimentos complexos"
            ]
        }

    def get_column_info(self, column_name: str) -> Dict[str, Any]:
        """Retorna informações detalhadas de uma coluna."""
        column_upper = column_name.upper()
        return self.columns_info.get(column_upper, {
            "nome": column_name,
            "descricao": "Coluna não documentada",
            "tipo": "Desconhecido"
        })

    def get_mortality_info(self) -> Dict[str, Any]:
        """Retorna informações específicas sobre mortalidade."""
        return {
            "campo_principal": "MORTE",
            "descricao": "Use MORTE = 1 para contar óbitos",
            "campo_causa": "CID_MORTE",
            "queries_corretas": {
                "total_mortes": "SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1",
                "taxa_mortalidade": "SELECT (COUNT(CASE WHEN MORTE = 1 THEN 1 END) * 100.0) / COUNT(*) FROM dados_sus3",
                "mortes_por_estado": "SELECT UF_RESIDENCIA_PACIENTE, COUNT(*) FROM dados_sus3 WHERE MORTE = 1 GROUP BY UF_RESIDENCIA_PACIENTE",
                "mortes_por_cidade": "SELECT CIDADE_RESIDENCIA_PACIENTE, COUNT(*) FROM dados_sus3 WHERE MORTE = 1 GROUP BY CIDADE_RESIDENCIA_PACIENTE"
            },
            "queries_incorretas": {
                "SELECT COUNT(*) FROM dados_sus3 WHERE CID_MORTE > 0": "Não conta todas as mortes (causa pode não estar preenchida)",
                "SELECT COUNT(*) FROM dados_sus3 WHERE MUNIC_RES = codigo AND MORTE > 0": "Use nome da cidade e MORTE = 1"
            }
        }

    def get_contextual_prompt(self) -> str:
        """Gera prompt contextual para o agente com informações do schema."""

        mortality_info = self.get_mortality_info()

        prompt = f"""
        DOCUMENTAÇÃO DO SCHEMA - DADOS SUS (SIH/SUS):
        
        CAMPOS IMPORTANTES PARA ANÁLISES:
        
        1. MORTALIDADE:
           - MORTE: {self.columns_info['MORTE']['valores_validos']}
           - CID_MORTE: {self.columns_info['CID_MORTE']['descricao']}
           - REGRA: Para contar mortes, use "MORTE = 1", NÃO "MORTE > 0" ou "CID_MORTE > 0"
        
        2. GEOGRAFIA:
           - CIDADE_RESIDENCIA_PACIENTE: Nome da cidade (use para filtrar por cidade)
           - MUNIC_RES: Código IBGE (431490=Porto Alegre, 430300=Santa Maria)
           - UF_RESIDENCIA_PACIENTE: Sigla do estado
           - REGRA: Para perguntas sobre cidades, use CIDADE_RESIDENCIA_PACIENTE = 'Nome'
        
        3. SEXO:
           - {self.columns_info['SEXO']['valores_validos']}
           - ATENÇÃO: Não é 1=M, 2=F - é 1=M, 3=F
        
        4. UTI:
           - UTI_MES_TO = 0: Não ficou em UTI
           - UTI_MES_TO > 0: Número de dias em UTI
        
        QUERIES CORRETAS:
        - Mortes totais: SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1
        - Mortes por cidade: SELECT COUNT(*) FROM dados_sus3 WHERE CIDADE_RESIDENCIA_PACIENTE = 'Nome' AND MORTE = 1
        
        EVITAR:
        - SELECT COUNT(*) FROM dados_sus3 WHERE CID_MORTE > 0  (incorreto para mortes!)
        - SELECT COUNT(*) FROM dados_sus3 WHERE MUNIC_RES = codigo AND MORTE > 0  (use nome da cidade e MORTE = 1!)
                """

        return prompt

    def validate_query_semantics(self, query: str) -> Dict[str, Any]:
        """Valida semântica de uma query baseada no schema."""

        query_upper = query.upper()
        issues = []
        suggestions = []

        # Verificar problemas comuns com mortalidade
        if "CID_MORTE > 0" in query_upper and "MORTE" not in query_upper:
            issues.append("Usando CID_MORTE > 0 para contar mortes (incorreto)")
            suggestions.append("Use 'MORTE = 1' para contar óbitos")

        # Verificar uso de código IBGE para cidades quando deveria usar nome
        if "MUNIC_RES =" in query_upper and any(city in query_upper for city in ["PORTO", "SANTA", "CAXIAS"]):
            issues.append("Usando código IBGE para filtrar cidade (pode ser impreciso)")
            suggestions.append("Use 'CIDADE_RESIDENCIA_PACIENTE = nome_cidade' para maior precisão")

        # Verificar problemas com sexo
        if "SEXO = 2" in query_upper:
            issues.append("SEXO = 2 não existe no padrão DATASUS")
            suggestions.append("Use SEXO = 1 (Masculino) ou SEXO = 3 (Feminino)")

        # Verificar uso de MORTE > 0 quando deveria ser MORTE = 1
        if "MORTE > 0" in query_upper:
            suggestions.append("Considere usar 'MORTE = 1' ao invés de 'MORTE > 0' para maior especificidade")

        # Verificar se está usando campos de data corretamente
        if ("DT_INTER" in query_upper or "DT_SAIDA" in query_upper) and "LIKE" in query_upper:
            suggestions.append("Datas estão no formato YYYYMMDD - considere usar comparações numéricas")

        return {
            "query": query,
            "issues": issues,
            "suggestions": suggestions,
            "is_valid": len(issues) == 0
        }

    def get_column_suggestions(self, intent: str) -> List[str]:
        """Sugere colunas baseado na intenção do usuário."""

        intent_lower = intent.lower()
        suggestions = []

        if any(word in intent_lower for word in ["morte", "morreu", "óbito", "falecimento"]):
            suggestions.append("MORTE = 1 (para contar óbitos)")
            suggestions.append("CID_MORTE (para causa da morte, quando MORTE = 1)")

        if any(word in intent_lower for word in ["cidade", "porto alegre", "santa maria"]):
            suggestions.append("CIDADE_RESIDENCIA_PACIENTE (nome da cidade - PREFERIDO)")
            suggestions.append("MUNIC_RES (código IBGE - menos preciso)")

        if any(word in intent_lower for word in ["idade", "anos"]):
            suggestions.append("IDADE (idade em anos)")

        if any(word in intent_lower for word in ["sexo", "masculino", "feminino"]):
            suggestions.append("SEXO (1=Masculino, 3=Feminino)")

        if any(word in intent_lower for word in ["estado", "uf", "região"]):
            suggestions.append("UF_RESIDENCIA_PACIENTE (sigla do estado)")

        if any(word in intent_lower for word in ["uti", "intensive"]):
            suggestions.append("UTI_MES_TO (dias em UTI, 0=não ficou)")

        if any(word in intent_lower for word in ["custo", "valor"]):
            suggestions.append("VAL_TOT (valor total em Reais)")

        return suggestions


# Instância global da documentação
schema_docs = SUSSchemaDocumentation()