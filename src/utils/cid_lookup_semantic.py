"""
CIDLookup MELHORADO - Busca em CAPITULOS + CATEGORIAS
Implementa busca semantica nos dois arquivos CID para melhor cobertura.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
import re
from difflib import SequenceMatcher
import os

# Tentar importar sentence-transformers para embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("sentence-transformers nao disponivel. Usando busca textual avancada.")


class CIDLookup:
    """
    CIDLookup MELHORADO com busca em CAPITULOS + CATEGORIAS.

    CAPITULOS: Para termos gerais (respiratorias, cardiovasculares, etc.)
    CATEGORIAS: Para codigos especificos (pneumonia, asma, etc.)
    """

    def __init__(self,
                 capitulos_path: str = 'CID-10-CAPITULOS.CSV',
                 categorias_path: str = 'CID-10-CATEGORIAS.CSV'):
        """
        Inicializa com busca dupla nos dois arquivos CID.
        """
        self.capitulos_path = capitulos_path
        self.categorias_path = categorias_path

        # DataFrames para os dois tipos de dados
        self.capitulos_df = None
        self.categorias_df = None

        # Embeddings separados
        self.capitulos_embeddings = None
        self.categorias_embeddings = None
        self.model = None

        # Base hardcoded robusta baseada na analise real
        self.hardcoded_chapters = self._build_comprehensive_hardcoded_base()

        # Carregar ambos os arquivos
        self._load_capitulos_database()
        self._load_categorias_database()

        # Inicializar busca semantica se disponivel
        if EMBEDDINGS_AVAILABLE:
            self._initialize_semantic_search()

        print(f"CIDLookup MELHORADO inicializado:")
        print(f"   Capitulos: {'✅' if self.capitulos_df is not None else '❌'} ({len(self.capitulos_df) if self.capitulos_df is not None else 0} entradas)")
        print(f"   Categorias: {'✅' if self.categorias_df is not None else '❌'} ({len(self.categorias_df) if self.categorias_df is not None else 0} codigos)")
        print(f"   Semantic search: {'✅' if self.model else '❌'}")
        print(f"   Fallback hardcoded: ✅ ({len(self.hardcoded_chapters)} termos)")

    def _build_comprehensive_hardcoded_base(self) -> Dict[str, Tuple[str, str]]:
        """
        Base hardcoded ABRANGENTE baseada na estrutura real do CID-10.
        """
        return {
            # RESPIRATORIAS (J00-J99) - FOCO PRINCIPAL
            'respiratorias': ('J00', 'J99'),
            'respiratoria': ('J00', 'J99'),
            'respiratorio': ('J00', 'J99'),
            'aparelho respiratorio': ('J00', 'J99'),
            'vias respiratorias': ('J00', 'J99'),
            'sistema respiratorio': ('J00', 'J99'),
            'pulmao': ('J00', 'J99'),
            'pulmonar': ('J00', 'J99'),
            'pulmonares': ('J00', 'J99'),
            'broncos': ('J00', 'J99'),
            'bronquios': ('J00', 'J99'),

            # Termos especificos respiratorios
            'pneumonia': ('J12', 'J18'),
            'pneumonias': ('J12', 'J18'),
            'asma': ('J45', 'J46'),
            'bronquite': ('J20', 'J42'),
            'bronquites': ('J20', 'J42'),
            'gripe': ('J09', 'J11'),
            'influenza': ('J09', 'J11'),
            'resfriado': ('J00', 'J06'),
            'resfriados': ('J00', 'J06'),
            'sinusite': ('J01', 'J01'),
            'faringite': ('J02', 'J02'),
            'amigdalite': ('J03', 'J03'),
            'laringite': ('J04', 'J04'),
            'bronquite aguda': ('J20', 'J21'),
            'bronquite cronica': ('J40', 'J42'),
            'enfisema': ('J43', 'J43'),
            'doenca pulmonar obstrutiva': ('J44', 'J44'),
            'dpoc': ('J44', 'J44'),

            # CARDIOVASCULARES (I00-I99)
            'cardiovasculares': ('I00', 'I99'),
            'cardiovascular': ('I00', 'I99'),
            'cardiacas': ('I00', 'I99'),
            'coracao': ('I00', 'I99'),
            'cardiaco': ('I00', 'I99'),
            'sistema cardiovascular': ('I00', 'I99'),
            'aparelho cardiovascular': ('I00', 'I99'),
            'circulatorias': ('I00', 'I99'),
            'sistema circulatorio': ('I00', 'I99'),

            # NEOPLASIAS (C00-D49)
            'cancer': ('C00', 'D49'),
            'tumor': ('C00', 'D49'),
            'tumores': ('C00', 'D49'),
            'neoplasia': ('C00', 'D49'),
            'neoplasias': ('C00', 'D49'),
            'maligno': ('C00', 'C97'),
            'malignos': ('C00', 'C97'),
            'maligna': ('C00', 'C97'),
            'malignas': ('C00', 'C97'),
            'oncologicas': ('C00', 'D49'),

            # DIABETES E ENDOCRINAS (E00-E89)
            'diabetes': ('E10', 'E14'),
            'diabetica': ('E10', 'E14'),
            'diabetico': ('E10', 'E14'),
            'endocrinas': ('E00', 'E89'),
            'hormonal': ('E00', 'E89'),
            'hormonais': ('E00', 'E89'),
            'metabolicas': ('E00', 'E89'),

            # TRANSTORNOS MENTAIS (F00-F99)
            'mentais': ('F00', 'F99'),
            'mental': ('F00', 'F99'),
            'psiquiatrica': ('F00', 'F99'),
            'psiquiatricas': ('F00', 'F99'),
            'comportamentais': ('F00', 'F99'),
            'demencia': ('F00', 'F03'),
            'alzheimer': ('F00', 'F00'),
            'depressao': ('F32', 'F33'),

            # SISTEMA NERVOSO (G00-G99)
            'neurologicas': ('G00', 'G99'),
            'nervoso': ('G00', 'G99'),
            'sistema nervoso': ('G00', 'G99'),
            'neurologico': ('G00', 'G99'),

            # DOENCAS RENAIS (N00-N99)
            'renal': ('N00', 'N99'),
            'renais': ('N00', 'N99'),
            'rim': ('N00', 'N99'),
            'rins': ('N00', 'N99'),
            'sistema renal': ('N00', 'N99'),
            'aparelho urinario': ('N00', 'N99'),
            'urinarias': ('N00', 'N99'),

            # DIGESTIVAS (K00-K95)
            'digestivas': ('K00', 'K95'),
            'digestiva': ('K00', 'K95'),
            'digestorio': ('K00', 'K95'),
            'sistema digestivo': ('K00', 'K95'),
            'aparelho digestivo': ('K00', 'K95'),
            'gastrointestinais': ('K00', 'K95'),

            # MUSCULOESQUELETICAS (M00-M99)
            'osteomusculares': ('M00', 'M99'),
            'musculoesqueleticas': ('M00', 'M99'),
            'ossos': ('M00', 'M99'),
            'musculos': ('M00', 'M99'),
            'articulacoes': ('M00', 'M99'),

            # INFECCIOSAS (A00-B99)
            'infecciosas': ('A00', 'B99'),
            'parasitarias': ('A00', 'B99'),
            'contagiosas': ('A00', 'B99'),
        }

    def _load_capitulos_database(self):
        """Carrega dados do arquivo CID-10-CAPITULOS.CSV."""
        possible_paths = [
            self.capitulos_path,
            'data/CID-10-CAPITULOS.CSV',
            'CID-10-CAPITULOS.CSV',
            'CID10CAPITULOS.CSV',
            'data/CID10CAPITULOS.CSV'
        ]

        file_found = False
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    self.capitulos_df = pd.read_csv(
                        path,
                        delimiter=';',
                        encoding='latin1',
                        dtype=str
                    )
                    # Normalizar nomes das colunas
                    self.capitulos_df.columns = [col.upper().strip() for col in self.capitulos_df.columns]

                    # Limpar dados
                    required_cols = ['CATINIC', 'CATFIM', 'DESCRICAO']
                    if all(col in self.capitulos_df.columns for col in required_cols):
                        self.capitulos_df = self.capitulos_df.dropna(subset=required_cols)
                        file_found = True
                        print(f"Capitulos CID carregados: {len(self.capitulos_df)} entradas")
                        break
                    else:
                        print(f"Arquivo {path} nao tem colunas esperadas: {list(self.capitulos_df.columns)}")
                except Exception as e:
                    print(f"Erro ao carregar {path}: {e}")

        if not file_found:
            print("Arquivo CID-10-CAPITULOS.CSV nao encontrado")

    def _load_categorias_database(self):
        """Carrega dados do arquivo CID-10-CATEGORIAS.CSV."""
        possible_paths = [
            self.categorias_path,
            'data/CID-10-CATEGORIAS.CSV',
            'CID-10-CATEGORIAS.CSV',
            'CID10CATEGORIAS.CSV',
            'data/CID10CATEGORIAS.CSV'
        ]

        file_found = False
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    self.categorias_df = pd.read_csv(
                        path,
                        delimiter=';',
                        encoding='latin1',
                        dtype=str
                    )
                    # Normalizar nomes das colunas
                    self.categorias_df.columns = [col.upper().strip() for col in self.categorias_df.columns]

                    # Limpar dados
                    required_cols = ['CAT', 'DESCRICAO']
                    if all(col in self.categorias_df.columns for col in required_cols):
                        self.categorias_df = self.categorias_df.dropna(subset=required_cols)
                        file_found = True
                        print(f"Categorias CID carregadas: {len(self.categorias_df)} codigos")
                        break
                    else:
                        print(f"Arquivo {path} nao tem colunas esperadas: {list(self.categorias_df.columns)}")
                except Exception as e:
                    print(f"Erro ao carregar {path}: {e}")

        if not file_found:
            print("Arquivo CID-10-CATEGORIAS.CSV nao encontrado")

    def _initialize_semantic_search(self):
        """Inicializa busca semantica para ambos os datasets."""
        try:
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

            # Embeddings para capitulos
            if self.capitulos_df is not None:
                capitulos_texts = []
                for _, row in self.capitulos_df.iterrows():
                    text = f"{row.get('CATINIC', '')}-{row.get('CATFIM', '')} {row.get('DESCRICAO', '')}"
                    capitulos_texts.append(text)
                self.capitulos_embeddings = self.model.encode(capitulos_texts, show_progress_bar=False)
                print(f"Embeddings capitulos: {len(capitulos_texts)} textos")

            # Embeddings para categorias
            if self.categorias_df is not None:
                categorias_texts = []
                for _, row in self.categorias_df.iterrows():
                    text = f"{row.get('CAT', '')} {row.get('DESCRICAO', '')}"
                    categorias_texts.append(text)
                self.categorias_embeddings = self.model.encode(categorias_texts, show_progress_bar=False)
                print(f"Embeddings categorias: {len(categorias_texts)} textos")

        except Exception as e:
            print(f"Erro ao inicializar semantic search: {e}")
            self.model = None

    def find_cid_range(self, search_term: str) -> Optional[Tuple[str, str]]:
        """
        INTERFACE PRINCIPAL - Busca inteligente em multiplas fontes.

        Ordem de prioridade:
        1. Busca em CAPITULOS (para termos gerais como "respiratorias")
        2. Busca semantica em CATEGORIAS (para termos especificos)
        3. Busca textual em CATEGORIAS
        4. Fallback hardcoded
        """
        search_term_lower = search_term.lower().strip()
        print(f"Busca inteligente para: '{search_term}'")

        # 1. PRIORIDADE: Busca em CAPITULOS para termos gerais
        capitulos_result = self._search_in_capitulos(search_term_lower)
        if capitulos_result:
            print(f"Encontrado em CAPITULOS: {capitulos_result}")
            return capitulos_result

        # 2. Busca semantica em CATEGORIAS para termos especificos
        if self.model and self.categorias_embeddings is not None:
            semantic_result = self._semantic_search_categorias(search_term)
            if semantic_result:
                print(f"Encontrado via semantic search CATEGORIAS: {semantic_result}")
                return semantic_result

        # 3. Busca textual em CATEGORIAS
        if self.categorias_df is not None:
            textual_result = self._textual_search_categorias(search_term_lower)
            if textual_result:
                print(f"Encontrado via busca textual CATEGORIAS: {textual_result}")
                return textual_result

        # 4. Fallback hardcoded (sempre disponivel)
        hardcoded_result = self._hardcoded_search(search_term_lower)
        if hardcoded_result:
            print(f"Encontrado via hardcoded: {hardcoded_result}")
            return hardcoded_result

        print(f"Termo '{search_term}' nao encontrado em nenhuma fonte")
        return None

    def _search_in_capitulos(self, search_term: str) -> Optional[Tuple[str, str]]:
        """Busca especifica no arquivo de CAPITULOS."""
        if self.capitulos_df is None:
            return None

        # Busca semantica em capitulos (se disponivel)
        if self.model and self.capitulos_embeddings is not None:
            try:
                query_embedding = self.model.encode([search_term])
                similarities = np.dot(query_embedding, self.capitulos_embeddings.T).flatten()

                best_idx = np.argmax(similarities)
                best_similarity = similarities[best_idx]

                if best_similarity > 0.5:  # Threshold para capitulos
                    row = self.capitulos_df.iloc[best_idx]
                    start_cat = row.get('CATINIC', '')
                    end_cat = row.get('CATFIM', '')
                    desc = row.get('DESCRICAO', '')

                    print(f"Match semantico CAPITULOS: {start_cat}-{end_cat} ({desc}) sim:{best_similarity:.3f}")
                    return (start_cat, end_cat)
            except Exception as e:
                print(f"Erro busca semantica capitulos: {e}")

        # Busca textual em capitulos
        mask = self.capitulos_df['DESCRICAO'].str.lower().str.contains(search_term, na=False, regex=False)
        matches = self.capitulos_df[mask]

        if not matches.empty:
            row = matches.iloc[0]
            start_cat = row.get('CATINIC', '')
            end_cat = row.get('CATFIM', '')
            desc = row.get('DESCRICAO', '')
            print(f"Match textual CAPITULOS: {start_cat}-{end_cat} ({desc})")
            return (start_cat, end_cat)

        return None

    def _semantic_search_categorias(self, search_term: str) -> Optional[Tuple[str, str]]:
        """Busca semantica em CATEGORIAS."""
        try:
            query_embedding = self.model.encode([search_term])
            similarities = np.dot(query_embedding, self.categorias_embeddings.T).flatten()

            best_idx = np.argmax(similarities)
            best_similarity = similarities[best_idx]

            if best_similarity > 0.6:  # Threshold mais alto para categorias especificas
                row = self.categorias_df.iloc[best_idx]
                code = row.get('CAT', '')
                desc = row.get('DESCRICAO', '')

                print(f"Match semantico CATEGORIAS: {code} ({desc}) sim:{best_similarity:.3f}")
                return (code, code)

        except Exception as e:
            print(f"Erro busca semantica categorias: {e}")

        return None

    def _textual_search_categorias(self, search_term: str) -> Optional[Tuple[str, str]]:
        """Busca textual em CATEGORIAS."""
        # Busca exata
        mask = self.categorias_df['DESCRICAO'].str.lower().str.contains(search_term, na=False, regex=False)
        matches = self.categorias_df[mask]

        if not matches.empty:
            row = matches.iloc[0]
            code = row.get('CAT', '')
            desc = row.get('DESCRICAO', '')
            print(f"Match textual CATEGORIAS: {code} ({desc})")
            return (code, code)

        # Busca por palavras
        words = search_term.split()
        for word in words:
            if len(word) > 3:
                mask = self.categorias_df['DESCRICAO'].str.lower().str.contains(word, na=False, regex=False)
                matches = self.categorias_df[mask]

                if not matches.empty:
                    row = matches.iloc[0]
                    code = row.get('CAT', '')
                    desc = row.get('DESCRICAO', '')
                    print(f"Match palavra '{word}' CATEGORIAS: {code} ({desc})")
                    return (code, code)

        return None

    def _hardcoded_search(self, search_term: str) -> Optional[Tuple[str, str]]:
        """Busca hardcoded otimizada."""
        # Busca exata
        if search_term in self.hardcoded_chapters:
            return self.hardcoded_chapters[search_term]

        # Busca por substring
        for key, value in self.hardcoded_chapters.items():
            if search_term in key or key in search_term:
                return value

        # Busca por palavras
        words = search_term.split()
        for word in words:
            if len(word) > 3:
                for key, value in self.hardcoded_chapters.items():
                    if word in key or key in word:
                        return value

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Estatisticas completas das bases carregadas."""
        stats = {
            'has_capitulos': self.capitulos_df is not None,
            'has_categorias': self.categorias_df is not None,
            'has_semantic_search': self.model is not None,
            'total_hardcoded': len(self.hardcoded_chapters),
            'capitulos_count': len(self.capitulos_df) if self.capitulos_df is not None else 0,
            'categorias_count': len(self.categorias_df) if self.categorias_df is not None else 0,
        }

        if self.capitulos_df is not None:
            stats['capitulos_sample'] = self.capitulos_df.head(3).to_dict('records')

        if self.categorias_df is not None:
            # Contagem por capitulo
            chapter_counts = {}
            for _, row in self.categorias_df.iterrows():
                chapter = row.get('CAT', '')[:1] if row.get('CAT') else '?'
                chapter_counts[chapter] = chapter_counts.get(chapter, 0) + 1
            stats['chapters_distribution'] = chapter_counts

        return stats

    def debug_search(self, search_term: str) -> Dict[str, Any]:
        """Metodo para debug - mostra todos os passos da busca."""
        debug_info = {
            'search_term': search_term,
            'steps': [],
            'final_result': None
        }

        search_term_lower = search_term.lower().strip()

        # Testar cada metodo
        debug_info['steps'].append("Iniciando debug da busca")

        # 1. Capitulos
        capitulos_result = self._search_in_capitulos(search_term_lower)
        debug_info['steps'].append(f"Busca CAPITULOS: {capitulos_result}")

        # 2. Semantica em categorias
        if self.model and self.categorias_embeddings is not None:
            semantic_result = self._semantic_search_categorias(search_term)
            debug_info['steps'].append(f"Semantica CATEGORIAS: {semantic_result}")

        # 3. Textual em categorias
        if self.categorias_df is not None:
            textual_result = self._textual_search_categorias(search_term_lower)
            debug_info['steps'].append(f"Textual CATEGORIAS: {textual_result}")

        # 4. Hardcoded
        hardcoded_result = self._hardcoded_search(search_term_lower)
        debug_info['steps'].append(f"Hardcoded: {hardcoded_result}")

        # Resultado final
        debug_info['final_result'] = self.find_cid_range(search_term)

        return debug_info

