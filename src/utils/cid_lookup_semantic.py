"""
CIDLookup com busca semântica - mantém mesma interface, adiciona inteligência.
Mudanças mínimas no código existente, máximo ganho de funcionalidade.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict
import re
from difflib import SequenceMatcher

# Tentar importar sentence-transformers para embeddings
try:
    from sentence_transformers import SentenceTransformer

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ sentence-transformers não disponível. Usando busca por similaridade textual.")


class CIDLookup:
    """
    CIDLookup melhorado com busca semântica.
    Mantém a mesma interface, mas adiciona inteligência semântica.
    """

    def __init__(self, file_path: str = 'CID-10-CAPITULOS.CSV'):
        """
        Inicializa com busca semântica se disponível, senão usa similarity textual.
        """
        self.cid_df = None
        self.cid_codes_df = None
        self.embeddings = None
        self.model = None

        # Base hardcoded como último fallback (mantém compatibilidade)
        self.hardcoded_chapters = self._build_hardcoded_base()

        # Tentar carregar base CID-10 completa
        self._load_cid_database()

        # Inicializar busca semântica se disponível
        if EMBEDDINGS_AVAILABLE and self.cid_codes_df is not None:
            self._initialize_semantic_search()

        print(f"📚 CIDLookup inicializado:")
        print(f"   🔍 Semantic search: {'✅' if self.model else '❌'}")
        print(f"   📋 Base CID completa: {'✅' if self.cid_codes_df is not None else '❌'}")
        print(f"   🔄 Fallback hardcoded: ✅ ({len(self.hardcoded_chapters)} categorias)")

    def _build_hardcoded_base(self) -> Dict[str, Tuple[str, str]]:
        """Mantém base hardcoded como fallback - exatamente igual ao anterior."""
        return {
            # Respiratórias
            'respiratórias': ('J00', 'J99'), 'respiratória': ('J00', 'J99'),
            'respiratorio': ('J00', 'J99'), 'pulmão': ('J00', 'J99'),
            'pneumonia': ('J12', 'J18'), 'asma': ('J45', 'J46'),
            'bronquite': ('J20', 'J42'), 'gripe': ('J09', 'J11'),

            # Cardiovasculares
            'cardiovasculares': ('I00', 'I99'), 'cardíacas': ('I00', 'I99'),
            'coração': ('I00', 'I99'), 'infarto': ('I21', 'I22'),
            'avc': ('I60', 'I69'), 'hipertensão': ('I10', 'I15'),

            # Outras categorias principais
            'câncer': ('C00', 'D49'), 'cancer': ('C00', 'D49'),
            'diabetes': ('E10', 'E14'), 'renal': ('N00', 'N99'),
            'digestivas': ('K00', 'K95'), 'mentais': ('F00', 'F99'),
            'neurológicas': ('G00', 'G99'), 'endócrinas': ('E00', 'E89')
        }

    def _load_cid_database(self):
        """
        Carrega base CID-10 completa ou cria uma simulada.
        """
        try:
            # Tentar carregar arquivo real
            self.cid_df = pd.read_csv('CID-10-CAPITULOS.CSV', delimiter=';', encoding='latin-1')
            if not self.cid_df.empty:
                self.cid_df.columns = [col.upper() for col in self.cid_df.columns]
                print("✅ Arquivo CID-10-CAPITULOS carregado com sucesso")
        except:
            print("⚠️ Arquivo CID-10-CAPITULOS não encontrado, usando base simulada")

        # Criar ou carregar base de códigos específicos para busca semântica
        self.cid_codes_df = self._create_cid_codes_database()

    def _create_cid_codes_database(self) -> pd.DataFrame:
        """
        Cria base de códigos CID específicos com descrições.
        Simula uma base real ou carrega de arquivo.
        """

        # Base simulada com códigos reais CID-10 mais comuns
        cid_data = [
            # Respiratórias (J00-J99)
            {"codigo": "J00", "descricao": "Nasofaringite aguda (resfriado comum)"},
            {"codigo": "J06", "descricao": "Infecções agudas das vias aéreas superiores"},
            {"codigo": "J09", "descricao": "Influenza devida a vírus identificado da gripe aviária"},
            {"codigo": "J10", "descricao": "Influenza devida a outros vírus da gripe identificados"},
            {"codigo": "J11", "descricao": "Influenza devida a vírus não identificado"},
            {"codigo": "J12", "descricao": "Pneumonia viral não classificada em outra parte"},
            {"codigo": "J13", "descricao": "Pneumonia devida a Streptococcus pneumoniae"},
            {"codigo": "J14", "descricao": "Pneumonia devida a Haemophilus influenzae"},
            {"codigo": "J15", "descricao": "Pneumonia bacteriana não classificada em outra parte"},
            {"codigo": "J18", "descricao": "Pneumonia por microorganismo não especificado"},
            {"codigo": "J20", "descricao": "Bronquite aguda"},
            {"codigo": "J21", "descricao": "Bronquiolite aguda"},
            {"codigo": "J22", "descricao": "Infecção aguda não especificada das vias aéreas inferiores"},
            {"codigo": "J40", "descricao": "Bronquite não especificada como aguda ou crônica"},
            {"codigo": "J41", "descricao": "Bronquite crônica simples e a mucopurulenta"},
            {"codigo": "J42", "descricao": "Bronquite crônica não especificada"},
            {"codigo": "J43", "descricao": "Enfisema"},
            {"codigo": "J44", "descricao": "Outras doenças pulmonares obstrutivas crônicas"},
            {"codigo": "J45", "descricao": "Asma"},
            {"codigo": "J46", "descricao": "Estado de mal asmático"},

            # Cardiovasculares (I00-I99)
            {"codigo": "I10", "descricao": "Hipertensão essencial"},
            {"codigo": "I11", "descricao": "Doença cardíaca hipertensiva"},
            {"codigo": "I20", "descricao": "Angina pectoris"},
            {"codigo": "I21", "descricao": "Infarto agudo do miocárdio"},
            {"codigo": "I22", "descricao": "Infarto do miocárdio subseqüente"},
            {"codigo": "I25", "descricao": "Doença isquêmica crônica do coração"},
            {"codigo": "I50", "descricao": "Insuficiência cardíaca"},
            {"codigo": "I60", "descricao": "Hemorragia subaracnóide"},
            {"codigo": "I61", "descricao": "Hemorragia intracerebral"},
            {"codigo": "I63", "descricao": "Infarto cerebral"},
            {"codigo": "I64", "descricao": "Acidente vascular cerebral não especificado"},

            # Neoplasias (C00-D49)
            {"codigo": "C50", "descricao": "Neoplasia maligna da mama"},
            {"codigo": "C78", "descricao": "Neoplasia maligna secundária dos órgãos respiratórios e digestivos"},
            {"codigo": "C80", "descricao": "Neoplasia maligna sem especificação de localização"},

            # Diabetes (E10-E14)
            {"codigo": "E10", "descricao": "Diabetes mellitus insulino-dependente"},
            {"codigo": "E11", "descricao": "Diabetes mellitus não-insulino-dependente"},
            {"codigo": "E14", "descricao": "Diabetes mellitus não especificado"},

            # Exemplos de outros capítulos
            {"codigo": "F32", "descricao": "Episódios depressivos"},
            {"codigo": "G20", "descricao": "Doença de Parkinson"},
            {"codigo": "K25", "descricao": "Úlcera gástrica"},
            {"codigo": "N18", "descricao": "Doença renal crônica"},
        ]

        df = pd.DataFrame(cid_data)
        print(f"✅ Base CID específica criada com {len(df)} códigos")
        return df

    def _initialize_semantic_search(self):
        """
        Inicializa modelo de embeddings para busca semântica.
        """
        try:
            print("🔄 Carregando modelo de embeddings...")
            # Usar modelo multilíngue e compacto
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

            # Gerar embeddings das descrições CID
            descriptions = self.cid_codes_df['descricao'].tolist()
            self.embeddings = self.model.encode(descriptions)

            print(f"✅ Semantic search inicializado com {len(descriptions)} códigos")

        except Exception as e:
            print(f"❌ Erro ao inicializar semantic search: {e}")
            self.model = None
            self.embeddings = None

    def find_cid_range(self, search_term: str) -> Optional[Tuple[str, str]]:
        """
        MESMA INTERFACE - Busca semântica primeiro, fallback depois.
        """
        search_term_lower = search_term.lower().strip()
        print(f"🔍 Buscando: '{search_term}'")

        # 1. BUSCA SEMÂNTICA (se disponível)
        if self.model and self.embeddings is not None:
            semantic_result = self._semantic_search(search_term)
            if semantic_result:
                print(f"✅ Encontrado via semantic search: {semantic_result}")
                return semantic_result

        # 2. BUSCA TEXTUAL na base CID específica
        if self.cid_codes_df is not None:
            textual_result = self._textual_search(search_term_lower)
            if textual_result:
                print(f"✅ Encontrado via busca textual: {textual_result}")
                return textual_result

        # 3. BUSCA HARDCODED (fallback original)
        hardcoded_result = self._hardcoded_search(search_term_lower)
        if hardcoded_result:
            print(f"✅ Encontrado via hardcoded: {hardcoded_result}")
            return hardcoded_result

        print(f"❌ Termo '{search_term}' não encontrado")
        return None

    def _semantic_search(self, search_term: str, top_k: int = 3, threshold: float = 0.6) -> Optional[Tuple[str, str]]:
        """
        Busca semântica usando embeddings.
        """
        try:
            # Gerar embedding da query
            query_embedding = self.model.encode([search_term])

            # Calcular similaridades
            similarities = np.dot(query_embedding, self.embeddings.T).flatten()

            # Pegar os top_k mais similares
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            best_similarity = similarities[top_indices[0]]

            if best_similarity > threshold:
                best_match_idx = top_indices[0]
                matched_code = self.cid_codes_df.iloc[best_match_idx]['codigo']
                matched_desc = self.cid_codes_df.iloc[best_match_idx]['descricao']

                print(f"   🎯 Melhor match: {matched_code} - {matched_desc}")
                print(f"   📊 Similaridade: {best_similarity:.3f}")

                # Retornar código específico como range
                return (matched_code, matched_code)

        except Exception as e:
            print(f"   ❌ Erro na busca semântica: {e}")

        return None

    def _textual_search(self, search_term: str) -> Optional[Tuple[str, str]]:
        """
        Busca textual na base de códigos específicos.
        """
        if self.cid_codes_df is None:
            return None

        # Busca por substring na descrição
        mask = self.cid_codes_df['descricao'].str.lower().str.contains(search_term, na=False)
        matches = self.cid_codes_df[mask]

        if not matches.empty:
            best_match = matches.iloc[0]  # Pegar o primeiro match
            code = best_match['codigo']
            desc = best_match['descricao']
            print(f"   🎯 Match textual: {code} - {desc}")
            return (code, code)

        # Busca por similaridade de string se não encontrou substring
        best_similarity = 0
        best_code = None

        for _, row in self.cid_codes_df.iterrows():
            similarity = SequenceMatcher(None, search_term, row['descricao'].lower()).ratio()
            if similarity > best_similarity and similarity > 0.4:  # threshold mínimo
                best_similarity = similarity
                best_code = row['codigo']

        if best_code:
            print(f"   🎯 Match por similaridade: {best_code} (sim: {best_similarity:.3f})")
            return (best_code, best_code)

        return None

    def _hardcoded_search(self, search_term: str) -> Optional[Tuple[str, str]]:
        """
        Busca hardcoded original (mantido como fallback).
        """
        # Busca exata
        if search_term in self.hardcoded_chapters:
            return self.hardcoded_chapters[search_term]

        # Busca parcial
        for key, value in self.hardcoded_chapters.items():
            if search_term in key or key in search_term:
                return value

        # Busca por palavras
        words = search_term.split()
        for word in words:
            if len(word) > 3:
                for key, value in self.hardcoded_chapters.items():
                    if word in key:
                        return value

        return None

    def search_detailed(self, search_term: str, max_results: int = 5) -> List[Dict]:
        """
        NOVA FUNÇÃO: Retorna resultados detalhados da busca semântica.
        """
        results = []

        if self.model and self.embeddings is not None:
            try:
                query_embedding = self.model.encode([search_term])
                similarities = np.dot(query_embedding, self.embeddings.T).flatten()

                # Top resultados
                top_indices = np.argsort(similarities)[-max_results:][::-1]

                for idx in top_indices:
                    if similarities[idx] > 0.3:  # threshold mínimo
                        row = self.cid_codes_df.iloc[idx]
                        results.append({
                            'codigo': row['codigo'],
                            'descricao': row['descricao'],
                            'similaridade': float(similarities[idx])
                        })

            except Exception as e:
                print(f"Erro na busca detalhada: {e}")

        return results

    # Mantém métodos existentes para compatibilidade
    def get_available_categories(self) -> Dict[str, Tuple[str, str]]:
        """Retorna categorias hardcoded (compatibilidade)."""
        return self.hardcoded_chapters.copy()

    def search_suggestions(self, search_term: str) -> List[str]:
        """Sugestões melhoradas usando semantic search."""
        if self.model:
            detailed_results = self.search_detailed(search_term, max_results=3)
            return [f"{r['codigo']}: {r['descricao']}" for r in detailed_results]
        else:
            # Fallback original
            suggestions = []
            search_term_lower = search_term.lower()
            for key in self.hardcoded_chapters.keys():
                if any(word in key for word in search_term_lower.split() if len(word) > 2):
                    suggestions.append(key)
            return suggestions[:5]


# Demonstração e teste
def demonstrar_melhorias():
    """
    Demonstra as melhorias da busca semântica vs. hardcoded.
    """
    print("🧪 DEMONSTRAÇÃO: BUSCA SEMÂNTICA vs HARDCODED")
    print("=" * 60)

    lookup = CIDLookup()

    test_cases = [
        # Casos que semantic search resolve melhor
        "falta de ar",  # → J44 (DPOC) via semantic, vs genérico J00-J99
        "dor no peito",  # → I20 (angina) via semantic
        "tosse persistente",  # → J40 (bronquite) via semantic
        "pressão alta",  # → I10 (hipertensão) via semantic
        "açúcar no sangue",  # → E11 (diabetes) via semantic

        # Casos que ambos funcionam
        "pneumonia",  # Ambos funcionam
        "asma",  # Ambos funcionam
        "diabetes",  # Ambos funcionam

        # Casos edge
        "covid",  # Teste para novos termos
        "depressão",  # Teste para saúde mental
    ]

    for term in test_cases:
        print(f"\n🔍 Testando: '{term}'")
        print("-" * 30)

        result = lookup.find_cid_range(term)
        if result:
            print(f"✅ Resultado: {result[0]}-{result[1]}")

            # Mostrar detalhes se semantic search disponível
            if lookup.model:
                detailed = lookup.search_detailed(term, max_results=2)
                for detail in detailed:
                    print(f"   📋 {detail['codigo']}: {detail['descricao']} (sim: {detail['similaridade']:.3f})")
        else:
            print("❌ Não encontrado")


if __name__ == "__main__":
    demonstrar_melhorias()