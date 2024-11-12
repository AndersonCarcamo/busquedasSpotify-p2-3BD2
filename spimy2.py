# librerias
import numpy as np
import pandas as pd
import os
import sys
from sortedcontainers import SortedDict
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
import regex as re
import heapq
import shutil
nltk.download('punkt')

#variables globales
size_per_block_input = 10240*4 # 4 KBytes
path_block_temp = './.temp/'
global_dictionary = SortedDict()
global_block_size = 0
output_path = './blocks/'
block_limit_size = 1024*5.9
max_ram_limit = 1024*1024*1024

class PostingBlock:
    def __init__(self, max_size=10):
        self.doc_dict = {}  # Diccionario para almacenar postings como {doc_id: TF}
        self.next_block = None
        self.max_size = max_size
        self.current_size = 0

    def is_full(self):
        return len(self.doc_dict) >= self.max_size

    def add_doc(self, doc_id, tf=1):
        if doc_id in self.doc_dict:
            self.doc_dict[doc_id] += tf
        else:
            self.doc_dict[doc_id] = tf
            self.current_size += 1


def ParseDocs(doc):
    words = []

    col_text = ['lyrics', 'track_name', 'track_artist', 'track_album_name', 'playlist_name', 'playlist_genre', 'playlist_subgenre']
    texto = ''
    for col in col_text:
        texto += ' ' + doc[col]

    texto = texto.lower()

    texto = re.sub(r'[^a-zA-Z0-9_À-ÿ]', ' ', texto)


    if doc['language'] == 'es':
        ln = 'spanish'
    elif doc['language'] == 'tl':
        ln = 'english'
    else:
        ln = 'english'
    
    for word in texto.split():
        
        if word not in stopwords.words(ln):
            words.append(word)

    # aplicar stemming
    stemmer = SnowballStemmer(language=ln)
    words = [stemmer.stem(word) for word in words]

    return words


def WriteBlockToDisk(dictionary, block_id, path='./blocks2/'):
    output_file = f"{path}block_{block_id}.txt"
    
    with open(output_file, 'w') as f:
        for term, data in dictionary.items():
            df = data['df']
            postings_list = []

            posting_block = data['posting_block']
            while posting_block is not None:
                postings_list.extend([f"({doc_id}, {tf})" for doc_id, tf in posting_block.doc_dict.items()])
                posting_block = posting_block.next_block  # Avanzar al siguiente bloque enlazado
 
            postings = ', '.join(postings_list)
            f.write(f"{term} (DF: {df}): {postings}\n")

def SPIMI_INVERT(token_stream, # recibo una lista de lexemas
                 docId, # el numero del documento
                 num_block, # el numero del bloque en el que escribo
                 size_per_block,
                 path_block = './blocks/'
                 ):

    global global_dictionary, global_block_size

    
    for token in token_stream:

        if token not in global_dictionary:
            posting_block = PostingBlock()
            global_dictionary[token] = {
                'df': 1,
                'posting_block': posting_block
            }
            posting_block.add_doc(docId, 1)
            global_block_size += sys.getsizeof(token) + sys.getsizeof(global_dictionary[token])
            
        else:
            # posting_list = GetPostingsList(dictionary, term(token))
            posting_block = global_dictionary[token]['posting_block']
            doc_found = False

            while posting_block is not None:
                if docId in posting_block.doc_dict:
                    # Incrementa TF si el doc_id ya existe
                    posting_block.doc_dict[docId] += 1
                    doc_found = True
                    break
                
                # Avanzar al siguiente bloque si es necesario
                if posting_block.next_block is None:
                    break
                else:
                    posting_block = posting_block.next_block
  
            # Si el documento no fue encontrado en ningún bloque
            if not doc_found:
                global_dictionary[token]['df'] += 1
                # Si el bloque actual está lleno, enlazar un nuevo bloque
                if posting_block.is_full():
                    new_posting_block = PostingBlock()
                    posting_block.next_block = new_posting_block
                    posting_block = new_posting_block

                posting_block.add_doc(docId, 1)
                global_block_size += sys.getsizeof(docId)

        # Si el bloque alcanza el límite de tamaño, escribir a disco y resetear el diccionario
        if global_block_size >= size_per_block:
            WriteBlockToDisk(global_dictionary, num_block, path_block)
            global_dictionary = SortedDict()
            global_block_size = 0
            num_block += 1

    return num_block


