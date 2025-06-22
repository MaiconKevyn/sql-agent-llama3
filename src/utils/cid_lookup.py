"""
Versão melhorada do CIDLookup com mapeamento hardcoded dos principais capítulos.
"""

import pandas as pd
from typing import Optional, Tuple, Dict


class CIDLookup:
    """
    Ferramenta melhorada para consultar categorias CID-10 com fallback hardcoded.
    """

    def __init__(self, file_path: str = 'CID-10-CAPITULOS.CSV'):
        """
        Inicializa com dados hardcoded como fallback.
        """
        # Base de conhecimento hardcoded dos principais capítulos CID-10
        self.hardcoded_chapters = {
            # Doenças Respiratórias - Capítulo X (J00-J99)
            'respiratórias': ('J00', 'J99'),
            'respiratória': ('J00', 'J99'),
            'respiratorio': ('J00', 'J99'),
            'respiratoria': ('J00', 'J99'),
            'pulmão': ('J00', 'J99'),
            'pulmao': ('J00', 'J99'),
            'bronquite': ('J20', 'J42'),
            'pneumonia': ('J12', 'J18'),
            'asma': ('J45', 'J46'),
            'gripe': ('J09', 'J11'),
            'tuberculose': ('A15', 'A19'),  # Algumas infecções respiratórias estão em A

            # Doenças Cardiovasculares - Capítulo IX (I00-I99)
            'cardiovasculares': ('I00', 'I99'),
            'cardiovascular': ('I00', 'I99'),
            'cardíacas': ('I00', 'I99'),
            'cardiacas': ('I00', 'I99'),
            'coração': ('I00', 'I99'),
            'coracao': ('I00', 'I99'),
            'infarto': ('I21', 'I22'),
            'avc': ('I60', 'I69'),
            'hipertensão': ('I10', 'I15'),
            'hipertensao': ('I10', 'I15'),

            # Neoplasias - Capítulo II (C00-D49)
            'câncer': ('C00', 'D49'),
            'cancer': ('C00', 'D49'),
            'tumor': ('C00', 'D49'),
            'neoplasia': ('C00', 'D49'),
            'maligno': ('C00', 'C97'),

            # Doenças Digestivas - Capítulo XI (K00-K95)
            'digestivas': ('K00', 'K95'),
            'digestiva': ('K00', 'K95'),
            'estômago': ('K20', 'K31'),
            'estomago': ('K20', 'K31'),
            'fígado': ('K70', 'K77'),
            'figado': ('K70', 'K77'),

            # Doenças do Sistema Nervoso - Capítulo VI (G00-G99)
            'nervoso': ('G00', 'G99'),
            'neurológicas': ('G00', 'G99'),
            'neurologicas': ('G00', 'G99'),
            'alzheimer': ('F03', 'F03'),  # Está em F
            'parkinson': ('G20', 'G20'),

            # Doenças Endócrinas - Capítulo IV (E00-E89)
            'diabetes': ('E10', 'E14'),
            'diabética': ('E10', 'E14'),
            'diabetica': ('E10', 'E14'),
            'endócrinas': ('E00', 'E89'),
            'endocrinas': ('E00', 'E89'),

            # Transtornos Mentais - Capítulo V (F00-F99)
            'mentais': ('F00', 'F99'),
            'mental': ('F00', 'F99'),
            'psiquiátrica': ('F00', 'F99'),
            'psiquiatrica': ('F00', 'F99'),
            'depressão': ('F32', 'F39'),
            'depressao': ('F32', 'F39'),

            # Doenças Renais - Capítulo XIV (N00-N99)
            'renal': ('N00', 'N99'),
            'renais': ('N00', 'N99'),
            'rim': ('N00', 'N99'),
            'rins': ('N00', 'N99'),
            'urinário': ('N00', 'N99'),
            'urinario': ('N00', 'N99'),

            # Causas Externas - Capítulo XX (V01-Y98)
            'acidente': ('V01', 'Y98'),
            'acidentes': ('V01', 'Y98'),
            'violência': ('X85', 'Y09'),
            'violencia': ('X85', 'Y09'),
            'suicídio': ('X60', 'X84'),
            'suicidio': ('X60', 'X84'),
        }

        # Tentar carregar arquivo CSV se existir
        self.cid_df = None
        try:
            self.cid_df = pd.read_csv(
                file_path,
                delimiter=';',
                encoding='latin-1'
            )
            if not self.cid_df.empty:
                self.cid_df.columns = [col.upper() for col in self.cid_df.columns]
                print("✅ Arquivo CID-10 carregado com sucesso como fonte primária.")
            else:
                print("⚠️ Arquivo CID-10 vazio, usando base hardcoded.")
                self.cid_df = None
        except FileNotFoundError:
            print(f"⚠️ Arquivo CID '{file_path}' não encontrado, usando base hardcoded.")
            self.cid_df = None
        except Exception as e:
            print(f"⚠️ Erro ao carregar arquivo CID: {e}. Usando base hardcoded.")
            self.cid_df = None

        print(f"📚 Base de conhecimento CID inicializada com {len(self.hardcoded_chapters)} categorias.")

    def find_cid_range(self, search_term: str) -> Optional[Tuple[str, str]]:
        """
        Procura por um termo e retorna o range de códigos CID.
        Usa hardcoded como fallback se arquivo não estiver disponível.
        """
        search_term_lower = search_term.lower().strip()

        # 1. Tentar busca no arquivo CSV primeiro (se disponível)
        if self.cid_df is not None and not self.cid_df.empty:
            try:
                mask = self.cid_df['DESCRICAO'].str.lower().str.contains(search_term_lower, na=False)
                result_df = self.cid_df[mask]

                if not result_df.empty:
                    first_match = result_df.iloc[0]
                    cat_inic = first_match['CATINIC']
                    cat_fim = first_match['CATFIM']
                    print(f"✅ Encontrado no arquivo CSV: {search_term} -> {cat_inic}-{cat_fim}")
                    return (cat_inic, cat_fim)
            except Exception as e:
                print(f"⚠️ Erro na busca CSV: {e}. Tentando hardcoded.")

        # 2. Busca exata na base hardcoded
        if search_term_lower in self.hardcoded_chapters:
            result = self.hardcoded_chapters[search_term_lower]
            print(f"✅ Encontrado hardcoded (exato): {search_term} -> {result[0]}-{result[1]}")
            return result

        # 3. Busca parcial na base hardcoded
        for key, value in self.hardcoded_chapters.items():
            if search_term_lower in key or key in search_term_lower:
                print(f"✅ Encontrado hardcoded (parcial): {search_term} -> {value[0]}-{value[1]} (via '{key}')")
                return value

        # 4. Busca por palavras individuais
        words = search_term_lower.split()
        for word in words:
            if len(word) > 3:  # Evitar palavras muito curtas
                for key, value in self.hardcoded_chapters.items():
                    if word in key:
                        print(
                            f"✅ Encontrado hardcoded (palavra): {search_term} -> {value[0]}-{value[1]} (via '{word}' em '{key}')")
                        return value

        print(f"❌ Termo '{search_term}' não encontrado na base de conhecimento.")
        return None

    def get_available_categories(self) -> Dict[str, Tuple[str, str]]:
        """
        Retorna todas as categorias disponíveis.
        """
        return self.hardcoded_chapters.copy()

    def search_suggestions(self, search_term: str) -> list:
        """
        Sugere termos similares quando a busca falha.
        """
        search_term_lower = search_term.lower()
        suggestions = []

        for key in self.hardcoded_chapters.keys():
            # Busca por subsequências comuns
            if any(word in key for word in search_term_lower.split() if len(word) > 2):
                suggestions.append(key)

        return suggestions[:5]  # Limitar a 5 sugestões


# Testador para verificar se está funcionando
if __name__ == "__main__":
    lookup = CIDLookup()

    test_terms = [
        "respiratórias", "respiratória", "pulmão", "pneumonia",
        "cardiovasculares", "coração", "infarto",
        "diabetes", "câncer", "tumor"
    ]

    print("\n🧪 TESTANDO MAPEAMENTOS:")
    print("=" * 50)

    for term in test_terms:
        result = lookup.find_cid_range(term)
        if result:
            print(f"✅ {term}: {result[0]}-{result[1]}")
        else:
            suggestions = lookup.search_suggestions(term)
            print(f"❌ {term}: não encontrado")
            if suggestions:
                print(f"   💡 Sugestões: {', '.join(suggestions)}")