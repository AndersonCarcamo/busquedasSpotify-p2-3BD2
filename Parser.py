from pyparsing import Word, alphas, Group, CaselessLiteral, quotedString, delimitedList, alphanums, Or, Literal, Optional, nums , Suppress
from test import CosineSimilaritySearch , data
import time 
import pandas as pd

ALL_COLUMNS = ["title", "artist", "lyrics", "similarity"]

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
    def __init__(self, block_folder='./blocks1/'):
        self.invert_index = CosineSimilaritySearch(block_folder , data)
        self.queryparser = QueryParser()

    def search(self, query):
        start_time = time.time()

        parsed_query = self.queryparser.parse_query(query)
        search_text = parsed_query["query"].strip("'")

        # Obtener el valor de LIMIT si está especificado, con un valor predeterminado de 5
        limit = int(parsed_query.get("limit", 5))

        # Realizar la búsqueda usando el valor de LIMIT
        results = self.invert_index.get_top_k_similar_documents(search_text, k=limit)
        tiempo_ejecucion = (time.time() - start_time) * 1000 

        
        # Filtrar los resultados según las columnas solicitadas
        columns = ALL_COLUMNS if '*' in parsed_query["columns"] else parsed_query["columns"]

        filter_results = []
        for result in results.itertuples(index=False):
            filtered_result = {}
            if "title" in columns:
                filtered_result["title"] = result.Song_Title
            if "artist" in columns:
                filtered_result["artist"] = result.Artist
            if "lyrics" in columns:
                filtered_result["lyrics"] = result.Lyrics
            if "similarity" in columns:
                filtered_result["similarity"] = result.Similarity_Score
            
            filter_results.append(filtered_result)

        return filter_results , tiempo_ejecucion



'''# Prueba del parser
query = "select * from Audio where content liketo 'mayor que yo' limit 1"

block_folder = './blocks1/'

# Prueba de la búsqueda
search_engine = MusicSearch(block_folder)
search_results = search_engine.search(query)
print("Top K documentos más similares:")
print(search_results)'''