def parse_block_line(line):
    """Parsea una línea del archivo de bloque en el formato (término, DF, PostingBlock)."""
    # print(f"Processing line: {line}")
    term, rest = line.split(" (DF: ")
    df, postings = rest.split("): ")
    df = int(df)
    posting_block = PostingBlock()

    postings_list = postings.strip("()").split("), (")
    # print(f'postings_list: {postings_list}')
    for posting in postings_list:
        # Extraer doc_id y tf
        doc_id, tf = map(int, posting.strip("()").split(", "))
        posting_block.add_doc(doc_id, tf)
    return term, df, posting_block

def write_to_output_block(block_id, 
                          output_terms, 
                          output_folder):
    """Escribe los términos y postings en un bloque de salida de 4 KB."""
    output_file = os.path.join(output_folder, f"block_{block_id}.txt")

    with open(output_file, 'w') as f:
        for term, (df, posting_block) in output_terms.items():
            term_entry = f"{term} (DF: {df}): "
            postings = []

            # Recorre todos los bloques de postings enlazados
            current_block = posting_block
            while current_block is not None:
                postings.extend([f"({doc}, {tf})" for doc, tf in current_block.doc_dict.items()])
                current_block = current_block.next_block

            # Unir todos los postings en una cadena y escribir la entrada completa
            term_entry += ', '.join(postings) + "\n"
            f.write(term_entry)

    print(f"Block {block_id} written to {output_file}")
    return block_id + 1, output_file


