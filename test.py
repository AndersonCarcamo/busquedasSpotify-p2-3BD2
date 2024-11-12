from spimy2 import BSBIndexConstuction
import pandas as pd
from spimi import SPIMI

import math
import os
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import regex as re

import pandas as pd
import csv


path = './dataset/'
data_path = path + 'spotify_songs_test2.csv'

data = pd.read_csv(data_path, index_col=None)

spimi = SPIMI(size_per_block=10240*4,
              output_folder='./blocks/',
              ram_limit=1024*1024*1024*4,
              size_per_block_out= 1024*5.9)

#spimi.BSBIndexConstuction(data)


class CosineSimilaritySearch:
    def __init__(self, block_folder):
        self.block_folder = block_folder
        self.stopwords = stopwords.words('spanish')  # ajusta el idioma si es necesario
        self.stemmer = SnowballStemmer(language='spanish')  # ajusta el idioma si es necesario

    def preprocess(self, text):
        """Preprocesa el texto: limpieza, stopword removal, stemming."""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9_À-ÿ]', ' ', text)
        words = [word for word in text.split() if word not in self.stopwords]
        return [self.stemmer.stem(word) for word in words]

    def calculate_query_vector(self, query_terms, df_dict, num_docs):
        """Calcula el vector TF-IDF para la consulta."""
        tf_query = defaultdict(int)
        for term in query_terms:
            tf_query[term] += 1
        
        query_vector = {}
        for term, tf in tf_query.items():
            idf = math.log((num_docs / df_dict[term])) if term in df_dict else 0
            query_vector[term] = tf * idf
        return query_vector

    def load_block_terms(self, query_terms):
        """Carga solo los términos relevantes de los bloques para la consulta."""
        term_postings = {}
        df_dict = {}
        num_docs = 0

        for filename in os.listdir(self.block_folder):
            with open(os.path.join(self.block_folder, filename), 'r') as file:
                for line in file:
                    term, rest = line.split(" (DF: ")
                    if term not in query_terms:
                        continue
                    
                    df, postings = rest.split("): ")
                    df = int(df)
                    df_dict[term] = df
                    num_docs += df
                    
                    term_postings[term] = []
                    postings_list = postings.strip().split("), (")
                    for posting in postings_list:
                        doc_id, tf = map(int, posting.strip("()").split(", "))
                        term_postings[term].append((doc_id, tf))
        return term_postings, df_dict, num_docs

    def cosine_similarity(self, query_vector, doc_vectors):
        """Calcula la similitud de coseno entre la consulta y cada documento, con depuración."""
        doc_scores = defaultdict(float)
        query_norm = math.sqrt(sum(weight**2 for weight in query_vector.values()))
        
        # Acumula pesos para cada documento y muestra detalles para depuración
        print("Vector de la consulta:", query_vector)
        for term, query_weight in query_vector.items():
            # Verificar si el término existe en doc_vectors antes de intentar acceder a él
            if term in doc_vectors:
                for doc_id, doc_tf in doc_vectors[term]:
                    # Calcula el peso del término en el documento y lo acumula
                    doc_weight = doc_tf * query_weight
                    doc_scores[doc_id] += doc_weight
                    print(f"Documento {doc_id} - Término '{term}': TF={doc_tf}, Peso en doc={doc_weight}, Acumulado={doc_scores[doc_id]}")

        # Calcular norma del vector de cada documento y similitud de coseno
        for doc_id in doc_scores:
            # Calcular la norma del documento usando solo términos en query_vector
            doc_norm = math.sqrt(
                sum(
                    (doc_tf * query_vector.get(term, 0))**2 
                    for term in query_vector
                    for doc_id_in_posting, doc_tf in doc_vectors.get(term, [])
                    if doc_id_in_posting == doc_id
                )
            )
            if doc_norm != 0:
                doc_scores[doc_id] = doc_scores[doc_id] / (query_norm * doc_norm)
            else:
                doc_scores[doc_id] = 0
            print(f"Documento {doc_id} - Similaridad de coseno: {doc_scores[doc_id]}")
        
        # Ordena y devuelve los resultados
        return sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)


    def get_top_k_similar_documents(self, query, k=5):
        # Procesar la consulta y realizar la búsqueda
        query_terms = self.preprocess(query)
        term_postings, df_dict, num_docs = self.load_block_terms(query_terms)
        query_vector = self.calculate_query_vector(query_terms, df_dict, num_docs)
        doc_scores = self.cosine_similarity(query_vector, term_postings)
        
        # Obtener los k documentos más similares
        top_k_docs = doc_scores[:k]
        top_k_indices = [doc_id for doc_id, _ in top_k_docs]  # Obtén solo los índices de los documentos 
        # Obtener los datos de los documentos más similares con sus metadatos
        top_k_data = data.iloc[top_k_indices][['track_name', 'track_artist', 'lyrics' ,'track_popularity' ,'track_album_name' ,'track_album_release_date' , 'playlist_name']].copy()
        top_k_data['Cosine Similarity Score'] = [score for _, score in top_k_docs]  # Agregar las puntuaciones

        # Crear el DataFrame con índice 1, 2, ..., k
        top_k_data.index = range(1, k + 1)
        return top_k_data

            
    def search(self, query):
        query_terms = self.preprocess(query)
        term_postings, df_dict, num_docs = self.load_block_terms(query_terms)
        query_vector = self.calculate_query_vector(query_terms, df_dict, num_docs)
        return self.cosine_similarity(query_vector, term_postings)



'''block_folder = './blocks/'
search_engine = CosineSimilaritySearch(block_folder)
results_df = search_engine.get_top_k_similar_documents("yea you just can't walk away", k=5)
print("Top K documentos más similares:")
print(results_df)'''

'''
k = 5 

254         In Between Days - 2006 Remaster        The Cure  The Head on the Door (Deluxed Edition)
423                             All The Way       Timeflies                             All The Way
457  Make It Better (feat. Smokey Robinson)  Anderson .Paak  Make It Better (feat. Smokey Robinson)
997          Tell Me What You Want Me to Do  Tevin Campbell                              T.E.V.I.N.
769                   Wake Up - Sondr Remix  Chelsea Cutler                       Wake Up (Remixes)



'''