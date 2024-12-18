from pyparsing import Word, alphas, Group, CaselessLiteral, quotedString, delimitedList, alphanums, Or, Literal, Optional, nums , Suppress
from test import CosineSimilaritySearch , data
import time 
import pandas as pd
import setting.postgresImp as postgresImp
import numpy as np


ALL_COLUMNS = ["doc_id", "title", "artist", "album", "release_date", "similarity"]

class QueryParser:
    def __init__(self):
        self.parser = self.build_parser()

    def build_parser(self):
        # Definir las palabras clave de la consulta
        SELECT = CaselessLiteral("select")
        FROM = CaselessLiteral("from")
        WHERE = CaselessLiteral("where")
        LIKETO = CaselessLiteral("liketo")
        LIMIT = CaselessLiteral("limit")

        # Definir los identificadores (columnas y tabla)
        identifier = Word(alphas, alphanums + "_")
        column = Group(Or([Literal("*"), delimitedList(identifier)])).setResultsName("columns")
        table = identifier.setResultsName("table")

        search_field = identifier.setResultsName("field")
        search_text = quotedString.setResultsName("query")

        # Definir el valor de LIMIT (opcional)
        limit_value = Word(nums).setResultsName("limit")
        limit_clause = LIMIT + Optional(Word(' \t')) + limit_value

        # Definir la declaración completa (con LIMIT opcional)
        select_stmt = (
            SELECT + column + FROM + table + WHERE + search_field + LIKETO + search_text + Optional(limit_clause)
        )

        return select_stmt

    def parse_query(self, query):
        parsed = self.parser.parseString(query)
        return parsed.asDict()



# Clase de búsqueda
class MusicSearch:
    def __init__(self, block_folder='./blocks1000/' , use_db = False , db_params = None):
        self.num_docs = self.selectData(block_folder)
        self.invert_index = CosineSimilaritySearch(block_folder, self.num_docs , lang='es')
        self.queryparser = QueryParser()
        self.use_db = use_db
        if use_db and db_params:
            self.db = postgresImp.PostgresPy(**db_params)
        else:
            self.db = None 
    def selectData(self, block_folder):
        folder_map = {
            "./blocks1000/": 1000,
            "./blocks5000/": 5000,
            "./blocks10000/": 10000
        }
        print(f'cambiando a {folder_map[block_folder]}')
        return folder_map[block_folder]
    def search(self, query):

        parsed_query = self.queryparser.parse_query(query) 
        search_text = parsed_query["query"].strip("'")
        limit = int(parsed_query.get("limit", 5))
        if(self.use_db):
            start_time = time.time()
            results = self.db.consulta(limit, search_text)
            tiempo_ejecucion = (time.time() - start_time) * 1000
            filter_results = []
            for result in results:
                filtered_result = {}
                filtered_result["doc_id"] = result[0]
                filtered_result["title"] = result[1]
                filtered_result["artist"] = result[2]
                filtered_result["album"] = result[3]
                filtered_result["release_date"] = result[4]
                filter_results.append(filtered_result)
            
        else:
            start_time = time.time()
            # Realizar la búsqueda usando el valor de LIMIT
            top_docs, results_df = self.invert_index.cosine_similarity(search_text, limit)
            tiempo_ejecucion = (time.time() - start_time) * 1000

            # Filtrar los resultados según las columnas solicitadas
            columns = ALL_COLUMNS if '*' in parsed_query["columns"] else parsed_query["columns"]
            filter_results = []

            for _ , result in results_df.iterrows():
                filtered_result = {}
                if "doc_id" in columns:
                    filtered_result["doc_id"] = result['doc_id']
                if "title" in columns:
                    filtered_result["title"] = result['track_name']
                if "artist" in columns:
                    filtered_result["artist"] = result['track_artist']
                if "album" in columns:
                    filtered_result["album"] = result['album_name']
                if "release_date" in columns:
                    filtered_result["release_date"] = result['release_date']
                if "similarity" in columns:
                    filtered_result["similarity"] = result['similarity']
                
                filter_results.append(filtered_result)

        return filter_results , tiempo_ejecucion



# Prueba del parser
query = "select * from Audio where content liketo 'love' limit 5"

block_folder = './blocks1000/'
search_engine = MusicSearch(block_folder , use_db = False)
search_results = search_engine.search(query)
for result in search_results:
    print(result)
