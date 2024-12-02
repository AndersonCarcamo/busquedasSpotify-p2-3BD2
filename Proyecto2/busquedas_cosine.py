import os
import ast
import numpy as np
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import re
import time

class CosineSimilaritySearch:
    def __init__(self, block_folder, num_docs, doc_metadata_map, lang='en'):
        self.block_folder = block_folder
        self.num_docs = num_docs
        self.language_map = {
            'es': 'spanish',
            'en': 'english',
            'fr': 'french',
            'de': 'german',
            'it': 'italian'
        }
        self.lang = lang
        self.stop_words = set(stopwords.words(self.language_map.get(lang, 'english')))
        self.stemmer = SnowballStemmer(language=self.language_map.get(lang, 'english'))
        self.doc_metadata_map = doc_metadata_map

    def preprocess_query(self, query):
        query = query.lower()
        tokens = [self.stemmer.stem(word) for word in query.split() if word not in self.stop_words]
        return tokens

    def parse_line(self, line):
        """
        Parsear una línea del bloque en formato: "term (DF: x): (doc_id, tf), ..."
        """
        line = line.strip()  # Eliminar saltos de línea y espacios extra
        try:
            term, rest = line.split(" (DF: ")
            df, postings = rest.split("): ")
            df = int(df)
            postings_list = [
                tuple(map(int, posting.strip("()").split(", "))) for posting in postings.split("), (")
            ]
            return term, df, postings_list
        except ValueError as e:
            raise ValueError(f"Error procesando la línea: {line}. Detalles: {str(e)}")

    def search_term_in_block(self, token, block_path):
        """
        Busca un término dentro de un bloque específico utilizando búsqueda binaria.
        """
        with open(block_path, "r", encoding='ISO-8859-1') as block_file:
            lines = [line.strip() for line in block_file.readlines()]

        low, high = 0, len(lines) - 1
        while low <= high:
            mid = (low + high) // 2
            line = lines[mid]
            term, df, postings_list = self.parse_line(line)

            if token == term:
                return postings_list, df
            elif token < term:
                high = mid - 1
            else:
                low = mid + 1
        return None, 0

    def search_term(self, token):
        """
        Encuentra el bloque donde puede estar el término y busca dentro de él.
        """
        def natural_sort_key(s):
            return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

        block_files = sorted(os.listdir(self.block_folder), key=natural_sort_key)
        # print(block_files)
        low, high = 0, len(block_files) - 1
        # print(f'low: {low}, high: {high}')
        while low <= high:
            mid = (low + high) // 2
            # print('mid:', mid)
            block_path = os.path.join(self.block_folder, block_files[mid])
            # print(f'Block_path: {block_path}')
            with open(block_path, "r", encoding='ISO-8859-1') as block_file:
                lines = [line.strip() for line in block_file.readlines()]
                # print(f"Línea 1 del bloque: {lines[0]}")
                # print(f"Last line del bloque: {lines[-1]}")
                first_line = lines[0]
                last_line = lines[-1]

            first_term, _, _ = self.parse_line(first_line)
            last_term, _, _ = self.parse_line(last_line)

            if first_term <= token <= last_term:
                postings_list, df = self.search_term_in_block(token, block_path)

                block_list = []
                while mid - 1 >= 0:
                    prev_block_path = os.path.join(self.block_folder, block_files[mid - 1])
                    with open(prev_block_path, "r", encoding="ISO-8859-1") as prev_block_file:
                        prev_lines = [line.strip() for line in prev_block_file.readlines()]
                        prev_first_term, _, _ = self.parse_line(prev_lines[0])
                        if prev_first_term == token:
                            postings_prev_block, _ = self.search_term_in_block(token, prev_block_path)
                            block_list.append(postings_prev_block)
                            mid -= 1
                        else:
                            break  # El término no está en el bloque anterior

                # Verificar si el término sigue existiendo en el bloque siguiente
                # Continuar buscando hacia adelante (bloques posteriores)
                while mid + 1 <= high:
                    next_block_path = os.path.join(self.block_folder, block_files[mid + 1])
                    with open(next_block_path, "r", encoding="ISO-8859-1") as next_block_file:
                        next_lines = [line.strip() for line in next_block_file.readlines()]
                        next_first_term, _, _ = self.parse_line(next_lines[0])
                        if next_first_term == token:
                            postings_next_block, _ = self.search_term_in_block(token, next_block_path)
                            block_list.append(postings_next_block)
                            mid += 1
                        else:
                            break  # El término no está en el bloque siguiente

                # Combinar todas las listas de postings de los bloques encontrados
                all_postings = []
                all_postings.extend(postings_list)
                for block_postings in block_list:
                    all_postings.extend(block_postings)

                return all_postings, df
            elif token < first_term:
                high = mid - 1
            else:
                low = mid + 1
        return None, 0

    def cosine_similarity(self, tf_query, topk):
        """
        Calcula la similitud de coseno entre la consulta y los documentos.
        """

        scores = defaultdict(float)
        norm_query = 0
        df_dict = {}
        global_tf_idf_squares = defaultdict(float)
        for token, tf in tf_query.items():
            # print(f'Token de busqueda: {token}')
            postings_list, df = self.search_term(token)
            # print(f"Postings list: {postings_list} con DF: {df} para término: {token}")
            if postings_list:
                df_dict[token] = df
                idf = np.log10(self.num_docs / df)
                tf_weight_query = np.log10(1 + tf)
                wt_query = tf_weight_query * idf

                norm_query += np.square(wt_query)

                for doc_id, tf_doc in postings_list:
                    tf_weight_doc = np.log10(tf_doc + 1)
                    wt_doc = tf_weight_doc * idf
                    scores[doc_id] += wt_query * wt_doc
                    global_tf_idf_squares[doc_id] += wt_doc ** 2

        norm_query = np.sqrt(norm_query)
        norm_global = np.sqrt(sum(global_tf_idf_squares.values()))

        for doc_id, score in scores.items():
            norm_doc = np.sqrt(global_tf_idf_squares[doc_id])
            if norm_query != 0 and norm_doc != 0 and norm_global != 0:
                scores[doc_id] = score / (norm_query * norm_global)
            else:
                scores[doc_id] = 0

        topk_docs = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:topk]
        return topk_docs
    
    def search_top_k(self, query, topk = 10):
        query_terms = self.preprocess_query(query)
        tf_query = defaultdict(int)
        for token in query_terms:
            tf_query[token] += 1
        
        # print(tf_query)
        start_time = time.time()
        topk_results = self.cosine_similarity(tf_query, topk)
        end_time = time.time()
        execution_time = end_time - start_time
        # print(topk_results)
        
        for doc_id, similarity in topk_results:
            # Recuperar información del DataFrame basado en el índice (doc_id)
            metadata = self.doc_metadata_map.get(doc_id, {})
            track_name = metadata.get("track_name", "Unknown")
            track_artist = metadata.get("track_artist", "Unknown")
            album_name = metadata.get("track_album_name", "Unknown")
            release_date = metadata.get("track_album_release_date", "Unknown")
            print(f"Documento: {doc_id}, Similitud: {similarity:.4f}, "
                f"Título: {track_name}, Artista: {track_artist}, "
                f"Álbum: {album_name}, Fecha de lanzamiento: {release_date}")
        
        print(f"\nTiempo de ejecución de la consulta: {execution_time:.4f} segundos")
        return execution_time