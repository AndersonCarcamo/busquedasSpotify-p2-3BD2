
from spimi import SPIMI
import pandas as pd

# testeo
path = './dataset/'
data_path = path + 'spotify_songs.csv'

data = pd.read_csv(data_path)


data1000 = data.head(1000)
data5000 = data.head(5000)
data10000 = data.head(10000)
data18000 = data


spimi = SPIMI(size_per_block=10240*4,
              path_block= './.temp1000/',
              output_folder='./blocks1000/',
              ram_limit=1024*1024*1024*4,
              size_per_block_out= 1024*4)

#spimi.BSBIndexConstuction(data1000)


spimi = SPIMI(size_per_block=10240*4,
              path_block= './.temp5000/',
              output_folder='./blocks5000/',
              ram_limit=1024*1024*1024*4,
              size_per_block_out= 1024*4)

#spimi.BSBIndexConstuction(data5000)

spimi = SPIMI(size_per_block=10240*4,
              path_block= './.temp10000/',
              output_folder='./blocks10000/',
              ram_limit=1024*1024*1024*4,
              size_per_block_out= 1024*4)

#spimi.BSBIndexConstuction(data10000)

spimi = SPIMI(size_per_block=10240*4,
              path_block= './.temp18000/',
              output_folder='./blocks18000/',
              ram_limit=1024*1024*1024*4,
              size_per_block_out= 1024*4)

#spimi.BSBIndexConstuction(data18000)


import numpy as np
import os
import re
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import pandas as pd
import bisect



class CosineSimilaritySearch:
    def __init__(self, block_folder, data):
        self.block_folder = block_folder
        self.data = data
        self.num_docs = len(data)
        self.language_map = {
            'es': 'spanish',
            'en': 'english',
            'fr': 'french',
            'de': 'german',
            'it': 'italian'
        }

    def preprocess(self, text, lang='en'):
        lang = self.language_map.get(lang, 'english')
        stop_words = stopwords.words(lang)
        stemmer = SnowballStemmer(language=lang)

        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9_À-ÿ]', ' ', text)

        words = []
        for word in text.split():
            if word not in stop_words:
                words.append(stemmer.stem(word))

        return words

    def calculate_query_vector(self, query_terms, df_dict):
        tf_query = defaultdict(int)
        for term in query_terms:
            tf_query[term] += 1

        query_vector = {}
        for term, tf in tf_query.items():
            idf = np.log((self.num_docs / df_dict[term])) if term in df_dict and df_dict[term] > 0 else 0
            query_vector[term] = tf * idf
            print(f"Término: {term}, TF: {tf}, IDF: {idf}, TF-IDF: {query_vector[term]}")  # Depuración
        return query_vector
    
    def load_block_terms(self, query_terms):
        term_postings = {}
        df_dict = {}

        for filename in os.listdir(self.block_folder):
            with open(os.path.join(self.block_folder, filename), 'r') as file:
                for line in file:
                    term, rest = line.split(" (DF: ")
                    if self.binary_search(query_terms, term):
                        df, postings = rest.split("): ")
                        df = int(df)
                        df_dict[term] = df
                        
                        term_postings[term] = []
                        postings_list = postings.strip().split("), (")
                        for posting in postings_list:
                            doc_id, tf = map(int, posting.strip("()").split(", "))
                            term_postings[term].append((doc_id, tf))
        return term_postings, df_dict

    def binary_search(self, sorted_list, item):
        index = bisect.bisect_left(sorted_list, item)
        return index < len(sorted_list) and sorted_list[index] == item

    def cosine_similarity(self, query_vector, term_postings):
        doc_scores = defaultdict(float)
        query_norm = np.sqrt(np.sum(np.square(list(query_vector.values()))))

        # Construcción de vectores de documentos
        doc_vectors = defaultdict(lambda: defaultdict(float))
        for term, query_weight in query_vector.items():
            if term in term_postings:
                for doc_id, tf in term_postings[term]:
                    tf_weight = tf * query_weight
                    doc_vectors[doc_id][term] += tf_weight
                    print(f"Doc: {doc_id}, Término: {term}, TF: {tf}, Peso: {tf_weight}")  # Depuración

        # Calcular similitud coseno
        for doc_id, terms in doc_vectors.items():
            dot_product = sum(query_vector[term] * terms[term] for term in terms if term in query_vector)
            doc_norm = np.sqrt(sum((terms[term])**2 for term in terms))
            if query_norm != 0 and doc_norm != 0:
                doc_scores[doc_id] = dot_product / (query_norm * doc_norm)
            else:
                doc_scores[doc_id] = 0.0
            print(f"Doc: {doc_id}, Producto punto: {dot_product}, Norma consulta: {query_norm}, Norma documento: {doc_norm}, Similitud: {doc_scores[doc_id]}")  # Depuración

        print(doc_scores)

        return sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    def get_top_k_similar_documents(self, query, lang='en', k=5):
        query_terms = self.preprocess(query, lang=lang)
        print(f"Términos de la consulta procesados: {query_terms}")
        term_postings, df_dict = self.load_block_terms(query_terms)
        query_vector = self.calculate_query_vector(query_terms, df_dict)
        
        doc_scores = self.cosine_similarity(query_vector, term_postings)
        doc_scores = sorted(doc_scores, key=lambda x: x[1], reverse=True)[:k]

        results = []
        for doc_id, score in doc_scores:
            try:
                doc_details = self.data.iloc[doc_id].to_dict()
                doc_details["Cosine Similarity Score"] = score
                results.append(doc_details)
            except IndexError:
                print(f"El documento con ID {doc_id} no está disponible en los datos.")

        results_df = pd.DataFrame(results)
        results_df = results_df[["track_name", "track_artist", "lyrics", "Cosine Similarity Score"]]
        results_df.columns = ["Song_Title", "Artist", "Lyrics", "Similarity_Score"]
        results_df.index = range(1, len(results) + 1)
        return results_df

    def search(self, query, lang='en'):
        query_terms = self.preprocess(query, lang=lang)
        term_postings, df_dict = self.load_block_terms(query_terms)
        query_vector = self.calculate_query_vector(query_terms, df_dict)
        return self.cosine_similarity(query_vector, term_postings)



'''
block_folder = './blocks1/'
search_engine = CosineSimilaritySearch(block_folder, data)
results_df = search_engine.get_top_k_similar_documents("mayor que yo", lang='es', k=5)
print("Top K documentos más similares:")
print(results_df)'''