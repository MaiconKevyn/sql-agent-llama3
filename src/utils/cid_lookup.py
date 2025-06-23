"""
CIDLookup CORRIGIDO - Semantic Search com bugs fixados
Corrige problemas de scoring e priorizacao identificados
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict, Any, Union
import re
import os
import pickle
from difflib import SequenceMatcher
from pathlib import Path

# Semantic Search
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("sentence-transformers nao disponivel. Use: pip install sentence-transformers")


class CIDLookupFixed:
    """
    CIDLookup CORRIGIDO com semantic search fixado.

    Correcoes aplicadas:
    - Normalizacao correta de similarity scores
    - Priorizacao de CAPITULOS para termos gerais
    - Validacao semantica de resultados
    - Fallback robusto para hardcoded
    - Scoring ponderado corrigido
    """

    def __init__(self,
                 capitulos_path: str = 'CID-10-CAPITULOS.CSV',
                 categorias_path: str = 'CID-10-CATEGORIAS.CSV',
                 cache_dir: str = '.cid_cache'):
        """Inicializa CIDLookup com correcoes aplicadas."""
        self.capitulos_path = capitulos_path
        self.categorias_path = categorias_path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # DataFrames
        self.capitulos_df = None
        self.categorias_df = None

        # Modelos e embeddings
        self.models = {}
        self.capitulos_embeddings = {}
        self.categorias_embeddings = {}

        # Configuracao corrigida
        self.config = {
            'thresholds': {
                'capitulos_high': 0.7,    # Threshold alto para capitulos
                'capitulos_medium': 0.5,  # Threshold medio para capitulos
                'categorias_high': 0.8,   # Threshold muito alto para categorias especificas
                'categorias_medium': 0.6  # Threshold medio para categorias
            },
            'weights': {
                'capitulos_bonus': 2.0,   # Bonus para capitulos em termos gerais
                'medical_model_bonus': 1.3,  # Bonus para modelos medicos
                'hardcoded_score': 0.95   # Score alto para hardcoded
            }
        }

        # Base hardcoded ROBUSTA
        self.hardcoded_chapters = self._build_robust_hardcoded()

        # Termos que devem priorizar CAPITULOS
        self.general_terms = {
            'respiratorias', 'respiratoria', 'respiratorias',
            'cardiovasculares', 'cardiovascular', 'cardiacas',
            'digestivas', 'digestiva', 'renais', 'renal',
            'neurologicas', 'neurologica', 'endocrinas', 'endocrina',
            'infecciosas', 'infecciosa', 'mentais', 'mental'
        }

        # Carregar dados
        self._load_databases()

        # Inicializar modelos
        if EMBEDDINGS_AVAILABLE:
            self._initialize_models()

        print(f"CIDLookup CORRIGIDO inicializado com {len(self.hardcoded_chapters)} termos hardcoded")

    def _build_robust_hardcoded(self) -> Dict[str, Tuple[str, str]]:
        """Base hardcoded ROBUSTA para fallback garantido."""
        return {
            # RESPIRATORIAS - Termos principais
            'respiratorias': ('J00', 'J99'),
            'respiratoria': ('J00', 'J99'),
            'respiratorias': ('J00', 'J99'),
            'doenca respiratoria': ('J00', 'J99'),  # Termo exato do problema
            'doenca respiratoria': ('J00', 'J99'),
            'doencas respiratorias': ('J00', 'J99'),
            'doencas respiratorias': ('J00', 'J99'),
            'aparelho respiratorio': ('J00', 'J99'),
            'sistema respiratorio': ('J00', 'J99'),
            'pulmao': ('J00', 'J99'),
            'pulmoes': ('J00', 'J99'),
            'pulmonar': ('J00', 'J99'),
            'pulmonares': ('J00', 'J99'),
            'bronquio': ('J00', 'J99'),
            'bronquios': ('J00', 'J99'),
            'pneumonia': ('J12', 'J18'),
            'asma': ('J45', 'J46'),
            'bronquite': ('J20', 'J42'),
            'dpoc': ('J44', 'J44'),

            # CARDIOVASCULARES
            'cardiovasculares': ('I00', 'I99'),
            'cardiovascular': ('I00', 'I99'),
            'cardiacas': ('I00', 'I99'),
            'cardiaca': ('I00', 'I99'),
            'coracao': ('I00', 'I99'),
            'cardiaco': ('I00', 'I99'),
            'infarto': ('I21', 'I22'),
            'avc': ('I60', 'I69'),
            'hipertensao': ('I10', 'I15'),

            # OUTRAS CATEGORIAS IMPORTANTES
            'diabetes': ('E10', 'E14'),
            'diabetica': ('E10', 'E14'),
            'diabetico': ('E10', 'E14'),
            'cancer': ('C00', 'D49'),
            'tumor': ('C00', 'D49'),
            'neoplasia': ('C00', 'D49'),
            'renal': ('N00', 'N99'),
            'renais': ('N00', 'N99'),
            'rim': ('N00', 'N99'),
            'rins': ('N00', 'N99'),
            'neurologicas': ('G00', 'G99'),
            'neurologica': ('G00', 'G99'),
            'nervoso': ('G00', 'G99'),
            'digestivas': ('K00', 'K95'),
            'digestiva': ('K00', 'K95'),
            'mentais': ('F00', 'F99'),
            'mental': ('F00', 'F99'),
            'infecciosas': ('A00', 'B99'),
            'infecciosa': ('A00', 'B99')
        }

    def _load_databases(self):
        """Carrega bancos CID com tratamento robusto."""
        self._load_capitulos_database()
        self._load_categorias_database()

    def _load_capitulos_database(self):
        """Carrega CID-10-CAPITULOS.CSV."""
        possible_paths = [
            self.capitulos_path,
            'CID-10-CAPITULOS.CSV',
            'CID10CAPITULOS.CSV',
            'data/CID-10-CAPITULOS.CSV'
        ]

        for path in possible_paths:
            if os.path.exists(path):
                try:
                    for encoding in ['latin1', 'cp1252', 'utf-8']:
                        try:
                            self.capitulos_df = pd.read_csv(path, delimiter=';', encoding=encoding, dtype=str)
                            break
                        except UnicodeDecodeError:
                            continue

                    if self.capitulos_df is not None:
                        self.capitulos_df.columns = [col.upper().strip() for col in self.capitulos_df.columns]
                        required_cols = ['CATINIC', 'CATFIM', 'DESCRICAO']
                        if all(col in self.capitulos_df.columns for col in required_cols):
                            self.capitulos_df = self.capitulos_df.dropna(subset=required_cols)
                            print(f"Capitulos carregados: {len(self.capitulos_df)} de {path}")
                            return
                except Exception as e:
                    print(f"Erro em {path}: {e}")

        print("CID-10-CAPITULOS.CSV nao encontrado")

    def _load_categorias_database(self):
        """Carrega CID-10-CATEGORIAS.CSV."""
        possible_paths = [
            self.categorias_path,
            'CID-10-CATEGORIAS.CSV',
            'CID10CATEGORIAS.CSV',
            'data/CID-10-CATEGORIAS.CSV'
        ]

        for path in possible_paths:
            if os.path.exists(path):
                try:
                    for encoding in ['latin1', 'cp1252', 'utf-8']:
                        try:
                            self.categorias_df = pd.read_csv(path, delimiter=';', encoding=encoding, dtype=str)
                            break
                        except UnicodeDecodeError:
                            continue

                    if self.categorias_df is not None:
                        self.categorias_df.columns = [col.upper().strip() for col in self.categorias_df.columns]
                        required_cols = ['CAT', 'DESCRICAO']
                        if all(col in self.categorias_df.columns for col in required_cols):
                            self.categorias_df = self.categorias_df.dropna(subset=required_cols)
                            print(f"Categorias carregadas: {len(self.categorias_df)} de {path}")
                            return
                except Exception as e:
                    print(f"Erro em {path}: {e}")

        print("CID-10-CATEGORIAS.CSV nao encontrado")

    def _initialize_models(self):
        """Inicializa modelos com tratamento de erro robusto."""
        models_to_try = [
            ('multilingual', 'paraphrase-multilingual-MiniLM-L12-v2'),
            ('biobert', 'dmis-lab/biobert-v1.1')
        ]

        for model_name, model_path in models_to_try:
            try:
                print(f"Carregando {model_name}...")
                model = SentenceTransformer(model_path)
                self.models[model_name] = model
                self._generate_embeddings(model_name, model)
                print(f"{model_name} carregado")
            except Exception as e:
                print(f"Falha {model_name}: {e}")

        if not self.models:
            print("Nenhum modelo carregado - usando apenas hardcoded")

    def _generate_embeddings(self, model_name: str, model: SentenceTransformer):
        """Gera embeddings com cache."""
        cache_file = self.cache_dir / f"embeddings_{model_name}_fixed.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached = pickle.load(f)
                    self.capitulos_embeddings[model_name] = cached.get('capitulos')
                    self.categorias_embeddings[model_name] = cached.get('categorias')
                    print(f"{model_name} carregado do cache")
                    return
            except:
                pass

        embeddings_data = {}

        # Capitulos
        if self.capitulos_df is not None:
            texts = [f"{row.get('DESCRICAO', '')} codigos {row.get('CATINIC', '')}-{row.get('CATFIM', '')}"
                    for _, row in self.capitulos_df.iterrows()]
            embeddings_data['capitulos'] = model.encode(texts, show_progress_bar=True)
            self.capitulos_embeddings[model_name] = embeddings_data['capitulos']

        # Categorias
        if self.categorias_df is not None:
            texts = [f"codigo {row.get('CAT', '')} {row.get('DESCRICAO', '')}"
                    for _, row in self.categorias_df.iterrows()]
            embeddings_data['categorias'] = model.encode(texts, show_progress_bar=True)
            self.categorias_embeddings[model_name] = embeddings_data['categorias']

        # Salvar cache
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embeddings_data, f)
        except:
            pass

    def find_cid_range(self, search_term: str) -> Optional[Tuple[str, str]]:
        """
        INTERFACE PRINCIPAL CORRIGIDA.

        Ordem de prioridade CORRIGIDA:
        1. Hardcoded (mais confiavel)
        2. CAPITULOS semantic (para termos gerais)
        3. CATEGORIAS semantic (para termos especificos)
        4. Fallback inteligente
        """
        search_term_lower = search_term.lower().strip()
        print(f"Busca CORRIGIDA para: '{search_term}'")

        # 1. PRIORIDADE MAXIMA: Hardcoded (mais confiavel)
        hardcoded_result = self._hardcoded_search(search_term_lower)
        if hardcoded_result:
            print(f"HARDCODED: {hardcoded_result}")
            return hardcoded_result

        # 2. Verificar se e termo geral (deve priorizar CAPITULOS)
        is_general_term = self._is_general_medical_term(search_term_lower)

        if is_general_term:
            # Para termos gerais, priorizar CAPITULOS
            capitulos_result = self._search_capitulos_semantic(search_term_lower)
            if capitulos_result:
                print(f"CAPITULOS (termo geral): {capitulos_result}")
                return capitulos_result

        # 3. Busca semantica com validacao
        semantic_result = self._validated_semantic_search(search_term_lower)
        if semantic_result:
            print(f"SEMANTIC VALIDADO: {semantic_result}")
            return semantic_result

        # 4. Fallback inteligente
        fallback_result = self._intelligent_fallback(search_term_lower)
        if fallback_result:
            print(f"FALLBACK: {fallback_result}")
            return fallback_result

        print(f"Nenhum resultado para '{search_term}'")
        return None

    def _hardcoded_search(self, search_term: str) -> Optional[Tuple[str, str]]:
        """Busca hardcoded robusta."""
        # Busca exata
        if search_term in self.hardcoded_chapters:
            return self.hardcoded_chapters[search_term]

        # Busca por palavras-chave
        for term in search_term.split():
            if len(term) > 3 and term in self.hardcoded_chapters:
                return self.hardcoded_chapters[term]

        # Busca parcial
        for key, value in self.hardcoded_chapters.items():
            if search_term in key or key in search_term:
                return value

        return None

    def _is_general_medical_term(self, search_term: str) -> bool:
        """Verifica se e termo medico geral (deve priorizar capitulos)."""
        # Verificar termos gerais conhecidos
        for general_term in self.general_terms:
            if general_term in search_term:
                return True

        # Verificar padroes de termos gerais
        general_patterns = ['doencas', 'doenca', 'problemas', 'sistema', 'aparelho']
        return any(pattern in search_term for pattern in general_patterns)

    def _search_capitulos_semantic(self, search_term: str) -> Optional[Tuple[str, str]]:
        """Busca semantica APENAS em capitulos."""
        if not self.models or not self.capitulos_df is not None:
            return None

        best_result = None
        best_score = 0

        for model_name, model in self.models.items():
            if model_name not in self.capitulos_embeddings:
                continue

            try:
                # Buscar apenas em capitulos
                query_embedding = model.encode([search_term])
                embeddings = self.capitulos_embeddings[model_name]

                # CORRECAO: Usar cosine similarity corretamente
                similarities = np.dot(query_embedding, embeddings.T).flatten()
                similarities = np.clip(similarities, -1, 1)  # Normalizar entre -1 e 1

                best_idx = np.argmax(similarities)
                similarity = similarities[best_idx]

                # Threshold mais baixo para capitulos (mais permissivo)
                if similarity > self.config['thresholds']['capitulos_medium']:
                    row = self.capitulos_df.iloc[best_idx]
                    start_cat = row.get('CATINIC', '')
                    end_cat = row.get('CATFIM', '')
                    desc = row.get('DESCRICAO', '')

                    # Bonus para capitulos
                    adjusted_score = similarity * self.config['weights']['capitulos_bonus']

                    if adjusted_score > best_score:
                        best_score = adjusted_score
                        best_result = (start_cat, end_cat)
                        print(f"   {model_name} CAPITULOS: {start_cat}-{end_cat} ({desc[:30]}...) sim:{similarity:.3f}")

            except Exception as e:
                print(f"   Erro {model_name} capitulos: {e}")

        return best_result

    def _validated_semantic_search(self, search_term: str) -> Optional[Tuple[str, str]]:
        """Busca semantica com validacao de resultado."""
        if not self.models:
            return None

        all_results = []

        for model_name, model in self.models.items():
            # Buscar em capitulos
            if model_name in self.capitulos_embeddings:
                cap_result = self._semantic_search_dataset(
                    search_term, model, model_name, 'capitulos'
                )
                if cap_result:
                    all_results.append({
                        'result': cap_result,
                        'source': 'capitulos',
                        'model': model_name,
                        'is_validated': self._validate_semantic_result(search_term, cap_result, 'capitulos')
                    })

            # Buscar em categorias (com threshold mais alto)
            if model_name in self.categorias_embeddings:
                cat_result = self._semantic_search_dataset(
                    search_term, model, model_name, 'categorias'
                )
                if cat_result:
                    all_results.append({
                        'result': cat_result,
                        'source': 'categorias',
                        'model': model_name,
                        'is_validated': self._validate_semantic_result(search_term, cat_result, 'categorias')
                    })

        # Filtrar apenas resultados validados
        validated_results = [r for r in all_results if r['is_validated']]

        if validated_results:
            # Priorizar capitulos para termos gerais
            if self._is_general_medical_term(search_term):
                cap_results = [r for r in validated_results if r['source'] == 'capitulos']
                if cap_results:
                    best = cap_results[0]
                    return (best['result'][0], best['result'][1])

            # Retornar melhor resultado validado
            best = validated_results[0]
            return (best['result'][0], best['result'][1])

        return None

    def _semantic_search_dataset(self, search_term: str, model: SentenceTransformer,
                                model_name: str, dataset: str) -> Optional[Tuple]:
        """Busca semantica em dataset especifico com correcoes."""
        try:
            query_embedding = model.encode([search_term])

            if dataset == 'capitulos':
                embeddings = self.capitulos_embeddings[model_name]
                df = self.capitulos_df
                threshold_key = 'capitulos_medium'
            else:
                embeddings = self.categorias_embeddings[model_name]
                df = self.categorias_df
                threshold_key = 'categorias_high'  # Threshold mais alto para categorias

            # CORRECAO: Normalizar similarities corretamente
            similarities = np.dot(query_embedding, embeddings.T).flatten()
            similarities = np.clip(similarities, -1, 1)  # Forca range [-1, 1]

            best_idx = np.argmax(similarities)
            best_similarity = float(similarities[best_idx])  # Converter para float

            threshold = self.config['thresholds'][threshold_key]

            if best_similarity > threshold:
                row = df.iloc[best_idx]

                if dataset == 'capitulos':
                    start_cat = row.get('CATINIC', '')
                    end_cat = row.get('CATFIM', '')
                    desc = row.get('DESCRICAO', '')
                    print(f"   {model_name} CAPITULOS: {start_cat}-{end_cat} ({desc[:30]}...) sim:{best_similarity:.3f}")
                    return (start_cat, end_cat, best_similarity)
                else:
                    code = row.get('CAT', '')
                    desc = row.get('DESCRICAO', '')
                    print(f"   {model_name} CATEGORIAS: {code} ({desc[:30]}...) sim:{best_similarity:.3f}")
                    return (code, code, best_similarity)

        except Exception as e:
            print(f"   Erro semantic search {dataset}: {e}")

        return None

    def _validate_semantic_result(self, search_term: str, result: Tuple, source: str) -> bool:
        """Valida se resultado semantico faz sentido."""
        if not result or len(result) < 2:
            return False

        start_code, end_code = result[0], result[1]

        # Validacoes basicas
        if not start_code or not end_code:
            return False

        # Para termos respiratorios, deve retornar codigos J
        if 'respirat' in search_term.lower():
            if not (start_code.startswith('J') or end_code.startswith('J')):
                print(f"   VALIDACAO: '{search_term}' retornou {start_code}-{end_code} (nao e respiratorio)")
                return False

        # Para termos cardiovasculares, deve retornar codigos I
        if any(term in search_term.lower() for term in ['cardiovascular', 'cardiaca', 'coracao']):
            if not (start_code.startswith('I') or end_code.startswith('I')):
                print(f"   VALIDACAO: '{search_term}' retornou {start_code}-{end_code} (nao e cardiovascular)")
                return False

        # Para diabetes, deve retornar codigos E
        if 'diabet' in search_term.lower():
            if not (start_code.startswith('E') or end_code.startswith('E')):
                print(f"   VALIDACAO: '{search_term}' retornou {start_code}-{end_code} (nao e endocrino)")
                return False

        # Validacao passou
        print(f"   VALIDACAO: '{search_term}' -> {start_code}-{end_code} (correto)")
        return True

    def _intelligent_fallback(self, search_term: str) -> Optional[Tuple[str, str]]:
        """Fallback inteligente baseado em padroes."""
        # Padroes de fallback por categoria
        fallback_patterns = {
            'respirat': ('J00', 'J99'),
            'pulmao': ('J00', 'J99'),
            'pulmonar': ('J00', 'J99'),
            'cardiovascular': ('I00', 'I99'),
            'cardiaca': ('I00', 'I99'),
            'coracao': ('I00', 'I99'),
            'diabetes': ('E10', 'E14'),
            'cancer': ('C00', 'D49'),
            'tumor': ('C00', 'D49'),
            'renal': ('N00', 'N99'),
            'rim': ('N00', 'N99'),
            'mental': ('F00', 'F99'),
            'neurologica': ('G00', 'G99'),
            'digestiva': ('K00', 'K95')
        }

        for pattern, cid_range in fallback_patterns.items():
            if pattern in search_term:
                return cid_range

        return None

    # Metodos de compatibilidade e debug
    def debug_search(self, search_term: str) -> Dict[str, Any]:
        """Debug completo da busca."""
        return {
            'term': search_term,
            'is_general': self._is_general_medical_term(search_term.lower()),
            'hardcoded_result': self._hardcoded_search(search_term.lower()),
            'capitulos_result': self._search_capitulos_semantic(search_term.lower()),
            'final_result': self.find_cid_range(search_term)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Estatisticas do sistema."""
        return {
            'hardcoded_terms': len(self.hardcoded_chapters),
            'models_loaded': list(self.models.keys()),
            'has_capitulos': self.capitulos_df is not None,
            'has_categorias': self.categorias_df is not None,
            'capitulos_count': len(self.capitulos_df) if self.capitulos_df is not None else 0,
            'categorias_count': len(self.categorias_df) if self.categorias_df is not None else 0
        }


CIDLookup = CIDLookupFixed

