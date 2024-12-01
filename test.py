from spimi import SPIMI
import pandas as pd

import numpy as np
import os
import re
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import pandas as pd
import bisect

# testeo
path = './dataset/'
data_path = path + 'spotify_songs.csv'

data = pd.read_csv(data_path)


data1000 = data.head(1000)
data5000 = data.head(5000)
data10000 = data.head(10000)
data18000 = data

doc_metadata_map = data1000.to_dict("index")

class CosineSimilaritySearch:
    def __init__(self, block_folder, num_docs, lang='en'):
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
        with open(block_path, "r") as block_file:
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
            with open(block_path, "r") as block_file:
                lines = [line.strip() for line in block_file.readlines()]
                # print(f"Línea 1 del bloque: {lines[0]}")
                # print(f"Last line del bloque: {lines[-1]}")
                first_line = lines[0]
                last_line = lines[-1]

            first_term, _, _ = self.parse_line(first_line)
            last_term, _, _ = self.parse_line(last_line)

            if first_term <= token <= last_term:
                return self.search_term_in_block(token, block_path)
            elif token < first_term:
                high = mid - 1
            else:
                low = mid + 1
        return None, 0

    def cosine_similarity(self, query, topk):
        """
        Calcula la similitud de coseno entre la consulta y los documentos.
        """
        scores = defaultdict(float)
        query_terms = self.preprocess_query(query)
        print(query_terms)
        norm_query = 0
        df_dict = {}
        tf_query = defaultdict(int)
        global_tf_idf_squares = defaultdict(float)

        for token in query_terms:
            tf_query[token] += 1

        print(f"TF de la consulta: {tf_query}")

        for token, tf in tf_query.items():
            postings_list, df = self.search_term(token)
            print(f"Postings list: {postings_list} con DF: {df} para término: {token}")
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
        
        results = []
        for doc_id, similarity in topk_docs:
            # Recuperar información del DataFrame basado en el índice (doc_id)
            metadata = doc_metadata_map.get(doc_id, {})
            track_name = metadata.get("track_name", "Unknown")
            track_artist = metadata.get("track_artist", "Unknown")
            album_name = metadata.get("track_album_name", "Unknown")
            release_date = metadata.get("track_album_release_date", "Unknown")
            # Guardar resultados en una lista
            results.append({
                'doc_id': doc_id,
                'similarity': similarity,
                'track_name': track_name,
                'track_artist': track_artist,
                'album_name': album_name,
                'release_date': release_date
            })
        
        # Crear DataFrame fuera del bucle
        results_df = pd.DataFrame(results, columns=['doc_id', 'similarity', 'track_name', 'track_artist', 'album_name', 'release_date'])


        return topk_docs, results_df


'''block_folder = './blocks1000/'
search_engine = CosineSimilaritySearch(block_folder, 1000 , lang='es')
topk_docs, results_df = search_engine.cosine_similarity("love", 5)
print("Top K documentos más similares:")
print(results_df)'''