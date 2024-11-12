from pyparsing import Word, alphas, Group, Suppress, CaselessLiteral, quotedString, delimitedList, alphanums, OneOrMore
from test import CosineSimilaritySearch

class QueryParser:
    def __init__(self):
        self.parser = self.build_parser()

    def build_parser(self):
        SELECT = CaselessLiteral("select")
        FROM = CaselessLiteral("from")
        WHERE = CaselessLiteral("where")
        LIKETO = CaselessLiteral("liketo")

        identifier = Word(alphas, alphanums + "_")
        column = Group(delimitedList(identifier)).setResultsName("columns")
        table = identifier.setResultsName("table")

        search_field = identifier.setResultsName("field")
        search_text = quotedString.setResultsName("query")

        select_stmt = (
            SELECT + column + FROM + table + WHERE + search_field + LIKETO + search_text
        )
        
        return select_stmt

    def parse_query(self, query):
        parsed = self.parser.parseString(query)
        return parsed.asDict()




#conectar con la base de datos
class MusicSearch:
    def __init__(self, block_folder = './blocks/'):
        self.invert_index = CosineSimilaritySearch(block_folder)
        self.queryparser = QueryParser()

    def search(self, query, top_k=5):
        parsed_query = self.queryparser.parse_query(query)
        search_text = parsed_query["query"].strip("'")
        results = self.invert_index.get_top_k_similar_documents(search_text, k=top_k)

        #filtrar los resultados segun los campos solicitados
        filter_results = []
        columnos = parsed_query["columns"]
        for result in results.itertuples(index=False):
            filtered_result = {}
            if "lyrics" in columnos:
                filtered_result["lyrics"] = result.lyrics
            if "title" in columnos:
                filtered_result["title"] = result.track_name
            if "artist" in columnos:
                filtered_result["artist"] = result.track_artist
            if "album" in columnos:
                filtered_result["album"] = result.track_album_name
            if "popularity" in columnos:
                filtered_result["popularity"] = result.track_popularity
            if "release_date" in columnos:
                filtered_result["release_date"] = result.track_album_release_date
            filter_results.append(filtered_result)

        return filter_results

'''# Prueba del parser
query = "select title, artist , lyrics from Audio where content liketo 'yea you just can't walk away'"

block_folder = './blocks/'

# Prueba de la búsqueda
search_engine = MusicSearch(block_folder)
search_results = search_engine.search(query, 5)
print("Top K documentos más similares:")
print(search_results)'''