def MergeBlocks(block_files, 
                output_folder='./merged_blocks/', 
                block_size_limit=4096, 
                max_ram_limit=1024*1024*1024):
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    open_files = {file_id: open(file_path, 'r') for file_id, file_path in block_files.items()}
    input_buffers = {}
    current_ram_usage = 0
    max_memory_per_block = (max_ram_limit - block_size_limit) // len(block_files)
    merged_files = []
    heap = []

    # Cargar los buffers iniciales y añadir al heap con fusión de términos duplicados
    for file_id, file in open_files.items():
        buffer = []
        buffer_size = 0
        while buffer_size < max_memory_per_block:
            line = file.readline().strip()
            if not line:
                break
            term, df, posting_block = parse_block_line(line)
            buffer.append((term, df, posting_block))
            buffer_size += sys.getsizeof(term) + sys.getsizeof(df) + sys.getsizeof(posting_block)
        
        input_buffers[file_id] = buffer
        
        # Insertar elementos del buffer en el heap con fusión continua
        for term, df, posting_block in buffer:
            found = False
            for i, (existing_term, existing_df, existing_file_id, existing_posting_block) in enumerate(heap):
                if existing_term == term:
                    existing_df += df
                    current_block = existing_posting_block
                    while current_block.next_block:
                        current_block = current_block.next_block
                    if current_block.is_full():
                        current_block.next_block = posting_block
                    else:
                        for doc, tf in posting_block.doc_dict.items():
                            if current_block.is_full():
                                new_block = PostingBlock()
                                current_block.next_block = new_block
                                current_block = new_block
                            current_block.add_doc(doc, tf)
                    heap[i] = (existing_term, existing_df, existing_file_id, existing_posting_block)
                    found = True
                    break
            if not found:
                heapq.heappush(heap, (term, df, file_id, posting_block))

    block_id = 0
    output_terms = {}
    current_output_size = 0

    # Procesar el heap hasta vaciarlo
    while heap:
        term, df, file_id, posting_block = heapq.heappop(heap)

        # Fusionar postings si el término ya existe en output_terms
        if term in output_terms:
            existing_df, existing_posting_block = output_terms[term]
            output_terms[term] = (existing_df + df, existing_posting_block)
            current_block = existing_posting_block
            while current_block.next_block:
                current_block = current_block.next_block
            if current_block.is_full():
                current_block.next_block = posting_block
            else:
                for doc, tf in posting_block.doc_dict.items():
                    if current_block.is_full():
                        new_block = PostingBlock()
                        current_block.next_block = new_block
                        current_block = new_block
                    current_block.add_doc(doc, tf)
            additional_postings_size = len(', '.join([f"({doc}, {tf})" for doc, tf in posting_block.doc_dict.items()]))
            current_output_size += additional_postings_size
        else:
            output_terms[term] = (df, posting_block)
            postings_str = ', '.join([f"({doc}, {tf})" for doc, tf in posting_block.doc_dict.items()])
            term_entry = f"{term} (DF: {df}): {postings_str}\n"
            term_size = len(term_entry)
            current_output_size += term_size

        # Escribir el bloque de salida cuando se alcanza el límite
        if current_output_size > block_size_limit:
            block_id, block_file = write_to_output_block(block_id, output_terms, output_folder)
            merged_files.append(block_file)
            output_terms.clear()
            current_output_size = 0

        # Recargar el buffer si se queda vacío
        if not input_buffers[file_id]:
            buffer = []
            buffer_size = 0
            while buffer_size < max_memory_per_block:
                line = open_files[file_id].readline().strip()
                if not line:
                    break
                term, df, posting_block = parse_block_line(line)
                buffer.append((term, df, posting_block))
                buffer_size += sys.getsizeof(term) + sys.getsizeof(df) + sys.getsizeof(posting_block)
            input_buffers[file_id] = buffer

            # Agregar nuevos términos del buffer al heap con fusión de duplicados
            for term, df, posting_block in buffer:
                found = False
                for i, (existing_term, existing_df, existing_file_id, existing_posting_block) in enumerate(heap):
                    if existing_term == term:
                        existing_df += df
                        current_block = existing_posting_block
                        while current_block.next_block:
                            current_block = current_block.next_block
                        if current_block.is_full():
                            current_block.next_block = posting_block
                        else:
                            for doc, tf in posting_block.doc_dict.items():
                                if current_block.is_full():
                                    new_block = PostingBlock()
                                    current_block.next_block = new_block
                                    current_block = new_block
                                current_block.add_doc(doc, tf)
                        heap[i] = (existing_term, existing_df, existing_file_id, existing_posting_block)
                        found = True
                        break
                if not found:
                    heapq.heappush(heap, (term, df, file_id, posting_block))

    # Escribir cualquier término restante en el último bloque
    if output_terms:
        block_id, block_file = write_to_output_block(block_id, output_terms, output_folder)
        merged_files.append(block_file)

    # Cerrar todos los archivos
    for file in open_files.values():
        file.close()

    return merged_files


def BSBIndexConstuction(data):

    global global_dictionary, global_block_size

    if not os.path.exists(path_block_temp):
        os.makedirs(path_block_temp)

    block_n = 0 # numero de bloque actual 

    f = {} # archivos de bloques
    for doc_id, row  in data.iterrows():

        token_stream = ParseDocs(row)
        num_block = SPIMI_INVERT(token_stream, doc_id, num_block=block_n,  size_per_block=size_per_block_input, path_block=path_block_temp,)
        block_n = num_block
        f[num_block] = f'{path_block_temp}block_{num_block}.txt'
    
    # en caso de que el ultimo bloque no se haya escrito
    if global_dictionary:
        WriteBlockToDisk(global_dictionary, num_block, path=path_block_temp)
        f[num_block] = f'{path_block_temp}block_{num_block}.txt'
        num_block += 1
        # innecesario pero me sirve para indicar que se acabo y limpiarlo
        global_dictionary = SortedDict()
        global_block_size = 0


    # print(f'Numero de bloques: {num_block}')    

    f = MergeBlocks(f, output_folder=output_path, block_size_limit=block_limit_size, max_ram_limit=max_ram_limit)
    shutil.rmtree(path_block_temp)
    return f