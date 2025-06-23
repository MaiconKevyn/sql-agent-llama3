"""
Sistema de Interpretação CID-10 Inteligente
Resolve a confusão entre CID_MORTE e DIAG_PRINC + interpreta códigos automaticamente
"""

import re
from typing import Dict, List, Optional, Tuple, Set
import pandas as pd


class CIDInterpreter:
    """
    Interpretador inteligente de códigos CID-10 que:
    1. Mapeia códigos para categorias legíveis
    2. Distingue claramente CID_MORTE vs DIAG_PRINC
    3. Sugere queries corretas baseadas em intenção
    4. Valida queries SQL para detectar erros comuns
    """

    def __init__(self):
        """Inicializa o interpretador com mappings CID-10."""
        self.chapter_mapping = self._build_chapter_mapping()
        self.respiratory_codes = self._build_respiratory_codes()
        self.common_patterns = self._build_common_patterns()

    def _build_chapter_mapping(self) -> Dict[str, Dict]:
        """Constrói mapping completo dos capítulos CID-10."""
        return {
            'A': {
                'range': ('A00', 'B99'),
                'name': 'Doenças infecciosas e parasitárias',
                'keywords': ['infecciosa', 'parasitária', 'infecção', 'vírus', 'bactéria']
            },
            'B': {
                'range': ('A00', 'B99'),
                'name': 'Doenças infecciosas e parasitárias',
                'keywords': ['infecciosa', 'parasitária', 'infecção', 'vírus', 'bactéria']
            },
            'C': {
                'range': ('C00', 'D49'),
                'name': 'Neoplasias malignas',
                'keywords': ['câncer', 'cancer', 'tumor', 'neoplasia', 'maligno', 'oncológica']
            },
            'D': {
                'range': ('C00', 'D89'),
                'name': 'Neoplasias e doenças do sangue',
                'keywords': ['tumor', 'sangue', 'anemia', 'leucemia', 'neoplasia']
            },
            'E': {
                'range': ('E00', 'E89'),
                'name': 'Doenças endócrinas e metabólicas',
                'keywords': ['diabetes', 'endócrina', 'metabólica', 'hormonal', 'tireóide']
            },
            'F': {
                'range': ('F00', 'F99'),
                'name': 'Transtornos mentais e comportamentais',
                'keywords': ['mental', 'psiquiátrica', 'depressão', 'ansiedade', 'comportamental']
            },
            'G': {
                'range': ('G00', 'G99'),
                'name': 'Doenças do sistema nervoso',
                'keywords': ['neurológica', 'nervoso', 'epilepsia', 'parkinson', 'alzheimer']
            },
            'H': {
                'range': ('H00', 'H95'),
                'name': 'Doenças dos olhos e ouvidos',
                'keywords': ['olho', 'ouvido', 'visão', 'audição', 'oftálmica']
            },
            'I': {
                'range': ('I00', 'I99'),
                'name': 'Doenças cardiovasculares',
                'keywords': ['cardiovascular', 'cardíaca', 'coração', 'infarto', 'avc', 'hipertensão']
            },
            'J': {
                'range': ('J00', 'J99'),
                'name': 'Doenças respiratórias',
                'keywords': ['respiratória', 'pulmonar', 'pulmão', 'pneumonia', 'asma', 'bronquite']
            },
            'K': {
                'range': ('K00', 'K95'),
                'name': 'Doenças digestivas',
                'keywords': ['digestiva', 'estômago', 'intestino', 'fígado', 'gastrite']
            },
            'L': {
                'range': ('L00', 'L99'),
                'name': 'Doenças da pele',
                'keywords': ['pele', 'dermatológica', 'eczema', 'dermatite']
            },
            'M': {
                'range': ('M00', 'M99'),
                'name': 'Doenças musculoesqueléticas',
                'keywords': ['osso', 'músculo', 'articulação', 'artrite', 'osteoporose']
            },
            'N': {
                'range': ('N00', 'N99'),
                'name': 'Doenças renais e urinárias',
                'keywords': ['renal', 'rim', 'urinária', 'bexiga', 'próstata']
            },
            'O': {
                'range': ('O00', 'O99'),
                'name': 'Gravidez, parto e puerpério',
                'keywords': ['gravidez', 'parto', 'gestação', 'obstétrica']
            },
            'P': {
                'range': ('P00', 'P96'),
                'name': 'Condições perinatais',
                'keywords': ['recém-nascido', 'perinatal', 'neonatal']
            },
            'Q': {
                'range': ('Q00', 'Q99'),
                'name': 'Malformações congênitas',
                'keywords': ['malformação', 'congênita', 'anomalia']
            },
            'R': {
                'range': ('R00', 'R99'),
                'name': 'Sintomas e sinais gerais',
                'keywords': ['sintoma', 'febre', 'dor', 'mal-estar']
            },
            'S': {
                'range': ('S00', 'T98'),
                'name': 'Lesões e traumatismos',
                'keywords': ['lesão', 'trauma', 'fratura', 'ferimento']
            },
            'T': {
                'range': ('S00', 'T98'),
                'name': 'Lesões e traumatismos',
                'keywords': ['lesão', 'trauma', 'envenenamento', 'queimadura']
            },
            'V': {
                'range': ('V01', 'Y98'),
                'name': 'Causas externas',
                'keywords': ['acidente', 'externa', 'violência']
            },
            'W': {
                'range': ('V01', 'Y98'),
                'name': 'Causas externas',
                'keywords': ['acidente', 'externa', 'violência']
            },
            'X': {
                'range': ('V01', 'Y98'),
                'name': 'Causas externas',
                'keywords': ['acidente', 'externa', 'violência']
            },
            'Y': {
                'range': ('V01', 'Y98'),
                'name': 'Causas externas',
                'keywords': ['acidente', 'externa', 'violência']
            },
            'Z': {
                'range': ('Z00', 'Z99'),
                'name': 'Fatores que influenciam o estado de saúde',
                'keywords': ['prevenção', 'contato', 'exame']
            }
        }

    def _build_respiratory_codes(self) -> Set[str]:
        """Constrói conjunto de códigos respiratórios conhecidos."""
        # Códigos respiratórios comuns que podem aparecer nos dados
        return {
            'J00', 'J01', 'J02', 'J03', 'J04', 'J05', 'J06',  # Infecções agudas
            'J09', 'J10', 'J11', 'J12', 'J13', 'J14', 'J15', 'J16', 'J17', 'J18',  # Pneumonia/Gripe
            'J20', 'J21', 'J22',  # Bronquite aguda
            'J40', 'J41', 'J42', 'J43', 'J44', 'J45', 'J46', 'J47',  # Crônicas
            'J60', 'J61', 'J62', 'J63', 'J64', 'J65', 'J66', 'J67', 'J68', 'J69', 'J70',  # Externas
            'J80', 'J81', 'J82', 'J84', 'J85', 'J86',  # Outras
            'J90', 'J91', 'J92', 'J93', 'J94', 'J95', 'J96', 'J98', 'J99'  # Outras/NE
        }

    def _build_common_patterns(self) -> List[Dict]:
        """Constrói padrões comuns de consultas médicas."""
        return [
            {
                'pattern': r'(?:quantas?|quantos?)\s+(?:pessoas?|pacientes?|casos?)\s+(?:com|de|por)\s+([\w\s]+)',
                'type': 'count_cases',
                'field': 'DIAG_PRINC',
                'description': 'Contagem de casos por diagnóstico'
            },
            {
                'pattern': r'(?:quantas?|quantos?)\s+(?:mortes?|óbitos?|morreram)\s+(?:com|de|por)\s+([\w\s]+)',
                'type': 'count_deaths',
                'field': 'MORTE + DIAG_PRINC',
                'description': 'Contagem de mortes por diagnóstico'
            },
            {
                'pattern': r'(?:quantas?|quantos?)\s+(?:internações?|internaç[oõ]es?)\s+(?:com|de|por)\s+([\w\s]+)',
                'type': 'count_admissions',
                'field': 'DIAG_PRINC',
                'description': 'Contagem de internações por diagnóstico'
            }
        ]

    def interpret_cid_code(self, code: str) -> Dict:
        """
        Interpreta um código CID-10 individual.

        Args:
            code: Código CID como 'J128', 'I21', etc.

        Returns:
            Dict com informações interpretadas
        """
        if not code or len(code) < 1:
            return {'error': 'Código vazio ou inválido'}

        chapter_letter = code[0].upper()

        if chapter_letter not in self.chapter_mapping:
            return {'error': f'Capítulo {chapter_letter} não reconhecido'}

        chapter_info = self.chapter_mapping[chapter_letter]

        return {
            'code': code,
            'chapter': chapter_letter,
            'chapter_name': chapter_info['name'],
            'range': chapter_info['range'],
            'keywords': chapter_info['keywords'],
            'is_respiratory': chapter_letter == 'J',
            'is_cardiovascular': chapter_letter == 'I',
            'is_cancer': chapter_letter in ['C', 'D'],
            'sql_condition': f"DIAG_PRINC LIKE '{chapter_letter}%'"
        }

    def analyze_query_intent(self, query: str) -> Dict:
        """
        Analisa a intenção de uma query em linguagem natural.

        Args:
            query: Query em português como "quantas pessoas com doenças respiratórias"

        Returns:
            Dict com análise da intenção
        """
        query_lower = query.lower().strip()

        result = {
            'original_query': query,
            'intent_type': None,
            'disease_terms': [],
            'target_field': None,
            'sql_suggestions': [],
            'warnings': []
        }

        # Analisar padrões
        for pattern_info in self.common_patterns:
            match = re.search(pattern_info['pattern'], query_lower)
            if match:
                disease_term = match.group(1).strip()
                result['intent_type'] = pattern_info['type']
                result['target_field'] = pattern_info['field']
                result['disease_terms'] = [disease_term]

                # Mapear termo para capítulo CID
                mapped_chapter = self._map_term_to_chapter(disease_term)
                if mapped_chapter:
                    result['mapped_chapter'] = mapped_chapter
                    result['sql_suggestions'] = self._generate_sql_suggestions(
                        pattern_info['type'], mapped_chapter
                    )

                break

        # Detectar confusões comuns
        if 'cid_morte' in query_lower and 'diagnóstico' in query_lower:
            result['warnings'].append(
                "⚠️ CID_MORTE é causa da morte, não diagnóstico da internação (use DIAG_PRINC)"
            )

        return result

    def _map_term_to_chapter(self, term: str) -> Optional[Dict]:
        """Mapeia termo da doença para capítulo CID."""
        term_lower = term.lower()

        for chapter, info in self.chapter_mapping.items():
            for keyword in info['keywords']:
                if keyword in term_lower or term_lower in keyword:
                    return {
                        'chapter': chapter,
                        'name': info['name'],
                        'range': info['range']
                    }
        return None

    def _generate_sql_suggestions(self, intent_type: str, chapter_info: Dict) -> List[str]:
        """Gera sugestões SQL baseadas na intenção e capítulo."""
        chapter = chapter_info['chapter']
        range_start, range_end = chapter_info['range']

        suggestions = []

        if intent_type == 'count_cases':
            suggestions.extend([
                f"SELECT COUNT(*) FROM dados_sus3 WHERE DIAG_PRINC LIKE '{chapter}%'",
                f"SELECT COUNT(*) FROM dados_sus3 WHERE DIAG_PRINC >= '{range_start}' AND DIAG_PRINC <= '{range_end}'"
            ])

        elif intent_type == 'count_deaths':
            suggestions.extend([
                f"SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1 AND DIAG_PRINC LIKE '{chapter}%'",
                f"SELECT COUNT(*) FROM dados_sus3 WHERE MORTE = 1 AND DIAG_PRINC >= '{range_start}' AND DIAG_PRINC <= '{range_end}'"
            ])

        elif intent_type == 'count_admissions':
            suggestions.extend([
                f"SELECT COUNT(*) FROM dados_sus3 WHERE DIAG_PRINC LIKE '{chapter}%'",
                f"SELECT COUNT(*) FROM dados_sus3 WHERE DIAG_PRINC >= '{range_start}' AND DIAG_PRINC <= '{range_end}'"
            ])

        return suggestions

    def validate_sql_query(self, sql_query: str) -> Dict:
        """
        Valida uma query SQL para detectar erros comuns com CID.

        Args:
            sql_query: Query SQL para validar

        Returns:
            Dict com resultado da validação
        """
        sql_upper = sql_query.upper()

        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }

        # Erro crítico: usar CID_MORTE para contar casos/diagnósticos
        if 'CID_MORTE >' in sql_upper and 'MORTE = 1' not in sql_upper:
            validation['is_valid'] = False
            validation['errors'].append(
                "❌ ERRO: CID_MORTE é para CAUSAS DE MORTE, não diagnósticos de internação"
            )
            validation['suggestions'].append(
                "✅ Use DIAG_PRINC para diagnósticos da internação"
            )

        # Erro: buscar texto em campo de códigos
        if "DIAG_PRINC LIKE '%doenças%" in sql_upper or "DIAG_PRINC LIKE '%respirat%" in sql_upper:
            validation['is_valid'] = False
            validation['errors'].append(
                "❌ ERRO: DIAG_PRINC contém CÓDIGOS (ex: J128), não texto em português"
            )
            validation['suggestions'].append(
                "✅ Use DIAG_PRINC LIKE 'J%' para doenças respiratórias"
            )

        # Warning: usar CID_MORTE sem MORTE = 1
        if 'CID_MORTE' in sql_upper and 'MORTE' not in sql_upper:
            validation['warnings'].append(
                "⚠️ CID_MORTE só faz sentido quando MORTE = 1"
            )

        # Sugestão: melhorar eficiência
        if 'DIAG_PRINC >=' in sql_upper and 'DIAG_PRINC <=' in sql_upper:
            validation['suggestions'].append(
                "💡 Alternativa mais simples: DIAG_PRINC LIKE 'X%' onde X é a letra do capítulo"
            )

        return validation

    def generate_corrected_query(self, problematic_query: str, intent: str) -> str:
        """
        Gera query corrigida baseada em uma query problemática.

        Args:
            problematic_query: Query com problemas
            intent: Intenção detectada (ex: "doenças respiratórias")

        Returns:
            Query SQL corrigida
        """
        # Analisar intenção
        analysis = self.analyze_query_intent(intent)

        if analysis['sql_suggestions']:
            return analysis['sql_suggestions'][0]  # Primeira sugestão

        # Fallback genérico
        if 'respirat' in intent.lower():
            return "SELECT COUNT(*) FROM dados_sus3 WHERE DIAG_PRINC LIKE 'J%'"
        elif 'cardiovascular' in intent.lower() or 'cardí' in intent.lower():
            return "SELECT COUNT(*) FROM dados_sus3 WHERE DIAG_PRINC LIKE 'I%'"
        elif 'câncer' in intent.lower() or 'tumor' in intent.lower():
            return "SELECT COUNT(*) FROM dados_sus3 WHERE DIAG_PRINC LIKE 'C%'"

        return "SELECT COUNT(*) FROM dados_sus3"

    def get_explanation_for_code(self, code: str) -> str:
        """Gera explicação didática para um código CID."""
        interpretation = self.interpret_cid_code(code)

        if 'error' in interpretation:
            return f"❌ {interpretation['error']}"

        explanation = f"""
🔍 CÓDIGO CID-10: {code}

📋 Capítulo: {interpretation['chapter']} - {interpretation['chapter_name']}
📊 Faixa: {interpretation['range'][0]} a {interpretation['range'][1]}
🏷️  Palavras-chave: {', '.join(interpretation['keywords'])}

💾 Para usar em SQL:
   • Específico: DIAG_PRINC = '{code}'
   • Todo o capítulo: DIAG_PRINC LIKE '{interpretation['chapter']}%'
   • Faixa completa: DIAG_PRINC >= '{interpretation['range'][0]}' AND DIAG_PRINC <= '{interpretation['range'][1]}'

⚠️  LEMBRETE: 
   • DIAG_PRINC = diagnóstico da internação
   • CID_MORTE = causa da morte (só quando MORTE = 1)
        """

        return explanation.strip()

    def debug_query_flow(self, original_query: str, generated_sql: str) -> Dict:
        """Debug completo do fluxo de uma query."""
        return {
            'original_query': original_query,
            'intent_analysis': self.analyze_query_intent(original_query),
            'generated_sql': generated_sql,
            'sql_validation': self.validate_sql_query(generated_sql),
            'recommendations': self._get_debug_recommendations(original_query, generated_sql)
        }

    def _get_debug_recommendations(self, query: str, sql: str) -> List[str]:
        """Gera recomendações de debug."""
        recommendations = []

        if 'respirat' in query.lower() and 'J' not in sql.upper():
            recommendations.append("🔧 Para respiratórias, use DIAG_PRINC LIKE 'J%'")

        if 'morte' in query.lower() and 'MORTE = 1' not in sql.upper():
            recommendations.append("🔧 Para mortes, adicione MORTE = 1")

        if 'CID_MORTE' in sql.upper() and 'MORTE' not in sql.upper():
            recommendations.append("🔧 CID_MORTE só é válido com MORTE = 1")

        return recommendations


# Instância global
cid_interpreter = CIDInterpreter()